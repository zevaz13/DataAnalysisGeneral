# SSVEP project: work-to-date summary and code review

**Section 1 is kept current** (last updated after M10). **Section 2 is a
dated code review specifically of the M1-M5 code** (the axis-swap fix, the
test suite, the permutation subsampling fix, and related findings) -- it was
not repeated for M6-M10, whose own design decisions and rationale live in
`docs/methods.md` instead (one section per milestone) rather than as a
review-style writeup. Companion docs: `methods.md` (analysis conventions and
per-milestone rationale), `api_reference.md` (per-function signatures),
`ssvep_analyses.md` (the seven proposed analyses M6-M10 implement).

## 1. What exists

### Data pipeline

Raw: 62 `.mat` files in `/home/sebas/data/ssveps/`, 43 unique subjects, sessions
1-2 (no session 3 in this dataset). Read in place, never copied into the repo.

| Script | Role |
|---|---|
| `loader.py` | `load_ssvep` (scipy `.mat` -> dict), `to_rows` (one file -> tidy rows), `write_derived_csv` (shared writer) |
| `build_derived.py` | Full from-scratch rebuild of `files/`. Wipes hand-edits. |
| `update_derived.py` | Incremental add/refresh; preserves `metadata.csv` hand-edits |
| `build_troughs.py` | Recomputes `subject_troughs.csv` / `group_troughs.csv` |

Derived files in `ssveps/files/`: `metadata.csv` (62 rows), `grid.json`,
`runmap.csv` (24,200), `baselines.csv` (968), `subject_troughs.csv` (62 rows,
now also carrying the M6 ramp-fit columns -- see below), `group_troughs.csv`
(7). M7/M8/M10's own derived quantities (variance components, gain/shape
fits, PCA components) are computed fresh in their notebooks, not persisted --
see `methods.md` for why.

### Analysis layer

- `analysis.py` (~590 lines) -- tidy-CSV access, three normalizations
  (percent/db/zscore) over a selectable baseline scope/trial subset,
  single-subject and cross-subject/group aggregation, interpolation, trough
  argmin, four parametric surface fits (paraboloid, gaussian, **ramp_gaussian
  -- the default since M4's replacement**, and M6's ramp-only `fit_ramp`),
  M6's `extrapolate_ramp_crossing` and generic `bootstrap_ci`, and M8's
  `fit_gain_shape`/`trough_region_residual`.
- `permutation.py` (307 lines) -- three cluster-based permutation tests
  mirroring the three MATLAB templates: size-only, size+weight, and
  positive/negative directional.
- `reliability.py` (~170 lines) -- paired-subject discovery, per-pixel
  ICC(A,1) grid via `pingouin`, session-pair extraction, two example-point
  selectors, and M9's `feature_icc`/`minimum_detectable_effect` (per-subject
  scalar reliability and the ICC-to-power connection).
- `variance.py` (M7, new module) -- within/between-subject variance
  decomposition via a random-intercept `statsmodels` `MixedLM` per group,
  plus a subject-level bootstrap CI on each component.
- `pca.py` (M10, new module) -- PCA (plain SVD, no covariance shrinkage) of
  the 100-cell response grid, plus permutation-based component-count
  selection (a numpy-native alternative to a fixed cutoff or shrinkage
  covariance).
- `plotting.py` (~800 lines, 40 functions) -- heatmaps, distributions
  (including M6's baseline-comparison and M6/M9's generic per-feature
  boxplot), trough scatter/overlay, permutation panels, ICC maps,
  Bland-Altman/session scatter.

### Notebooks

`01_explore`, `02_plots`, `03_group_comparisons`, `04_distributions`,
`05_permutation_testing`, `06_trough_surface_fit`, `07_test_retest_reliability`
(M1-M5), then `08_cvd_gamut`, `09_variance_components`, `10_gain_shape`,
`11_reliability_outcomes`, `12_pca` (M6-M10). `08`-`12` each include an
"Understanding ..." section per method with a synthetic-data walkthrough
before the real analysis -- read those first if the underlying statistics
aren't already familiar (see `ssveps/README.md`).

