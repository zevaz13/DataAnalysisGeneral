# SSVEP scripts and notebooks: reference

Everything lives in `ssveps/scripts/`. Notebooks (`ssveps/notebooks/`) call
these directly after `sys.path.append('../scripts')`. See `docs/methods.md`
for the conventions (baseline split, normalization formulas, axis
orientation) these functions implement. Function reference below; jump to
"Notebooks" at the end for what each notebook demonstrates and what to edit
to point it at different subjects/groups/sessions.

## `loader.py` -- reading raw `.mat` files

- **`load_ssvep(path: str) -> dict`**
  Loads one `MET*.mat` file, dropping MATLAB header keys. Returns the raw
  dict of arrays/scalars (`SubID`, `session`, `group`, `subgroup`,
  `redArray`, `greenArray`, `runMap`, `baselines`, ...).

- **`to_rows(d: dict, filename: str) -> tuple[dict, list[dict], list[dict]]`**
  Converts one loaded `.mat` dict into `(metadata_row, runmap_rows,
  baseline_rows)` -- the tidy long-format rows written to `metadata.csv`,
  `runmap.csv`, `baselines.csv`. `red_idx`/`green_idx` are 0-based; `run`/
  `trial` are 1-based. Used by both `build_derived.py` and
  `update_derived.py` so their row extraction stays identical.
- **`write_derived_csv(path: str, df, kind: 'runmap'|'baselines') -> None`**
  The single writer both `build_derived.py` and `update_derived.py` call, so
  they produce byte-identical output (2.5 -- see `docs/ssvep_summary.md`):
  reindexes to the canonical column order for `kind`, sorts by the canonical
  sort key, and writes with `float_format="%.17g"` (pandas' default
  formatting doesn't always round-trip float64 exactly; 17 significant
  digits guarantees it does). Calls `infer_objects()` first, since
  `float_format` is silently ignored on object-dtype columns -- which is
  what a DataFrame built by concatenating onto an empty one (`update_derived
  .py`'s first-run path) leaves `value` as.

## `analysis.py` -- data access, normalization, aggregation

### Loading the tidy CSVs

- **`load_runmap() -> DataFrame`** -- `ssveps/files/runmap.csv`
  (`sub_id, session, run, red_idx, green_idx, value`).
- **`load_baselines() -> DataFrame`** -- `ssveps/files/baselines.csv`
  (`sub_id, session, run, trial, value`).
- **`load_metadata() -> DataFrame`** -- `ssveps/files/metadata.csv`
  (`filename, sub_id, session, group, subgroup`). Reads with
  `keep_default_na=False` so subgroup's literal string `"NA"` (control
  subjects) isn't turned into a real NaN.
- **`load_grid_axes() -> (list[float], list[float])`** -- `redArray`,
  `greenArray` from `ssveps/files/grid.json` (shared across every subject).

### Single-run / single-subject grids

- **`raw_grid(runmap_df, sub_id, session, run) -> ndarray[10,10]`**
  One run's raw grid, indexed `[red_idx, green_idx]`.
- **`mean_raw_grid(runmap_df, sub_id, session) -> ndarray[10,10]`**
  Mean raw grid across all runs of a session.
- **`baseline_values(baselines_df, sub_id, session, *, scope='run'|'session', run=None, trials='all'|'first2'|'last2') -> ndarray`**
  Selected baseline trial values. `scope='run'` requires `run`.
- **`normalize_grid(raw, baseline_vals, *, method='percent'|'db'|'zscore') -> ndarray`**
  Normalizes a raw grid against a scalar baseline derived from
  `baseline_vals` (formulas in `docs/methods.md`).
- **`normalized_grid(runmap_df, baselines_df, sub_id, session, run, *, scope='run', trials='all', method='percent') -> ndarray`**
  `raw_grid` + `baseline_values` + `normalize_grid` in one call.
- **`mean_grid(runmap_df, baselines_df, sub_id, session, *, normalize=None) -> ndarray[10,10]`**
  Mean grid across all runs, raw (`normalize=None`) or normalized (each run
  normalized individually, then averaged). `normalize` is a
  `{scope, trials, method}` dict, used the same way in every function below
  that takes it.

### Cross-subject / cross-group aggregation

- **`subjects_in_group(metadata_df, session, *, group=None, subgroup=None) -> list[str]`**
  Subject IDs at a session, optionally filtered.
- **`mean_grid_across_subjects(runmap_df, baselines_df, sub_ids, session, *, normalize=None) -> ndarray[10,10]`**
  Mean of each subject's own `mean_grid` (each subject weighted equally).
- **`group_grid(runmap_df, baselines_df, metadata_df, session, *, group=None, subgroup=None, normalize=None) -> ndarray[10,10]`**
  `subjects_in_group` + `mean_grid_across_subjects` in one call.
- **`interpolate_grid(grid, shape: (n_red, n_green), *, method='linear') -> ndarray`**
  Resizes any `[red_idx, green_idx]` grid to an arbitrary (including
  rectangular) resolution.

### Pixel distributions (boxplots/histograms, M2)

- **`flatten_runs(runmap_df, baselines_df, sub_id, session, *, normalize=None) -> ndarray[400 or 300]`**
  Every pixel of every run of one subject, concatenated (300 for the ragged
  3-run subjects).
- **`pooled_pixels(runmap_df, baselines_df, sub_ids, session, *, normalize=None) -> ndarray`**
  `flatten_runs` concatenated across every subject in `sub_ids` -- a group's
  whole pixel distribution, pooled (not averaged).
