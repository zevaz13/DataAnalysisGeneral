# SSVEPs

SSVEP (steady-state visual evoked potential) grid experiment data.

Raw data: `/home/sebas/data/ssveps/` (read in place, not copied into the repo).
62 MATLAB `.mat` files, one per subject/session, 43 unique subjects. Filename
is `METxxx[b].mat`: `METxxx` is the subject id, the optional trailing letter
is the session (no letter = session 1, `b` = session 2; the plan's `c`/session
3 does not occur in this dataset).

Conventions and rationale: `docs/methods.md`. Function-by-function reference:
`docs/api_reference.md`. Status, review findings and open issues:
`docs/ssvep_summary.md`.

## Fields (per raw `.mat` file)

- `SubID` — subject id string (stable per subject across sessions)
- `session` — session number (1 or 2)
- `group` — `CTR`/`PD`/`HD`/`CVD`/`UNKNOWN` (stable per subject)
- `subgroup` — `protan`/`deutan`/`NA`, color-blindness type (stable per subject)
- `redArray`, `greenArray` — 10 intensity levels each, defining the grid axes
  (identical across all 62 files; red spans 0-3200, green 0-2000)
- `runMap` — 10x10 grid of measurements per run; run count is usually 4, but
  only 3 for `MET037-040` (all group `PD`)
- `baselines` — shape `(trial, run)` per `baseDIM` (`TR_RUN`); 4 baseline trials
  per run, trials 1-2 pre-grid and 3-4 post-grid

**`runMap` axis order.** `mapDIM` reports `RED_GREEN_RUN`, but the array's
first axis is actually **green** and its second **red** (confirmed three ways
-- see `docs/methods.md`). `loader.to_rows` handles this, so the derived CSVs'
`red_idx`/`green_idx` columns and every grid downstream are genuinely indexed
`[red_idx, green_idx]`. Pinned by `ssveps/tests/test_ssveps.py`.

## Derived files (`files/`)

- `metadata.csv` — one row per subject-session: `filename, sub_id, session, group, subgroup`.
  **`group`/`subgroup` are set once, when a row is first created, and are never
  overwritten automatically afterward** (see `scripts/update_derived.py`) --
  correct them by editing `metadata.csv` directly.