### Headline results so far

- Group trough is broad and flat; CTR (n=21, session 1) minimum sits at
  red 2133 / green 889, matching the independent reference image.
- Permutation testing (session 1 vs HC, after the 2.3 fix): PD shows no
  cluster; protan has a cluster at p=0.042 and deutan one at p=0.012.
- Test-retest ICC: 0.77 across the whole grid (n=19 paired), 0.79 for CTR
  (n=13), 0.42 for PD (n=4, too thin to trust). CVD subgroups have too few
  paired subjects to run at all.
- **CVD vs. CTR is the one well-powered effect in the dataset** (M6):
  73%/81% sensitivity/specificity on whether a subject's trough fit pegs at
  the sampled range boundary (Fisher exact p=0.0019). The protan-vs-deutan
  subtype question has a consistent hint across three independent
  analyses -- shallower `ramp_slope_red` (M6), a trough-specific residual
  beyond gain (M8, p=0.030 uncorrected), the closest-to-significant PC1
  split (M10, p=0.092) -- but none individually reaches significance at
  n=7-8.
- **PD's higher variability is about the people, not the measurement** (M7):
  within-subject SD is not elevated, but whether PD's between-subject SD
  exceeds CTR's remains unresolved at n=6. Deutan's between-subject SD came
  out *lower* than CTR's -- unexpected, flagged rather than explained away.
- **Reliability-first outcome selection changed the recommendation** (M9):
  `ramp_slope_red` (M6) and `gain` (M8) are *more* reliable (ICC 0.85, 0.90)
  than `depth` (0.76, the original top pick); `fitted_red` (0.18) is
  functionally unusable at this project's sample sizes.
- **PCA confirms "gain" as the dominant real axis** (M10) three independent
  ways (PC1, `ramp_intercept`, `gain` all correlate >0.9), and only PC1
  clears a permutation-based noise floor at n=43 -- stricter than originally
  expected.
- The standing experimental recommendation since M6, unchanged: extend the
  red stimulus axis, and collect more PD/protan/deutan subjects. See
  `PLANssveps.md`'s "M6-M10: where this leaves things" for the full picture.

## 2. Findings

Ordered by severity. Each is backed by a check that was actually run, not by
inspection alone.

### 2.1 Red/green axis naming was swapped everywhere except the heatmaps [FIXED]

**The grid's array axis 0 is green and axis 1 is red**, but every name in the
codebase says the opposite. `loader.to_rows` unpacks
`n_red, n_green, n_runs = d["runMap"].shape`, so the CSV column called
`red_idx` actually holds the green index and vice versa.

Three independent confirmations:

1. The MATLAB templates plot with `imagesc(redArray, greenArray, M)`
   (`group_permTesting_01JULY25.m:124`, `ICC_grids_22oct25.m:94`). MATLAB maps
   `M`'s **columns** to x and **rows** to y, so `M`'s rows are green. `M` comes
   straight from `runMap` with no transpose (`computeICC_gridMaps.m:25-33`).
2. `ssveps/CTRdata.png` (independent reference, produced by that MATLAB code)
   has its minimum at red 2133 / green 889. Our CTR session-1 grid's argmin is
   at `(axis0=4, axis1=6)`. Reading axis1 as red gives `redArray[6] = 2133.3`
   and `greenArray[4] = 888.9` - an exact match on both coordinates. Reading
   axis0 as red gives 1422 / 1333, matching neither.
3. Decoding `CTRdata.png` cell-by-cell and correlating against our grid:
   **r = 0.92 as-is (axis0=green), r = 0.70 transposed**.

`docs/methods.md`'s "Axis convention" section is self-contradictory on this: a
grid indexed `[red_idx, green_idx]` passed to `imshow` with no transpose puts
red on **y**, not x. The r=0.99 validation recorded in `PLANssveps.md` compared
rendered pixel values, which are identical either way - it could not detect a
naming error, so this was never actually tested.