- **`run_grids(runmap_df, baselines_df, sub_id, session, normalize) -> list[ndarray]`**
  Each run's own grid (raw or normalized), in run order -- what `mean_grid`
  averages. Public (not just an internal helper) so a run-level bootstrap can
  resample which runs go into the mean, with replacement, and refit on each
  resample (M6, `08_cvd_gamut.ipynb`'s ramp-crossing CI).
- **`pooled_baseline_values(baselines_df, sub_ids, session, *, trials='all') -> ndarray`**
  `baseline_values(scope='session')` concatenated across every subject in
  `sub_ids` -- the baseline analogue of `pooled_pixels`. Always raw: baseline
  is the normalization's own denominator.
- **`run_mean_values(runmap_df, baselines_df, sub_id, session, *, normalize=None) -> ndarray`**
  Each run's overall response level for one subject/session -- the mean of
  that run's grid (100 cells), one scalar per run. The unit `variance.py`'s
  within/between-subject decomposition (M7) operates on.

### Trough location (M2)

- **`trough_location(grid, red_vals, green_vals) -> dict`**
  `{red, green, depth, red_idx, green_idx}` for a grid's minimum (native
  resolution, `np.argmin`).
- **`subject_troughs(runmap_df, baselines_df, metadata_df, *, normalize=DEFAULT_NORMALIZE, surface_method=DEFAULT_SURFACE_METHOD) -> DataFrame`**
  One row per `(sub_id, session)` in `metadata_df`: `sub_id, session, group,
  subgroup, red, green, depth, red_idx, green_idx` (argmin) plus
  `fitted_red, fitted_green, fitted_depth, fitted_amp, fitted_sigma_red,
  fitted_sigma_green, fitted_r_squared, fitted_at_bound, fitted_valid`
  (parametric fit, `surface_method=` default `'ramp_gaussian'`, M4 -- see
  below) plus `ramp_intercept, ramp_slope_red, ramp_slope_green,
  ramp_r_squared` (ramp-only fit, M6 -- see below). Unlike the `fitted_*`
  columns, the `ramp_*` ones are never NaN and don't depend on
  `fitted_valid`/`fitted_at_bound` -- they're defined for every row.