- `grid.json` — the shared grid constants: `redArray`, `greenArray`, `baseDIM`, `mapDIM`
- `runmap.csv` — tidy long format: `sub_id, session, run, red_idx, green_idx, value`
  (indices are 0-based positions into `grid.json`'s arrays; `run` is 1-based)
- `baselines.csv` — tidy long format: `sub_id, session, run, trial, value` (1-based `run`/`trial`)
- `subject_troughs.csv` / `group_troughs.csv` — per subject-session and per
  group-session trough location and depth, both grid-argmin and surface-fit
  (built by `scripts/build_troughs.py`). `subject_troughs.csv` also carries a
  ramp-only fit (`ramp_intercept`/`ramp_slope_red`/`ramp_slope_green`/
  `ramp_r_squared`, M6) that's defined for every row, unlike the `fitted_*`
  columns which can fail to locate an interior trough; and a rotated-dip fit
  (`rotated_red`/`rotated_green`/`rotated_depth`/`rotated_amp`/
  `rotated_sigma_major`/`rotated_sigma_minor`/`rotated_orientation_deg`/
  `rotated_r_squared`/`rotated_at_bound`/`rotated_valid`, M11) — purely
  additive alongside `fitted_*`, adds a tilt the axis-aligned fit can't
  express. See `16_grid_shape_features.ipynb`.

M7's variance components, M8's gain/shape decomposition, and M10's PCA
components are not persisted to CSV -- all three depend on a choice made at
analysis time (which group's subjects to pool, which template to regress
against, which session's grids go into the matrix) rather than being an
intrinsic per-subject property, so they're computed fresh in their notebooks.

## Analysis

### `scripts/analysis.py` — data access, normalization, aggregation

- `raw_grid`/`mean_raw_grid`/`mean_grid` — 10x10 grids from `runmap.csv`;
  `mean_grid` takes an optional `normalize=` dict covering both the raw and
  normalized case
- `baseline_values` — select baseline trials: `scope='run'` uses one run's own
  trials, `scope='session'` pools across every run; `trials='all'/'first2'/'last2'`,
  where first2/last2 = pre-/post-grid
- `normalize_grid`/`normalized_grid` — `method='percent'/'db'/'zscore'`, baseline
  reduced to its mean (z-score also uses its std). `DEFAULT_NORMALIZE` is
  percent change per run, the setting the MATLAB templates used and the default
  for every cross-subject statistic here
- `subjects_in_group`/`mean_grid_across_subjects`/`group_grid` — cross-subject
  aggregation, one session at a time so 2-session subjects aren't double-counted
- `flatten_runs`/`pooled_pixels` — every pixel of every run for one subject, or
  pooled across a list of subjects, as a 1D array
- `interpolate_grid(grid, shape)` — resize a grid to an arbitrary (including
  rectangular) resolution via linear interpolation
- `trough_location` — argmin location and depth on the native 10x10 grid
- `fit_paraboloid`/`fit_gaussian`/`fit_ramp_gaussian` behind
  `fit_trough_surface(..., method=)` — parametric surface fit locating a
  continuous, off-grid minimum; `fit_ramp_gaussian` (default) is a linear ramp
  plus a bounded Gaussian dip and is the only one that converges on every
  subject-session; all report `fit_valid`/`at_bound` and `r_squared`
- `fit_ramp` — the ramp term alone, no dip (M6); `intercept`/`slope_red`/
  `slope_green`/`r_squared`, defined for every subject regardless of whether a
  trough was ever located — the continuous measure used for CVD subjects whose
  trough lies beyond the sampled red range
- `fit_rotated_gaussian` — a tilted, anisotropic generalization of
  `fit_ramp_gaussian`'s dip (M11): `sigma_major`/`sigma_minor`/`orientation_deg`
  instead of axis-aligned `sigma_red`/`sigma_green`, `orientation_deg` folded
  into `[0, 180)` to match `beh/`'s own convention. Purely additive — does not
  touch `fit_ramp_gaussian`. Same `at_bound`/`fit_valid` flags; converges less
  often into a *valid* (non-pegged) fit than the axis-aligned version, since
  it has one more parameter to identify (see `16_grid_shape_features.ipynb`)
- `extrapolate_ramp_crossing` — given a `fit_ramp` result and a target
  depth/green (typically a population reference, not the subject's own
  unreliable fit), the red value at which that ramp would reach it —
  extrapolation beyond the sampled range, not a measurement
- `bootstrap_ci` — generic percentile bootstrap CI over any resampling
  function; used for both a group proportion's CI and a per-subject fitted
  statistic's CI (see `08_cvd_gamut.ipynb`)
- `run_grids` — each run's own grid for one subject/session (what `mean_grid`
  averages); public so a run-level bootstrap can resample which runs go into
  the mean
- `pooled_baseline_values` — every baseline trial value pooled across runs and
  subjects, the baseline analogue of `pooled_pixels`
- `run_mean_values` — each run's overall response level (mean of that run's
  grid) for one subject/session, one scalar per run (M7)
- `fit_gain_shape`/`trough_region_residual` — per-subject gain vs. shape
  decomposition against a reference template grid (M8)
- `subject_troughs`/`group_troughs` — the above tabulated per subject-session
  and per group-session (persisted by `scripts/build_troughs.py`)

### `scripts/variance.py` — within/between-subject variance decomposition (M7)

`group_run_values` (per-subject run-mean values for a group/subgroup),
`variance_components` (random-intercept MixedLM per group + subject-level
bootstrap CI on within-subject and between-subject SD), `within_subject_cv`
(scale-corrected within-subject noise, per subject).

### `scripts/permutation.py` — cluster-based permutation testing

Three functions mirroring the three MATLAB templates:
`permutation_test_size` (cluster-size correction), `permutation_test_weighted`
(adds cluster weight and per-cluster p-values), `permutation_test_directional`
(positive and negative clusters against separate one-tailed nulls). All take a
`group`/`subgroup` pair, a `seed`, and `n1`/`n2`.