**What is wrong as a result:**

| Location | Consequence |
|---|---|
| `runmap.csv` `red_idx`/`green_idx` columns | Column names swapped at the source |
| `analysis.trough_location` | Returns red and green swapped |
| `subject_troughs.csv`, `group_troughs.csv` | `red`/`green` and `red_idx`/`green_idx` columns swapped in all 69 rows |
| `analysis.fit_paraboloid` / `fit_gaussian` | `fitted_red`/`fitted_green` swapped |
| `plotting.plot_trough_locations` | Marker lands at pixel (4,6); true minimum is at (6,4) - verified |
| `plotting.plot_trough_scatter` | Axes swapped; points also clipped by `set_xlim`/`set_ylim` |
| `reliability.example_points_fixed` | Samples the wrong pixels. Target (red 0, green 1111) resolves to grid[0,5], which is physically red 1778 / green 0 - verified |
| `ssveps/README.md` | States `runMap` shape is `(red, green, run)` |

**What is unaffected** (checked, not assumed): every heatmap, because
`_plot_heatmap` labels x as red and y as green, which happens to be correct for
the real layout. Also unaffected: all group means, all distribution plots, the
whole of `permutation.py` (orientation-agnostic), and `icc_grid`/`icc_map`
values (internally self-consistent - only the column *names* are misleading).

**Fixed at the source.** `loader.to_rows` now unpacks `n_green, n_red,
n_runs` and reads `runMap[green_idx, red_idx, run]`, so the emitted columns are
truthful and every in-memory grid is genuinely `[red_idx, green_idx]`.
`plotting._plot_heatmap` displays `grid.T` so red stays on x, and
`plot_interpolated_grid`'s compensating `(n_green, n_red)` swap was removed.
`runmap.csv`, `baselines.csv` and both trough CSVs were rebuilt;
`metadata.csv` was left alone to preserve the hand-edits.

Verified:

- **Every heatmap renders pixel-identically before and after** (SHA-256 over
  eight rendered figures: single run, mean run, group mean, subject panels,
  group panels, interpolated, ICC map). Only `plot_all_runs` changed, and only
  because it was separately routed through the 5-column panel helper.
- `group_troughs.csv` for HC session 1 now reads red 2133.3 / green 888.9,
  matching `CTRdata.png` exactly; it previously read 1422 / 1333. Depths are
  unchanged, as they must be.
- `plot_trough_locations`' marker now lands on the darkest pixel (x=6, y=4)
  instead of (x=4, y=6) - the "slightly left and up" offset that prompted this.
- `example_points_fixed` now samples the template's actual targets: (0, 1111)
  resolves to red 0 / green 1111, previously red 1778 / green 0.

### 2.2 No tests existed [FIXED]

2,631 lines of analysis code, zero tests. Finding 2.1 is the direct cost: the
one validation that was performed was structurally blind to the error it was
meant to catch.

**Added** `ssveps/tests/test_ssveps.py` - 14 tests, `uv run pytest ssveps/tests -q`:

- Axis orientation, pinned at both ends: `test_loader_reads_runmap_green_first`
  against the raw `.mat`, and `test_ctr_trough_matches_reference_image` against
  the reference image's coordinates. Plus a direction-sensitive check that the
  red=0 edge is the brightest, which a correlation cannot catch.
- `_plot_heatmap` really does put red on x and display the transpose.
- Percent normalization against `computeICC_gridMaps.m:27-32`, and that
  `mean_grid` normalizes per run *then* averages, not the reverse.
- Ragged 3-run subjects (`MET037`) give 300-length flattens and 10x10 means.
- `_clusters` 8-connectivity via a diagonal pair that must merge into one cluster.
- Permutation keeps every subject, and is reproducible under a seed.
- Panels wrap at `MAX_PANEL_COLS`.