- **`group_troughs(runmap_df, baselines_df, metadata_df, sessions, categories, *, normalize=DEFAULT_NORMALIZE) -> DataFrame`**
  One row per `(session, category)` with >=1 subject:
  `label, session, n, red, green, depth, red_idx, green_idx`. `categories` is
  a list of `{"label": str, "group": str|None, "subgroup": str|None}` (same
  shape as `plotting.plot_groups_side_by_side`'s `categories`).

`DEFAULT_NORMALIZE = {"scope": "run", "trials": "all", "method": "percent"}`
-- the standard cross-subject-comparable normalization, also the default for
every `permutation.py`/`reliability.py` function below.

### Parametric trough surface fit (M4)

- **`fit_paraboloid(grid, red_vals, green_vals) -> dict`**
  `{red, green, depth, r_squared, fit_valid}` -- closed-form quadratic
  surface fit; the analytic minimum need not land on a grid point. Valid for
  only ~60% of subject-sessions in this project's data (a single quadratic
  term can't represent a ramp-plus-dip surface -- see `fit_ramp_gaussian`).
- **`fit_gaussian(grid, red_vals, green_vals) -> dict`**
  Same shape, from an inverted 2D Gaussian dip (`scipy.optimize.curve_fit`,
  seeded from `trough_location`'s argmin). Same ramp-vs-dip limitation as
  `fit_paraboloid`.
- **`fit_ramp_gaussian(grid, red_vals, green_vals, *, min_snr=2.0) -> dict`**
  `{red, green, depth, amp, sigma_red, sigma_green, r_squared, at_bound,
  fit_valid}` -- **the default surface fit** (`DEFAULT_SURFACE_METHOD`), and
  the only one of the three that converges on every subject-session in this
  project's data (62/62 vs. paraboloid's 37/62). Fits a linear ramp *plus* a
  bounded Gaussian dip on top of it (`z = c0 + c1*x + c2*y - amp*exp(...)`),
  which is the shape this data actually has -- SSVEP amplitude falls off
  monotonically with red, and the isoluminant trough is a localized dip
  sitting on that ramp; `fit_paraboloid`/`fit_gaussian` each ask one term to
  represent both, which is why they fail so often.

  Two distinct quality flags, because they mean different things:
  `at_bound` -- some parameter (the dip's centre or width) is pegged against
  its bound, so the fit is reporting the edge of what the sampled range can
  express rather than a located dip (common and physiologically meaningful
  for CVD subjects whose true trough lies beyond the sampled red axis -- M6,
  `08_cvd_gamut.ipynb`). `fit_valid` -- the dip is deep enough to be real
  (`amp` above `min_snr` times the residual SD) **and** not `at_bound`. Only
  trust `red`/`green`/`amp`/`sigma_red`/`sigma_green` from rows where
  `fit_valid` is `True`; `r_squared` and `depth` are meaningful regardless
  (see `fit_trough_surface`'s notes below). `amp` (dip depth relative to the
  local ramp) and `sigma_red`/`sigma_green` (dip width per axis) have no
  argmin or paraboloid/Gaussian-fit equivalent.
- **`fit_trough_surface(grid, red_vals, green_vals, *, method=DEFAULT_SURFACE_METHOD) -> dict`**
  Dispatches to one of the three above (`'ramp_gaussian'` default,
  `'paraboloid'`, or `'gaussian'`) and normalizes the return schema so every
  caller sees the same keys regardless of method (`fit_paraboloid`/
  `fit_gaussian` return `amp`/`sigma_red`/`sigma_green`/`at_bound` as
  `NaN`/`False` to match). Call this one directly rather than
  `fit_paraboloid`/`fit_gaussian`/`fit_ramp_gaussian` in normal use, so
  `method` stays a single switch you can flip.

  **How to use this differently:**
  - *Compare both methods on one subject/session* -- call
    `fit_trough_surface` twice (`method='paraboloid'` and `'gaussian'`) on
    the same `grid`, and pass both results plus `trough_location`'s argmin
    into `plotting.plot_trough_locations` as one `locations` dict (see the
    plotting section below, and `06_trough_surface_fit.ipynb`).
  - *Get the paraboloid or Gaussian fit into the summary table instead of the
    default ramp_gaussian* -- `subject_troughs(runmap_df, baselines_df,
    metadata_df, surface_method='paraboloid')` (or `'gaussian'`). Note this is
    **not** what's in the persisted `subject_troughs.csv` (that file was built
    with the default `'ramp_gaussian'` via `scripts/build_troughs.py`) -- call
    `subject_troughs` yourself for a fresh DataFrame, or edit
    `build_troughs.py`'s call if you want a different method persisted
    instead.
  - *Only trust fits that actually converged to a real minimum* -- always
    filter on `fitted_valid` before using `fitted_red`/`fitted_green`/
    `fitted_depth`: `df[df['fitted_valid']]`. `ramp_gaussian` converges
    (`r_squared` non-NaN) on all 62 subject-sessions in this project's data,
    but `fit_valid` (a dip deep enough and not pegged at a bound) is a
    stricter bar -- currently true for CTR/PD but only ~2/8 protan and ~2/7
    deutan (see `docs/ssvep_analyses.md` proposal 2 and `08_cvd_gamut.ipynb`).
    For subjects that fail it, `ramp_slope_red` (M6, below) is usually a
    better fallback than trying another surface-fit method.
  - *Get raw (not baseline-normalized) fitted depth* -- pass `normalize=None`
    to `subject_troughs`, same as `trough_location`'s argmin columns already
    do (see "Trough location" above).

### Ramp-only fit, extrapolation, bootstrap CI (M6)

See `docs/ssvep_analyses.md` proposal 2 and `08_cvd_gamut.ipynb` for the full
worked analysis; this is the function reference.

- **`fit_ramp(grid, red_vals, green_vals) -> dict`**
  `{intercept, slope_red, slope_green, r_squared}` -- closed-form linear least
  squares on `z = c0 + c1*x + c2*y`, no dip term. Has no interior minimum to
  fail to find, so it's defined for every subject, including ones where
  `fit_ramp_gaussian` pegs (`at_bound=True`).
- **`extrapolate_ramp_crossing(ramp, target_depth, green_ref) -> float`**
  Solves `target_depth = ramp['intercept'] + ramp['slope_red']*red +
  ramp['slope_green']*green_ref` for `red`. Pass a `target_depth`/`green_ref`
  derived from subjects whose trough *was* actually located (e.g. the median
  `fitted_depth`/`fitted_green` among `fitted_valid` subjects of the same
  subgroup) rather than the pegged subject's own fit -- the result is always
  extrapolation beyond the sampled range for a pegged subject, and should be
  labelled as such wherever it's reported, not treated as a measurement.
- **`bootstrap_ci(replicate_fn, *, n_boot=2000, ci=0.95, seed=0) -> (float, float)`**
  Generic percentile bootstrap CI. `replicate_fn(rng)` computes and returns
  one resampled statistic using `rng` for its own resampling (e.g.
  `rng.choice(arr, size=len(arr), replace=True).mean()` for a proportion's
  CI, or resampling `run_grids`' output and refitting for a per-subject
  statistic's CI); called `n_boot` times, NaN replicates dropped before
  taking percentiles.

### Gain/shape decomposition (M8)

See `docs/ssvep_analyses.md` proposal 4 and `10_gain_shape.ipynb` for the full
worked analysis; this is the function reference.

- **`fit_gain_shape(grid, template) -> dict`**
  `{gain, intercept, r_squared, residual}` -- linear least squares fit of
  `grid ~= gain*template + intercept` over all 100 cells, where `template` is
  typically a reference group's mean grid (e.g. CTR). `gain` is a uniform
  scaling of the template's whole shape; `residual` (same shape as `grid`) is
  what's left after removing it -- near zero everywhere means `grid` really
  is just a scaled/shifted copy of `template`.
- **`trough_region_residual(residual, red_idx, green_idx, *, half_width=1) -> dict`**
  `{trough_region, rest_of_grid}` -- mean residual inside a
  `(2*half_width+1)^2` window centered on `(red_idx, green_idx)` (typically
  the *template's* own trough location -- see `analysis.trough_location` --
  not the subject's own, which is exactly the point for subjects whose own
  trough couldn't be located at all) versus the mean residual everywhere
  else. A negative `trough_region` well below `rest_of_grid` after gain is
  removed is the "structured residual concentrated near the trough" proposal
  4 describes as a shape-specific effect.

## `plotting.py` -- all figures

Axes convention: red is always x, green is always y (see `docs/methods.md`).
Every heatmap function takes optional `clim=(vmin, vmax)` and `cmap`
overrides; multi-panel functions share one `clim`/`cmap` across all panels
by default.

### Heatmaps

- **`plot_run(runmap_df, baselines_df, sub_id, session, run, *, normalize=None, clim=None, cmap=None, ax=None) -> Axes`**
- **`plot_all_runs(runmap_df, baselines_df, sub_id, session, *, normalize=None, clim=None, cmap=None) -> Figure`**
  One panel per run (3 or 4).
- **`plot_mean_run(runmap_df, baselines_df, sub_id, session, *, normalize=None, clim=None, cmap=None) -> Axes`**
- **`plot_mean_across_subjects(runmap_df, baselines_df, metadata_df, session, *, sub_ids=None, group=None, subgroup=None, normalize=None, clim=None, cmap=None) -> Axes`**
  Grand mean, or filtered by `group`/`subgroup`/explicit `sub_ids`.
- **`plot_subjects_side_by_side(runmap_df, baselines_df, metadata_df, session, *, sub_ids=None, group=None, subgroup=None, normalize=None, clim=None, cmap=None) -> Figure`**
  One panel per subject.
- **`plot_group_all_methods(runmap_df, baselines_df, metadata_df, session, *, sub_ids=None, group=None, subgroup=None, cmap=None) -> Figure`**
  One group's raw + percent/db/zscore, each independently scaled.
- **`plot_groups_side_by_side(runmap_df, baselines_df, metadata_df, session, categories, *, normalize=None, clim=None, cmap=None) -> Figure`**
  One panel per named category (`categories` = list of
  `{"label", "group", "subgroup"}`), titled with sample size.
- **`plot_interpolated_grid(grid, shape, *, method='linear', label='value', diverging=False, clim=None, cmap=None, title=None, ax=None) -> Axes`**
  Any grid (raw, normalized, single-subject, or group mean), resized via
  `analysis.interpolate_grid` before plotting.

### Pixel distributions (M2)

- **`plot_subject_boxplot`/`plot_subject_histogram(runmap_df, baselines_df, sub_id, session, *, normalize=None, [bins=30,] ax=None) -> Axes`**
  Single box/histogram: `flatten_runs` (all-run pixels).
- **`plot_subject_mean_boxplot`/`plot_subject_mean_histogram(runmap_df, baselines_df, sub_id, session, *, normalize=None, [bins=30,] ax=None) -> Axes`**
  Single box/histogram: `mean_grid` raveled (100 cells).
- **`plot_subjects_boxplot(runmap_df, baselines_df, metadata_df, session, *, sub_ids=None, group=None, subgroup=None, normalize=None) -> Axes`**
  One box per subject, `flatten_runs` each.
- **`plot_subjects_mean_boxplot(...) -> Axes`**
  One box per subject, `mean_grid` each.
- **`plot_group_pooled_boxplot(runmap_df, baselines_df, metadata_df, session, *, sub_ids=None, group=None, subgroup=None, normalize=None, ax=None) -> Axes`**
  Single box: `pooled_pixels` for the whole group.
- **`plot_group_mean_boxplot(...) -> Axes`**
  Single box: `mean_grid_across_subjects` raveled (the group's mean-of-means, 100 cells).
- **`plot_groups_pooled_boxplot(runmap_df, baselines_df, metadata_df, session, categories, *, normalize=None) -> Axes`**
  One box per category, pooled-pixels strategy.
- **`plot_groups_mean_boxplot(...) -> Axes`**
  One box per category, mean-grid strategy.
- **`plot_groups_baseline_boxplot(baselines_df, metadata_df, session, categories, *, trials='all') -> Axes`**
  One box per category, raw baseline trial values pooled across every run and
  subject (`pooled_baseline_values`) -- always raw, never normalized.

All boxplot/histogram functions use one uniform fill color
(`DISTRIBUTION_COLOR`) -- category identity is carried by the x-axis tick
labels, not color.

### Trough scatter (M2)

- **`plot_trough_scatter(troughs_df, label_col, *, ax=None) -> Axes`**
  Scatter of `(red, green)` trough locations from a `subject_troughs`/
  `group_troughs` table, one marker **shape** per distinct `label_col` value
  (`'group'` or `'label'`) -- shape rather than color, since a scatter's
  all-pairs color comparisons only stay colorblind-safe up to 3 categories.
- **`plot_troughs_boxplot(troughs_df, value_col, label_col, *, ylabel=None, ax=None) -> Axes`**
  One box per distinct `label_col` value in `troughs_df` (a `subject_troughs`
  table, or anything with that shape), from `troughs_df[value_col]` -- any
  per-subject scalar feature (e.g. `ramp_slope_red`) against `group`/
  `subgroup`/a hand-built `label` column. NaNs dropped per category, so a
  column that's only sometimes defined (like `fitted_red`) still plots
  cleanly. (M6, `08_cvd_gamut.ipynb`.)

### Parametric trough surface fit (M4)

- **`plot_trough_locations(grid, locations, *, cmap=None, clim=None, ax=None) -> Axes`**
  Heatmap of `grid` with one marker per named location in `locations` (e.g.
  `{"argmin": trough_location(...), "paraboloid": fit_trough_surface(...)}`)
  -- for visually comparing trough-finding methods on one subject. Physical
  red/green values are interpolated onto the heatmap's pixel-index axes, so
  a fit's continuous, off-grid location overlays correctly; NaN locations
  (failed fits) are skipped.

  **How to use this differently:** `locations` is just a plain dict, so any
  combination/number of named locations works -- e.g. drop a key to compare
  only two methods, or add a 4th entry for a hand-picked reference point
  (`{"red": 1600, "green": 1000, "depth": grid_value_there}` -- `depth` isn't
  actually used for plotting, only `red`/`green`, but keeping the same shape
  as the other dicts makes it a drop-in). Marker shapes are assigned in
  dict-iteration order from `MARKER_SHAPES`, so the first ~7 entries each get
  a distinct shape.

### Permutation test results (M3)

- **`plot_permutation_result(result, panels, *, title=None, cmap=None) -> Figure`**
  Generic: one panel per `(result_key, panel_title)` pair from any
  `permutation.permutation_test_*` result dict, sharing one z-score color
  scale. The three functions below are thin presets over this.
- **`plot_permutation_test_size(result, *, title=None, cmap=None) -> Figure`**
  Panels: difference / uncorrected / cluster-size-corrected.
- **`plot_permutation_test_weighted(result, *, title=None, cmap=None) -> Figure`**
  Panels: difference / uncorrected / size-corrected / weight-corrected.
- **`plot_permutation_test_directional(result, *, title=None, cmap=None) -> Figure`**
  Panels: difference / uncorrected / size-corrected (+/-) / weight-corrected (+/-).
- **`plot_permutation_null_histogram(null_values, threshold, *, xlabel, ax=None) -> Axes`**
  Histogram of a null max-cluster-statistic distribution (e.g.
  `result['null_sizes']`/`result['null_weights']`) with the threshold marked.

## `permutation.py` -- cluster-based permutation testing (M3)

Replicates `ssveps/templateCode/permTestingcomparisons/*.m`; see
`docs/methods.md` for the methodology, the subsampling rationale, and the
negative-cluster fix vs. the template. All three take the same core
parameters: `runmap_df, baselines_df, metadata_df, session, *, group1=None,
subgroup1=None, group2=None, subgroup2=None, normalize=DEFAULT_NORMALIZE,
n1=None, n2=None, n_perm=1000, pval=0.05, seed=None`. `n1`/`n2` default to
both groups balanced to the smaller group's full size.

- **`permutation_test_size(...) -> dict`**
  `{zdiff, zthresh_uncorrected, zthresh_corrected, size_thresh, null_sizes, sig_thresh, n1, n2}`.
- **`permutation_test_weighted(...) -> dict`**
  `{zdiff, zthresh_uncorrected, zthresh_size_corrected, zthresh_weight_corrected, size_thresh, weight_thresh, null_sizes, null_weights, cluster_results, sig_thresh, n1, n2}`.
  `cluster_results` is a list of `{size, weight, pvalue}` per observed cluster.
- **`permutation_test_directional(...) -> dict`**
  `{zdiff, zthresh_uncorrected, zthresh_size_pos, zthresh_size_neg, zthresh_weight_pos, zthresh_weight_neg, pos_size_thresh, neg_size_thresh, pos_weight_thresh, neg_weight_thresh, null_pos_sizes, null_neg_sizes, null_pos_weights, null_neg_weights, cluster_results, sig_thresh, n1, n2}`.
  `cluster_results` is a list of `{sign, size, weight, pvalue}` per observed cluster.

All three `z*` arrays are `[red_idx, green_idx]` grids, plottable directly
with the "Permutation test results" functions above.

### Reliability & agreement (M5)

- **`plot_icc_map(icc, *, title=None, cmap=None, ax=None) -> Axes`**
  Heatmap of a `[red_idx, green_idx]` ICC map (`reliability.icc_map`), fixed
  to the `[0, 1]` ICC scale. `title` defaults to the map's mean/median ICC --
  pass your own (e.g. `f"{label} (n={len(sub_ids)})"`) to compare several
  groups' maps by eye, as `07_test_retest_reliability.ipynb` does.
- **`plot_bland_altman(values1, values2, *, ax=None) -> Axes`**
  Mean-vs-difference plot for one pair of paired session arrays (e.g. from
  `reliability.session_pair_values`), with the bias (mean difference) and
  +/-1.96 SD limits of agreement drawn as reference lines.
- **`plot_session_scatter(values1, values2, *, ax=None) -> Axes`**
  Session 1 vs. session 2 scatter for the same kind of paired arrays, with a
  y=x identity line -- the plain-correlation complement to Bland-Altman's
  bias/spread view.
- **`plot_example_points(runmap_df, baselines_df, sub_ids, points, *, kind='bland_altman'|'scatter', normalize=DEFAULT_NORMALIZE, title=None) -> Figure`**
  One panel per point in `points` (each `{"label", "red_idx", "green_idx"}`,
  from `reliability.example_points_fixed`/`example_points_informative`),
  using `plot_bland_altman` or `plot_session_scatter` per panel depending on
  `kind`. This is the one you actually call in a notebook -- `points` +
  `sub_ids` decide *which* pixels and *which* subjects, `kind` decides which
  of the two plot types.

  **How to use this differently:**
  - *Bland-Altman vs. scatter for the same points* -- call twice with
    `kind='bland_altman'` and `kind='scatter'`; both take the exact same
    `points`/`sub_ids`, so the two calls are directly comparable pixel-by-pixel.
  - *Different pixels* -- swap `points` for whatever
    `reliability.example_points_fixed`/`example_points_informative` (or a
    hand-built list of `{"label", "red_idx", "green_idx"}` dicts) gives you.
  - *Different subjects* -- swap `sub_ids` (e.g. `pd_paired` vs. `ctr_paired`
    vs. `all_paired` from `reliability.paired_subjects`); always set `title`
    when looping over several groups in one notebook so each figure is
    labeled (`fig.suptitle` after the fact will overlap the panel titles --
    pass `title=` instead, it's applied before `tight_layout`).
  - *Raw instead of normalized values* -- pass `normalize=None`.

## `reliability.py` -- test-retest reliability via per-pixel ICC (M5)

Replicates `ssveps/templateCode/ICCs/computeICC_gridMaps.m`; see
`docs/methods.md` for the methodology. Typical order of calls (see
`07_test_retest_reliability.ipynb`): `paired_subjects` -> `icc_grid` ->
`icc_map` (for the heatmap) and/or `example_points_fixed`/
`example_points_informative` + `session_pair_values` (for Bland-Altman/scatter
at specific pixels).

- **`paired_subjects(metadata_df, *, group=None, subgroup=None) -> list[str]`**
  Subject IDs present at both session 1 and session 2 (checked at session 1
  for the group/subgroup filter).

  **How to use this differently:** this is the one function that decides
  *who* every other reliability computation below runs on -- change `group`/
  `subgroup` to restrict to any subset (`group='PD'`, `group='CTR'`, or
  leave both `None` for everyone with both sessions, 19 subjects in this
  project's data). Not every filter returns enough subjects for `icc_grid`
  to run on, though -- see that function's "minimum sample size" note below
  before picking one. Whatever list comes back here is what you feed into
  `icc_grid`, `example_points_*`, and `plot_example_points` as `sub_ids` --
  keep the *same* list across all three when you want one consistent group's
  results (`07_test_retest_reliability.ipynb`'s `groups` dict does exactly
  this: one `sub_ids` list per group, reused everywhere below).
- **`icc_grid(runmap_df, baselines_df, sub_ids, *, normalize=DEFAULT_NORMALIZE) -> DataFrame`**
  One row per grid cell: `red_idx, green_idx, icc, ci_lower, ci_upper, f,
  df1, df2, pval` -- per-pixel `ICC(A,1)` (pingouin) between session 1 and
  session 2 mean grids across `sub_ids` (each must be in both sessions --
  pass the output of `paired_subjects`, not an arbitrary list).
- **`feature_icc(values1, values2) -> dict`** (M9)
  `{icc, ci_lower, ci_upper, f, df1, df2, pval}` -- the same `ICC(A,1)`
  computation as `icc_grid`, but for one per-subject scalar feature (e.g.
  `subject_troughs.csv`'s `depth`, `ramp_slope_red`, or a hand-computed `gain`
  series) instead of one grid cell. `values1`/`values2` must be in the same
  subject order; needs >=3 paired subjects, same as `icc_grid`. See
  `11_reliability_outcomes.ipynb`.
- **`minimum_detectable_effect(n1, n2, *, icc=1.0, alpha=0.05, power=0.8) -> float`** (M9)
  The smallest true (population) Cohen's d a two-sample comparison with
  `n1`/`n2` subjects per group can detect at `power`, on a measure with
  test-retest reliability `icc`. `icc=1.0` (default) is the textbook
  noiseless-measure formula; a lower `icc` divides the result by `sqrt(icc)`
  (classical test theory's attenuation correction), so an unreliable feature
  needs a bigger true effect to ever be detectable at a given n -- see
  `11_reliability_outcomes.ipynb`'s synthetic walkthrough for why.

  **How to use this differently:** *raw instead of normalized* --
  `normalize=None`. Takes a few seconds per call (one `pingouin` ANOVA per
  of the 100 grid cells) -- cheap enough to call fresh each time rather than
  needing to cache/persist it (this project deliberately doesn't -- see
  `docs/methods.md`).

  **Minimum sample size:** raises `ValueError` for fewer than 3 paired
  subjects (pingouin's ANOVA needs >=5 subject-x-session rows). Checked
  against this project's real data: `paired_subjects(metadata_df,
  group='PD')` (n=4) and `group='CTR'` (n=13) both work; `subgroup='protan'`
  (n=2), `subgroup='deutan'` (n=0), and `group='CVD'` (n=2, protan+deutan
  combined) are all **too small** and will raise -- only `PD`, `CTR`, and
  the unfiltered "all paired" (n=19) have enough paired subjects for
  `icc_grid` in this dataset today. That may change as more session-2 data
  comes in (`docs/methods.md`'s note on the still-thin CVD/protan/deutan
  test-retest sample).
- **`icc_map(icc_df) -> ndarray`**
  Pivots `icc_grid`'s tidy output into a `[red_idx, green_idx]` 10x10 array
  -- feed straight into `plotting.plot_icc_map`.
- **`session_pair_values(runmap_df, baselines_df, sub_ids, red_idx, green_idx, *, normalize=DEFAULT_NORMALIZE) -> (ndarray, ndarray)`**
  The raw session 1 / session 2 values at *one* grid cell across `sub_ids` --
  the paired data behind one `icc_grid` row.

  **How to use this differently:** call this directly (skipping
  `example_points_*`) whenever you already know which pixel you care about
  -- e.g. `session_pair_values(runmap_df, baselines_df, all_paired, 4, 6)`
  for the exact cell `analysis.trough_location(...)` returned as
  `red_idx`/`green_idx`. Feed the two returned arrays into
  `plotting.plot_bland_altman`/`plot_session_scatter` directly if you don't
  need `plot_example_points`'s multi-panel layout.
- **`example_points_fixed(red_vals, green_vals) -> list[dict]`**
  The template's 5 hardcoded (red, green) targets (from `ICC_grids_22oct25.m`),
  snapped to the nearest grid index -- same 5 points regardless of the data,
  for comparing against the original MATLAB analysis.
- **`example_points_informative(icc_df, *, trough_red_idx=None, trough_green_idx=None) -> list[dict]`**
  Data-driven points instead: the pixel with the lowest ICC in `icc_df`
  (worst reliability), the pixel with the highest ICC (best), and -- only if
  you pass them -- the group's own trough location as a third point.

  **How to use this differently:** these two are interchangeable inputs to
  `plotting.plot_example_points`'s `points` argument -- pick
  `example_points_fixed` to reproduce the template's exact analysis, or
  `example_points_informative` to actually look at *this* group's most/least
  reliable pixels (which move around depending on `icc_df`, i.e. depending
  on which `sub_ids` you ran `icc_grid` on -- recompute `icc_df` per group
  before calling this, don't reuse one group's `icc_df` for another). To get
  the trough point, compute it yourself first and pass its indices in:
  `loc = analysis.trough_location(analysis.mean_grid_across_subjects(runmap_df,
  baselines_df, sub_ids, 1, normalize=DEFAULT_NORMALIZE), red_vals,
  green_vals)` then `trough_red_idx=loc['red_idx'],
  trough_green_idx=loc['green_idx']` -- use `mean_grid_across_subjects` over
  exactly the same `sub_ids` you're reporting ICC for (not `group_grid`,
  which would re-derive a possibly-different subject list from `group`/
  `subgroup` filters -- see `07_test_retest_reliability.ipynb` for the
  worked example). Omit both `trough_*` arguments to get just the 2
  ICC-extreme points.

## `variance.py` -- within/between-subject variance decomposition (M7)

Replicates `docs/ssvep_analyses.md` proposal 3's within/between-subject SD
split properly: a random-intercept MixedLM fit **per group** (not one pooled
model -- see `docs/methods.md` for why), plus a subject-level bootstrap CI on
each variance component. See `09_variance_components.ipynb` for the full
worked analysis.

- **`group_run_values(runmap_df, baselines_df, metadata_df, session, *, group=None, subgroup=None, normalize=DEFAULT_NORMALIZE) -> dict[str, ndarray]`**
  `sub_id -> analysis.run_mean_values` for every subject matching
  `group`/`subgroup` at `session` -- the input every other function in this
  module takes.
- **`variance_components(values_by_subject, *, n_boot=2000, seed=0) -> dict`**
  `{within_sd, between_sd, within_ci, between_ci, n_subjects, n_boot_used}` --
  fits a random-intercept-only MixedLM (`value ~ 1`, grouped by subject) to
  get the point estimates, then a subject-level percentile bootstrap (resample
  subjects with replacement, refit, repeat) for each CI. Each bootstrap
  resample is relabeled with fresh synthetic subject ids so a real subject
  drawn twice is correctly treated as two independent subjects for that
  replicate, not as one subject with double the runs. `n_boot=2000` takes
  roughly 15-50s per group depending on its size (real per-fit cost is
  ~15-25ms) -- budget a couple of minutes to run this across every group.
- **`within_subject_cv(values_by_subject) -> dict[str, float]`**
  Per-subject within-subject coefficient of variation (`SD/|mean|` of that
  subject's own run values, `ddof=1`) -- corrects for response magnitude
  scaling the raw within-subject SD, so groups with different average
  response sizes stay comparable on noise alone.

## `pca.py` -- PCA of the response grid (M10)

Treats each subject's 10x10 grid as one 100-dimensional observation instead
of collapsing it to a single number or running 100 cell-wise tests. See
`docs/ssvep_analyses.md` proposal 7 and `12_pca.ipynb` for the full worked
analysis.

- **`pixel_matrix(runmap_df, baselines_df, metadata_df, session, *, normalize=DEFAULT_NORMALIZE) -> (DataFrame, ndarray)`**
  Every subject's mean grid at `session`, flattened and stacked into an
  `(n_subjects, 100)` matrix -- the input every function below takes.
  Returns `(metadata rows in matrix row order, matrix)`; row `i` of the
  metadata frame describes row `i` of the matrix.
- **`fit_pca(X) -> dict`**
  `{mean, components, scores, explained_variance, explained_variance_ratio}`
  -- ordinary PCA via SVD on mean-centered `X`, no covariance shrinkage.
  `components[k]` is the k-th principal axis (reshape to `(10, 10)` to view
  as a grid); `scores[:, k]` is every subject's projection onto it. Component
  sign is an SVD convention, not a data property.
- **`permutation_component_count(X, *, n_perm=2000, alpha=0.05, seed=0) -> dict`**
  `{observed_ratio, null_ratio_threshold, n_components_real}` -- how many
  components carry more structure than chance, via a numpy-native version of
  Horn's (1965) parallel analysis: permute each column (grid cell)
  independently across subjects (destroys cross-cell correlation, keeps each
  cell's own marginal distribution), redo PCA, repeat `n_perm` times to build
  a null explained-variance-ratio spectrum, and count the leading run of
  components whose observed ratio clears its own rank's `(1-alpha)` null
  percentile. This project's regularization-free alternative to a fixed
  component cutoff or a shrinkage-covariance estimate (see `docs/methods.md`
  for why).

## Build scripts

- **`scripts/build_derived.py`** -- full from-scratch rebuild of
  `metadata.csv`/`grid.json`/`runmap.csv`/`baselines.csv` from every raw
  `.mat` file. Wipes hand-edits to `metadata.csv`; intentional-reset-only.
- **`scripts/update_derived.py`** -- incremental version of the above that
  preserves hand-edited `group`/`subgroup` values. Use this day to day.
- **`scripts/build_troughs.py`** -- builds `subject_troughs.csv` and
  `group_troughs.csv` from the other derived CSVs (straight recompute, no
  hand-edits to preserve, safe to rerun anytime).

## Notebooks

All start with `sys.path.append('../scripts')` then load `runmap_df`/
`baselines_df`/`metadata_df` via `analysis.load_*`. Rerunning a whole
notebook top-to-bottom always reproduces its saved output (M3/M5's
randomized/stochastic steps are seeded). To point one at different data,
edit the variables called out below and rerun from that cell down.

- **`01_explore.ipynb`** -- loads one raw `.mat` file (`loader.load_ssvep`)
  and inspects its keys/shapes. *Edit:* `RAW_PATH` (top cell) to inspect a
  different subject/session's raw file directly, bypassing the tidy CSVs
  entirely -- useful when you suspect the CSVs themselves might be wrong,
  since this is the only notebook that reads raw `.mat` data.
- **`02_plots.ipynb`** -- heatmaps for one subject: single run, all runs,
  mean-across-runs; raw and normalized side by side; `clim`/`cmap`
  overrides; grand mean and group means across subjects. *Edit:* the
  `sub_id`/`session`/`run` arguments passed to each `plot_*` call (no single
  top-level constant -- each cell names its subject inline); swap
  `normalize=` dicts to try other scope/trials/method combinations.
- **`03_group_comparisons.ipynb`** -- one group's raw + all 3 normalization
  methods side by side (`plot_group_all_methods`); interpolated 100x100
  views; PD/HC/protan/deutan side by side (`plot_groups_side_by_side`).
  *Edit:* `SESSION` and the `categories` list (top cell) -- add/remove/rename
  categories (any `group`/`subgroup` combination) to change which groups
  every plot in the notebook compares.
- **`04_distributions.ipynb`** -- boxplots/histograms of pixel distributions
  (M2): one subject's all-run pixels and mean-grid pixels (raw + %change);
  per-subject boxplots within a group; pooled and mean-of-means boxplots for
  one group and for several groups side by side; a raw baseline comparison
  across groups (`plot_groups_baseline_boxplot`); trough summary tables
  (`subject_troughs.csv`/`group_troughs.csv`) and a trough-location scatter.
  *Edit:* `SESSION`, `SUB_ID` (single-subject sections), `categories` (group
  sections, also used by the baseline comparison), `PERCENT` (or any other
  `normalize=` dict) -- e.g. swap `PERCENT` for `{'scope': 'session', 'trials':
  'first2', 'method': 'zscore'}` to redo every normalized plot with a
  different normalization strategy.
- **`05_permutation_testing.ipynb`** -- cluster-based permutation testing
  (M3), all 3 sophistication levels (`permutation.permutation_test_size` /
  `_weighted` / `_directional`) between group pairs, plus null-distribution
  histograms. *Edit:* `SESSION`, `SEED` (top cell); the `comparisons` list in
  the directional section (`group1`/`subgroup1`/`group2`/`subgroup2` per
  entry -- any pair, not just the 3 shown); `n_perm`/`pval`/`n1`/`n2` on any
  individual `permutation_test_*` call to change power/strictness/sample
  balancing for that one comparison.
- **`06_trough_surface_fit.ipynb`** -- parametric surface fit for trough
  localization (M4): one subject's argmin vs. paraboloid vs. Gaussian fit,
  overlaid on its heatmap; the ragged 3-run case; fit-quality (`r_squared`)
  and argmin-vs-fitted agreement across every subject/session in
  `subject_troughs.csv`. Predates `ramp_gaussian` becoming the default
  surface method, so it isn't covered here -- see `08_cvd_gamut.ipynb` for
  that fit in use. *Edit:* the `sub_id` passed to `mean_grid`/
  `fit_trough_surface` in the single-subject cells to inspect a different
  subject; `method='paraboloid'|'gaussian'` on any `fit_trough_surface` call.
- **`07_test_retest_reliability.ipynb`** -- per-pixel ICC(A,1) test-retest
  reliability (M5): ICC maps for all paired subjects, PD, and HC; Bland-Altman
  and session1-vs-session2 scatter plots at the template's fixed example
  points and at data-driven (lowest/highest ICC + trough) points, per group.
  *Edit:* `GROUP_SPECS` (top cell, a list of `{"label", "group", "subgroup"}`
  dicts) to change which subject sets get their own ICC map and
  example-point plots -- one loop builds `groups`/`icc_dfs`/`icc_maps`/
  `troughs` from it, and every later cell reads those dicts, so adding an
  entry there is genuinely the only edit needed. **But check the sample size
  first**: `icc_grid` needs >=3 paired subjects, and in this project's data
  today only `group='PD'` (n=4), `group='CTR'` (n=13), and the unfiltered
  "all paired" (n=19) qualify -- `subgroup='protan'` (n=2), `subgroup=
  'deutan'` (n=0), and `group='CVD'` (n=2) don't, and `icc_grid` will raise
  a clear `ValueError` naming the problem rather than adding a broken entry
  silently.
- **`08_cvd_gamut.ipynb`** -- M6, `docs/ssvep_analyses.md` proposal 2:
  `fitted_at_bound` sensitivity/specificity with a bootstrap CI and a Fisher
  exact test (CVD vs CTR); `ramp_slope_red` as a measure defined for every CVD
  subject, boxplotted by subgroup; `extrapolate_ramp_crossing` with a
  run-level bootstrap CI for pegged subjects, with an explicit caveat about
  its instability; and the protan-vs-deutan subtype test on both measures
  (currently not significant at this project's sample size -- see the
  notebook's section 4 for the numbers). *Edit:* `SESSION` (top cell); the
  `reference()` function in section 3 to change what pegged subjects'
  extrapolation targets against.
- **`09_variance_components.ipynb`** -- M7, `docs/ssvep_analyses.md` proposal
  3: `variance.variance_components` (MixedLM per group + bootstrap CI) for
  within/between-subject SD by group, an errorbar plot of both, and
  `variance.within_subject_cv` to check the "not elevated" finding survives
  correcting for response-size scaling. Currently PD's within-subject SD is
  not elevated (confirms the earlier point estimate) and its between-subject
  CI is wide and overlaps CTR's (also confirms); deutan's between-subject CI
  does **not** overlap CTR's -- lower, not higher -- which is a new result
  this notebook's proper model surfaced. *Edit:* `SESSION`, `categories` (top
  cell); `n_boot` on the `variance_components` call to trade CI precision for
  runtime.
- **`10_gain_shape.ipynb`** -- M8, `docs/ssvep_analyses.md` proposal 4:
  `analysis.fit_gain_shape` against the CTR template for every subject, then
  `analysis.trough_region_residual` at the template's own trough to ask
  whether a group's deficit is a uniform gain change or something
  trough-specific; a cross-check of `gain` against `ramp_intercept` (M6) and
  `trough_region_residual` against `fitted_amp` (M4/M6). Currently protan
  shows a genuine trough-specific residual beyond gain (p=0.030, n=8, one
  test, uncorrected) that PD and deutan don't -- ties together with M6's
  `ramp_slope_red` finding that protan's trough sits furthest beyond the
  sampled range. *Edit:* `SESSION` (top cell); swap `group='CTR'` in the
  `group_grid` call for a different reference template.
- **`11_reliability_outcomes.ipynb`** -- M9, `docs/ssvep_analyses.md`
  proposal 5: `reliability.feature_icc` for six candidate outcome features
  (`depth`, `ramp_slope_red`, `gain` on all 19 paired subjects;
  `fitted_green`/`fitted_amp`/`fitted_red` restricted to the 14 with a valid
  `fit_ramp_gaussian` fit at both sessions), then
  `reliability.minimum_detectable_effect` at this project's two actual
  comparisons (PD vs CTR, protan vs deutan). Currently `gain` (ICC=0.90) and
  `ramp_slope_red` (ICC=0.85) are *more* reliable than `depth` (ICC=0.76,
  the previous primary-outcome recommendation); `fitted_red` (ICC=0.18)
  needs a true effect over d=3 to ever be detectable at this project's n --
  functionally unusable. *Edit:* the `features` list in the ICC cell to add
  a new candidate; the two `n1, n2` pairs passed to
  `minimum_detectable_effect` to check a different comparison.
- **`12_pca.ipynb`** -- M10, `docs/ssvep_analyses.md` proposal 7:
  `pca.pixel_matrix` + `pca.fit_pca` on all 43 session-1 grids, `pca.
  permutation_component_count` to decide how many components to trust,
  loading-map heatmaps for PC1-3, and a group comparison of PC1 scores.
  Currently only PC1 (75% of variance) clears the permutation noise floor;
  it correlates at r=-0.93 with M8's `gain` and M6's `ramp_intercept` --
  the same gain axis found three independent ways. PC1 doesn't separate PD
  from CTR (p=0.63) but comes closer than any single M6/M8 measure did on
  protan vs. deutan (p=0.092, not significant, exploratory). *Edit:*
  `SESSION` (top cell); `n_perm` on `permutation_component_count` to trade
  precision for runtime.
