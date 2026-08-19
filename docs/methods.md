# SSVEP grid analysis: conventions

Established during M1/M2 of the SSVEP project (`ssveps/`). These are the
non-obvious decisions and conventions that are easy to get wrong if
re-derived from scratch -- see `PLANssveps.md` for the full history and
reasoning behind each.

## The experiment

Each subject/session runs a red x green intensity grid (10x10 levels each,
`redArray` 0-3200, `greenArray` 0-2000) with 3-4 runs, plus 4 baseline trials
per run. `METxxx` is the subject id; `a`/`b`/`c` suffix on the raw filename
(none/`b`/`c`) is session 1/2/3. `MET037-040` (group `PD`) only have 3 runs
instead of 4 -- every function here reads the run count from the data rather
than assuming 4, so this "ragged" case is handled automatically, not as a
special case.

## Baseline trial split

Baseline trials 1-2 are pre-grid, 3-4 are post-grid (confirmed against the
raw data's trial ordering). `analysis.baseline_values(..., trials=)` selects
`'all'` (1-4), `'first2'` (pre only), or `'last2'` (post only).

`scope='run'` uses only that run's own 4 baseline trials; `scope='session'`
pools baseline trials across every run of the session. Aggregate/group
functions (`mean_grid`, `group_grid`, etc.) always operate on one fixed
`session` at a time -- passing a `group`/`subgroup` filter across sessions
would double-count the ~19 subjects who have both session 1 and 2.

## Normalization formulas

`analysis.normalize_grid(raw, baseline_vals, method=)`, given `base_mean =
baseline_vals.mean()`:

| method | formula |
|---|---|
| `percent` | `(raw - base_mean) / base_mean` |
| `db` | `10 * log10(raw / base_mean)` |
| `zscore` | `(raw - base_mean) / baseline_vals.std()` |

`zscore`'s `std()` is over the same `baseline_vals` used for `base_mean`, so
`scope`/`trials` selects the same trial subset for both the mean and the
spread.

## Axis convention: red = x, green = y, no transpose

Every grid array is indexed `[red_idx, green_idx]` and plotted with
`imshow(grid, origin='lower')` -- **no transpose**, red always the x-axis,
green always the y-axis. Only the tick labels map index -> physical value.

This was validated, not assumed: an independently-produced CTR-group
reference image (`ssveps/CTRdata.png`, different software) was decoded
pixel-by-pixel and compared against this pipeline's output -- **r=0.99,
MSE=0.0005**. `analysis.interpolate_grid` (used for upsampling to a finer
resolution) does its own dimensionally-correct transpose internally to
support rectangular target shapes, but the *displayed* orientation after
that transpose still matches this same convention -- confirmed by checking
that interpolating back to the native 10x10 resolution reproduces the
non-interpolated plot exactly (max abs diff 0.0).

## Trough depth: normalized by default

`analysis.trough_location`/`subject_troughs`/`group_troughs` locate each
subject's/group's minimum on the native 10x10 grid (argmin, no
interpolation -- a proper noise-resistant localization via a parametric
surface fit is planned for M4, so interpolating now would be a throwaway
half-measure). Depth defaults to **% change from baseline**
(`analysis.DEFAULT_TROUGH_NORMALIZE`), not raw value, because raw SSVEP
amplitude varies a lot subject-to-subject and isn't comparable across
subjects/groups -- pass `normalize=None` for raw depth instead.

## `metadata.csv`: hand-edits are permanent, and preserved by default

`group`/`subgroup` in `ssveps/files/metadata.csv` were hand-corrected for
some subjects (e.g. `MET043-046`) after the raw `.mat` files' own labels were
found stale (`UNKNOWN`/`NA`). Two rebuild scripts exist with different
policies:

- `scripts/build_derived.py` -- full from-scratch rebuild, **always**
  regenerates `group`/`subgroup` from the raw files. This wipes any hand-edit.
  Intentional-reset-only.
- `scripts/update_derived.py` -- incremental: a new subject/session is added
  directly; an existing one prompts `[y/N]` before overwriting, and even then
  only refreshes `runmap.csv`/`baselines.csv` -- `group`/`subgroup` in
  `metadata.csv` is set once at first creation and never touched again. Use
  this for day-to-day updates.

## Grid-file naming (`ssveps/files/`)

All CSVs are tidy/long-format, keyed by `sub_id`/`session` (and `run` where
applicable), rebuilt from the raw `.mat` files -- safe to delete and rerun
`build_derived.py`, except `metadata.csv`'s hand-edited `group`/`subgroup`
values (see above). `subject_troughs.csv`/`group_troughs.csv` are a further
derived layer (via `scripts/build_troughs.py`) on top of the others, with no
hand-edits of their own -- always a straight recompute.