Mutation-checked: reintroducing the loader's axis swap fails
`test_loader_reads_runmap_green_first`. Note the CSV-backed tests only catch
that bug after a rebuild - the loader test is the guard at the source.

Still uncovered and worth adding later: an `update_derived.py` no-op run
leaving the derived CSVs byte-identical.

### 2.3 Permutation subsampling [FIXED]

`_setup` defaults `n1 = n2 = min(len(grids1), len(grids2))`. For PD vs CTR at
session 1 that draws 6 from 6 and **6 from 21**. The MATLAB template
(`group_permTesting_01JULY25.m:38-39`) used 30 of 33 and 5 of 7 - it barely
subsampled the large group.

Measured effect on PD vs CTR, session 1, seed 0: **max |z| = 1.43 under the
current default vs 1.81 with `n1=6, n2=21`**. Discarding 15 of 21 controls
inflates the null's spread and shrinks every z-score by roughly a quarter. The
test is markedly more conservative than the one it replicates. Neither setting
reaches significance here, so no published result changes - but the default
should not silently throw away two thirds of the control group.

There is a second, structural point: the observed difference map is computed
from all 6 vs 21 subjects while the null is built from 6 vs 6. A permutation
null is only exact when the permuted statistic is computed exactly like the
observed one.

**Fixed.** `n1`/`n2` now default to the full group sizes; no subject is
discarded, and each permutation is a plain relabelling over exactly the
subjects the observed map uses. They remain parameters so the template's
behaviour can be reproduced deliberately.

**This changes M3's conclusions.** Re-run at session 1 vs HC, seed 0:

| comparison | before | after |
|---|---|---|
| PD vs HC | no cluster | no cluster (max \|z\| 1.43 -> 1.81) |
| protan vs HC | no surviving cluster | cluster p=0.042 (size 19, weight 54.7) |
| deutan vs HC | no surviving cluster | cluster p=0.012 (size 55, weight 146.9) |

`05_permutation_testing.ipynb` needs re-running.

### 2.4 The paraboloid is a poor model for this surface (medium)

Only **37 of 62** subject-sessions produce a valid fit: 12 are not minima at all
(the Hessian is a saddle or maximum) and 13 more put the vertex outside the
sampled range. A single global quadratic cannot represent a surface that ramps
monotonically along red and dips only in the middle.

The design matrix is badly conditioned (**cond = 2.3e7** on raw 0-3200 units,
vs 4.0 centred and scaled), but this was tested and is *not* the cause: a
centred/scaled refit gives byte-identical validity counts (37/62) and locations
agreeing to 1.5e-8. Scaling is worth doing for robustness, but it will not
recover a single fit.

**Proposed replacement: a linear ramp plus one localized Gaussian dip, fitted
jointly, with bounds.**

    z = c0 + c1*x + c2*y - amp * exp(-((x-x0)^2/(2*sx^2) + (y-y0)^2/(2*sy^2)))

This matches the shape the data actually has: a monotonic ramp along red with a
localized dip sitting on top of it. The current models each try to make one
term do both jobs, which is why they fail. The bounds encode the failure modes
directly rather than testing for them afterwards -- `amp > 0` (it must be a
dip), `x0`/`y0` inside the sampled range (no extrapolation), `sx`/`sy` bounded
below (no degenerate spikes) -- so `fit_valid` reduces to one substantive
check: is the dip deep enough to be real (`amp > 0.02`, i.e. 2% of baseline)?

Measured across all 62 subject-sessions:

| model | valid | median r2 |
|---|---|---|
| global paraboloid (current default) | 37/62 (60%) | 0.578 |
| local 5x5 window around argmin | 41/62 (66%) | 0.544 |
| local 7x7 window around argmin | 43/62 (69%) | 0.553 |
| plane-detrended paraboloid | 50/62 (81%) | n/a (r2 vs residual) |
| **ramp + gaussian dip, bounded** | **62/62 (100%)** | **0.650** |