`n1`/`n2` default to the **full group sizes** — no subject is discarded and
each permutation is a plain relabelling. The templates hardcoded a subsample
per comparison; pass `n1`/`n2` to reproduce that.

### `scripts/reliability.py` — test-retest reliability

`paired_subjects` (subjects with both sessions), `icc_grid`/`icc_map`
(per-pixel ICC(A,1) via `pingouin`, matching the template's MATLAB `ICC('A-1')`;
needs >=3 paired subjects), `feature_icc` (the same ICC(A,1) computation for
one per-subject scalar feature instead of a grid cell, M9),
`minimum_detectable_effect` (the smallest true effect a two-sample comparison
can detect at a given n and feature ICC, M9), `session_pair_values`, and two
example-point selectors — `example_points_fixed` (the template's 5 hardcoded
targets) and `example_points_informative` (lowest-ICC / highest-ICC / trough
pixels).

### `scripts/pca.py` — principal component analysis of the response grid (M10)

`pixel_matrix` (every subject's mean grid at a session, flattened and
stacked), `fit_pca` (PCA via SVD, no covariance shrinkage),
`permutation_component_count` (how many components are distinguishable from
a shuffled-column null -- this project's regularization-free alternative to
a fixed component cutoff or a shrinkage-covariance estimate).

### `scripts/plotting.py` — all figures

Red on the x-axis and green on the y-axis throughout (grids are stored
`[red_idx, green_idx]` and transposed at display time). Multi-panel figures
wrap to at most `MAX_PANEL_COLS` = 5 panels per row. Every function takes an
optional `normalize={scope, trials, method}` dict (raw if omitted) plus
`clim=(vmin, vmax)` and `cmap` overrides; multi-panel functions share one
auto-computed color scale unless `clim` is given. Raw values use a sequential blue colormap (magnitude), normalized
values a diverging blue/red one centered on zero (signed).

- Heatmaps: `plot_run`/`plot_all_runs`/`plot_mean_run` (single subject),
  `plot_mean_across_subjects`/`plot_subjects_side_by_side`/`plot_group_all_methods`
  (across subjects, filtered by `group`/`subgroup` or an explicit `sub_ids` list),
  `plot_groups_side_by_side` (one panel per named category),
  `plot_interpolated_grid` (any grid at an arbitrary resolution)
- Distributions: `plot_subject_boxplot`/`plot_subject_mean_boxplot` and their
  `_histogram` twins, `plot_subjects_boxplot`/`plot_subjects_mean_boxplot`
  (one box per subject), `plot_group_pooled_boxplot`/`plot_group_mean_boxplot`,
  `plot_groups_pooled_boxplot`/`plot_groups_mean_boxplot`,
  `plot_groups_baseline_boxplot` (raw baseline values by group/category, not
  pixel values)
