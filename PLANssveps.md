# SSVEP project plan

Raw data: `/home/sebas/data/ssveps/` - 62 MATLAB files, 43 subjects.
`METxxx` is the subject id; the filename suffix gives the session
(none = 1, `b` = 2, `c` = 3; no `c` files exist in this dataset).

Reference MATLAB implementations live in `ssveps/templateCode/` (gitignored).

## Documents

- `docs/ssvep_summary.md` - what has been built, code review findings, and the
  suggested order of work. **Read this first.**
- `docs/methods.md` - analysis conventions (normalization, axes, ICC, permutation).
- `docs/api_reference.md` - every public function's signature and parameters.
- `ssveps/README.md` - data dictionary and script/notebook index.

## Completed (M1-M5)

Delivered and in the repo. Detail lives in `docs/ssvep_summary.md` section 1;
this is the index.

- **M1 - Ingest and visualize.** `loader.py`, `build_derived.py`,
  `update_derived.py`; tidy CSVs in `ssveps/files/`; three normalizations
  (percent/db/zscore) over selectable baseline scope and trial subsets;
  single-subject, group, and interpolated heatmaps. Notebooks 01-03.
- **M2 - Distributions and trough location.** Boxplots/histograms per subject,
  per group (pooled and mean-grid); `trough_location` plus persisted
  `subject_troughs.csv` / `group_troughs.csv`. Notebook 04.
- **M3 - Cluster-based permutation testing.** Three functions mirroring the
  three MATLAB templates (size, size+weight, directional), generalized to any
  group/subgroup pair, seeded, with a corrected negative-cluster null.
  Notebook 05.
- **M4 - Parametric trough surface fit.** `fit_paraboloid` and `fit_gaussian`
  behind `fit_trough_surface`, with `fit_valid` and `r_squared` reported.
  Notebook 06.
- **M5 - Test-retest reliability.** Per-pixel ICC(A,1) maps via `pingouin`,
  paired-subject discovery, Bland-Altman and session-scatter plots.
  Notebook 07.

## Open issues

From the code review in `docs/ssvep_summary.md` section 2, which carries the
evidence and the suggested fix for each.

Next up:

- [ ] **Re-run every notebook.** The axis fix changed all reported trough
  coordinates, and the subsampling fix changed M3's results. `02_plots.ipynb`
  also has stale pre-wrapping output (cell 18 stores all 21 CTR panels in one
  6729px-wide row).
- [ ] **Work through `docs/ssvep_analyses.md`** -- seven proposed analyses,
  ordered. Start with the CVD-gamut finding (the only well-powered effect,
  p=0.0019) and the reliability-first outcome selection.

Cleanup:

- [ ] Small correctness and consistency items (2.7): permutation p-value `+1`
  correction, `zscore` `ddof`, `plotting` -> `reliability` import chain,
  `load_grid_axes` caching, inconsistent `normalize` defaults.
- [ ] Factor the repeated subject/category resolution in `plotting.py` (2.8).
- [ ] Repo hygiene (2.9): remove `Untitled Folder/`, decide on notebook
  outputs, make the notebook import path robust.

## Done since the review

- [x] **Trough surface fit replaced** (2.4) with `fit_ramp_gaussian` (linear
  ramp + bounded Gaussian dip), now the default. Converges on 62/62 rows and
  adds `fitted_amp`/`fitted_sigma_red`/`fitted_sigma_green`. Also added
  `fitted_at_bound`, which surfaced that most CVD subjects' troughs lie beyond
  the sampled red range -- see `docs/ssvep_analyses.md` section 2.
- [x] **`docs/ssvep_analyses.md`** -- seven proposed analyses with the
  supporting measurements.
- [x] **Red/green axis naming fixed at the source** (2.1). `loader.to_rows`
  reads `runMap[green_idx, red_idx, run]`; `_plot_heatmap` displays `grid.T`.
  Every heatmap verified pixel-identical before/after; HC's trough now reads
  red 2133 / green 889, matching the reference image.
- [x] **Test suite added** (2.2). `uv run pytest ssveps/tests -q`, 14 tests,
  mutation-checked against the axis bug.
- [x] **Permutation no longer discards subjects** (2.3). `n1`/`n2` default to
  the full group sizes; they remain parameters for reproducing the templates.
- [x] **Both build scripts unified** (2.5) onto `loader.write_derived_csv` --
  verified byte-identical output. Fixed two problems found while verifying: a
  dtype quirk that silently disabled the float formatting on a first run, and
  389 committed values that were 1 ULP off the raw data (now regenerated; no
  scientific change).
- [x] **`ssveps/README.md` rewritten** to cover M2-M5, and `methods.md`'s
  permutation section corrected (2.6).

## Next milestones

To be defined together once the blocking issues above are settled.