The fitted centre sits a median of 1.15 grid steps from the grid argmin (90th
percentile 4.02), which is the expected behaviour: sub-grid refinement for most
subjects, larger moves only where the argmin is itself unstable. Reporting
`amp` and `sx`/`sy` as columns also gives depth and trough *width* as
per-subject features, which the argmin cannot provide at all -- plausibly more
discriminative between groups than location alone.

Implement as a third `method='ramp_gaussian'` in `fit_trough_surface` and make
it the default for `subject_troughs`. Do this after 2.1, since the fit reports
physical red/green coordinates and would otherwise inherit the swap.

### 2.5 The two build scripts wrote different files [FIXED]

`build_derived.py` writes via the `csv` module (`str(float)`);
`update_derived.py` writes via pandas with `float_format="%.17g"`. **9,536 of
25,168 rows come out as different text** (e.g. `0.8689062516506942` vs
`0.86890625165069424`). Both round-trip to the same float64, so no value is
wrong - but running one script after the other produces a five-figure spurious
git diff, which makes real changes impossible to spot in review.

They also differed in **row order**: `build_derived` wrote in `red,green,run`
loop order, `update_derived` sorted by `run,red,green`.

**Fixed.** Both now write through a single `loader.write_derived_csv`, sharing
column order, row order and float formatting. Verified: building the same data
with each script now produces byte-identical `runmap.csv`, `baselines.csv`,
`metadata.csv` and `grid.json`.

Two further problems surfaced while verifying this:

- **`float_format` was being silently ignored on first run.** `update_derived`
  concatenates new rows onto an empty DataFrame, which leaves `value` as
  object dtype -- and `to_csv`'s `float_format` does not apply to object
  columns. So a freshly built file used one format and an incrementally
  updated one another. `write_derived_csv` now calls `infer_objects()` first.
- **The committed CSVs were 1 ULP off the raw data.** 373 of 24,200 values in
  `runmap.csv` and 16 of 968 in `baselines.csv` did not match what
  `loader.to_rows` reads from the `.mat` files (max relative error 3.7e-16) --
  written before the `float_format` fix existed and never regenerated, which
  is also why the earlier "byte-identical no-op" check passed: it compared the
  script against its own degraded output. Both files have been regenerated
  from source; `metadata.csv` was left alone to preserve the hand-edits.
  Nothing scientific changes -- `group_troughs.csv` moved by <=3e-17 and no
  trough location, index or label changed.

### 2.6 Documentation drift [FIXED]

- `ssveps/README.md` stopped at notebook 03. **Rewritten** to cover M2-M5
  (distributions, troughs, permutation, surface fits, ICC), with the `runMap`
  axis question recorded as an open issue rather than restated incorrectly.
- `docs/methods.md`'s permutation section claimed subsampling was deliberate.
  **Rewritten** to match 2.3.
- `docs/methods.md`'s axis section still states a convention that cannot hold
  as written -- left in place until 2.1 is decided.
- `docs/api_reference.md` is current and complete. It should stay generated
  from `inspect` rather than hand-maintained.

### 2.7 Smaller items (low)

- **Permutation p-values can be exactly 0.** `(null_weights > weight).mean()`
  with no `+1` correction. Use `(1 + count) / (1 + n_perm)`; a p-value of 0 is
  not a value a permutation test can produce.
- **Mixed-sign clusters merge in the directional test.** `_clusters` thresholds
  on `|z|`, so one connected component can span both signs and gets assigned a
  single sign from its signed sum. This faithfully replicates the template
  (`bwconncomp(logical(zdiffFake))`), and measurement shows it never fires here:
  **0 of 676 null clusters spanned both signs** in PD vs CTR. Note it in
  `methods.md`; do not change the code without reason.
- **`zscore` divides by `np.std` with `ddof=0`** over as few as 2 values when
  `scope='run', trials='first2'`. Use `ddof=1` and document the instability.
- **`build_derived._write_csv` raises `IndexError` on an empty file list**
  (`rows[0].keys()`).