- Troughs: `plot_trough_scatter` (locations across subjects/groups),
  `plot_trough_locations` (methods overlaid on one subject's heatmap),
  `plot_troughs_boxplot` (any per-subject scalar column from a
  `subject_troughs`-shaped table, one box per category — e.g. `ramp_slope_red`
  by subgroup)
- Permutation: `plot_permutation_test_size`/`_weighted`/`_directional` and
  `plot_permutation_null_histogram`
- Reliability: `plot_icc_map`, `plot_bland_altman`, `plot_session_scatter`,
  `plot_example_points`

## Scripts

- `scripts/loader.py` — `load_ssvep(path)` reads one `.mat` file into a plain
  dict; `to_rows(d, filename)` converts it to `(metadata_row, runmap_rows,
  baseline_rows)`; `write_derived_csv` is the single writer both build scripts
  use, so they produce byte-identical files
- `scripts/build_derived.py` — full from-scratch rebuild of `files/` from every
  raw `.mat` file. Always regenerates `metadata.csv` from the raw files, so it
  **will wipe any hand-edit made directly to metadata.csv**. Use only for an
  initial or intentional full reset.
- `scripts/update_derived.py` — day-to-day incremental update: adds new
  subject-sessions directly; for one already present, asks `[y/N]` before
  overwriting its `runmap.csv`/`baselines.csv` rows (`metadata.csv`'s
  group/subgroup is never touched, even on overwrite). Run after adding a new
  `.mat` file: `uv run python scripts/update_derived.py`
- `scripts/build_troughs.py` — recomputes both trough CSVs. Straight recompute,
  safe to rerun any time the other derived files change.

## Tests

`uv run pytest ssveps/tests -q` — 46 regression tests pinning the axis
orientation, the normalization formulas, the ragged 3-run subjects, cluster
connectivity, permutation reproducibility, the 5-column panel wrapping, and
(M11) `fit_rotated_gaussian`'s recovery of a known tilted dip, its
axis-aligned-canonicalization, and that adding it to `subject_troughs`
leaves every existing column unchanged.

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with `notebooks/`
as the working directory. `08`-`12` each include an "Understanding ..."
section per method, with a synthetic-data walkthrough and plots before the
real analysis -- read those first if the underlying statistics (bootstrap
CIs, MixedLM variance components, gain/shape regression, ICC/minimum
detectable effect, PCA/permutation component selection) aren't already
familiar.

- `01_explore.ipynb` — load and look at `MET000.mat`
- `02_plots.ipynb` — raw and baseline-normalized heatmaps (single run, all runs,
  mean across runs, ragged 3-run `MET037`), color-limit/colormap overrides, and
  cross-subject aggregation
- `03_group_comparisons.ipynb` — `PD`/`HC`(=`CTR`)/`CVD`/`protan`/`deutan`, each
  with all normalization methods and an interpolated 100x100 view, plus the four
  main categories side by side with sample sizes
- `04_distributions.ipynb` — boxplots and histograms per subject and per group
  (pooled and mean-grid), the trough-location scatter, and a raw baseline
  comparison across groups
- `05_permutation_testing.ipynb` — all three permutation tests on `PD`/`protan`/
  `deutan` vs `HC`, with null-distribution histograms
- `06_trough_surface_fit.ipynb` — paraboloid and gaussian fits overlaid on the
  grid argmin, plus fit-quality summaries across all 62 subject-sessions.
  Predates `ramp_gaussian` becoming the default surface method -- doesn't
  cover it; see `08_cvd_gamut.ipynb` for that fit in use, and `docs/methods.md`
  for why it replaced these two.
- `07_test_retest_reliability.ipynb` — ICC maps for the full paired set and per
  group, with Bland-Altman and session-scatter plots at selected pixels
- `08_cvd_gamut.ipynb` — M6: `fitted_at_bound` as a CVD/CTR diagnostic with a
  bootstrap CI, `ramp_slope_red` as a continuous measure for every CVD subject,
  ramp-crossing extrapolation for pegged subjects, and the protan-vs-deutan
  subtype test
- `09_variance_components.ipynb` — M7: within/between-subject SD per group
  via MixedLM with a bootstrap CI, and within-subject CV to check it's not
  just response-size scaling
- `10_gain_shape.ipynb` — M8: per-subject gain vs. shape decomposition
  against the CTR template, and a cross-check against M6's ramp measures
- `11_reliability_outcomes.ipynb` — M9: test-retest ICC for six candidate
  outcome features and the minimum detectable effect each supports at this
  project's actual sample sizes -- updates the primary-outcome recommendation
- `12_pca.ipynb` — M10: PCA of the 100-cell grids with permutation-based
  component selection, loading maps, and a group comparison of PC1
- `13_hc_vs_pd.ipynb` — M11: side-by-side grids, a raw/percent difference
  map, and subject-level (`ramp_slope_red`) + descriptive pixel-level
  boxplots for HC vs PD
- `14_hc_vs_subtypes.ipynb` — M11: same structure, three-way HC/protan/deutan
  with all three pairwise comparisons
- `15_permutation_stability.ipynb` — M11: all three permutation tests on
  protan vs deutan at 200 seeds each — a corrected-significant cluster
  survives in 86.5%-98% of seeds, not a fluke; see `docs/methods.md`'s M3
  section for the surviving cluster's location
- `16_grid_shape_features.ipynb` — M11: `fit_rotated_gaussian`'s tilted-dip
  shape features, per group; not enough `rotated_valid` fits yet for the
  protan-vs-deutan comparison (2/8, 3/7)