- **`plot_icc_map` clips negative ICCs to 0**, making "unreliable" and
  "slightly negative" indistinguishable. Matches the template's `clim([0 1])`,
  so this is a conscious inheritance - worth a note in the colorbar label.
- **Inconsistent defaults.** `plotting.*` defaults to `normalize=None` (raw)
  while `analysis.subject_troughs`, `permutation.*`, and `reliability.*` default
  to `DEFAULT_NORMALIZE`. Easy to plot raw next to normalized statistics without
  noticing.
- **`plotting.py` imports `reliability`, pulling `pingouin` into every plotting
  import** (1.07 s). Move `session_pair_values` to `analysis.py` or import it
  lazily.
- **`_plot_heatmap` re-reads `grid.json` from disk on every panel.** Wrap
  `load_grid_axes` in `functools.cache`.

### 2.8 Repetition in `plotting.py` (low)

37 functions, and three patterns repeat verbatim: the
`if sub_ids is None: sub_ids = subjects_in_group(...)` resolution (7x), the
`", ".join(filter(None, [group, subgroup])) or f"{len(sub_ids)} subjects"`
subtitle (7x), and the `categories` -> `sub_id_lists` expansion (3x). Two small
helpers - `_resolve_subjects(metadata_df, session, sub_ids, group, subgroup)`
returning `(sub_ids, label)`, and `_resolve_categories(...)` - remove roughly 30
lines and one whole class of copy-paste error.

### 2.9 Repo hygiene (low)

- Empty `Untitled Folder/` at the repo root.
- All 7 notebooks are committed with outputs embedded (~3.5 MB of base64 PNGs,
  dominating repo size). Consider `nbstripout`, or accept it deliberately since
  the rendered figures are the point of sharing them.
- Notebooks import via `sys.path.append('../scripts')`, which only works when
  the kernel's CWD is `notebooks/`. A `ssveps/scripts/__init__.py` plus a
  `pyproject.toml` path entry, or a one-line `conftest`-style bootstrap, would
  be sturdier.

## 3. What was checked and found correct

Stated explicitly so it does not get re-litigated:

- **Normalization matches the MATLAB template exactly.** `DEFAULT_NORMALIZE`
  (`scope='run'`, `trials='all'`, `method='percent'`) reproduces
  `computeICC_gridMaps.m:27-32` line for line: per-run percent change from that
  run's own baseline mean, then averaged across runs.
- **8-connectivity is correctly matched** to MATLAB `bwconncomp`'s 2D default,
  and is passed explicitly because scipy's default is 4-connected.
- **The negative-cluster `min()` fix is real and correctly applied.**
  `group_permTesting_positive_negative_clusters.m:145` does
  `max(cell2mat(newArrP))` over negative sums, picking the weakest cluster.
- **`pingouin`'s `ICC(A,1)` is the right match** for the template's MATLAB
  `ICC(..., 'A-1')`.
- **Ragged 3-run subjects are handled from the data throughout**, never
  special-cased.
- **Performance is not a problem.** 21-panel figure 0.89 s; 43 subject mean
  grids 0.64 s; full 100-pixel `icc_grid` at n=19 3.43 s. No optimisation is
  warranted.
- No unused imports in any of the eight scripts.

## 4. Suggested order of work (historical -- all items below are done)

For current, forward-looking guidance see `PLANssveps.md`'s "M6-M10: where
this leaves things" section instead.

1. Fix the axis swap (2.1) and rebuild the derived CSVs. Everything trough- and
   pixel-location-related is wrong until this lands.
2. Add the regression tests in 2.2, starting with the orientation test.
3. Decide the permutation subsampling default (2.3) and record the decision.
4. Unify the CSV writers (2.5).
5. Refresh `ssveps/README.md` and `methods.md` (2.6).
6. Revisit the trough surface fit (2.4) as a milestone of its own.
7. Sweep the low-severity items (2.7-2.9) opportunistically.
