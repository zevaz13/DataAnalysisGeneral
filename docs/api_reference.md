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

### Trough location (M2)

- **`trough_location(grid, red_vals, green_vals) -> dict`**
  `{red, green, depth, red_idx, green_idx}` for a grid's minimum (native
  resolution, `np.argmin`).
- **`subject_troughs(runmap_df, baselines_df, metadata_df, *, normalize=DEFAULT_NORMALIZE, surface_method='paraboloid') -> DataFrame`**
  One row per `(sub_id, session)` in `metadata_df`: `sub_id, session, group,
  subgroup, red, green, depth, red_idx, green_idx` (argmin) plus
  `fitted_red, fitted_green, fitted_depth, fitted_r_squared, fitted_valid`
  (parametric fit, M4 -- see below).
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
  surface fit; the analytic minimum need not land on a grid point.
- **`fit_gaussian(grid, red_vals, green_vals) -> dict`**
  Same shape, from an inverted 2D Gaussian dip (`scipy.optimize.curve_fit`,
  seeded from `trough_location`'s argmin).
- **`fit_trough_surface(grid, red_vals, green_vals, *, method='paraboloid'|'gaussian') -> dict`**
  Dispatches to one of the above. Call this one directly rather than
  `fit_paraboloid`/`fit_gaussian` in normal use, so `method` stays a single
  switch you can flip.

  **How to use this differently:**
  - *Compare both methods on one subject/session* -- call
    `fit_trough_surface` twice (`method='paraboloid'` and `'gaussian'`) on
    the same `grid`, and pass both results plus `trough_location`'s argmin
    into `plotting.plot_trough_locations` as one `locations` dict (see the
    plotting section below, and `06_trough_surface_fit.ipynb`).
  - *Get the Gaussian fit into the summary table instead of the paraboloid*
    -- `subject_troughs(runmap_df, baselines_df, metadata_df,
    surface_method='gaussian')`. Note this is **not** what's in the
    persisted `subject_troughs.csv` (that file was built with the default
    `'paraboloid'` via `scripts/build_troughs.py`) -- call `subject_troughs`
    yourself with `surface_method='gaussian'` for a fresh DataFrame, or edit
    `build_troughs.py`'s call if you want the Gaussian version persisted
    instead.
  - *Only trust fits that actually converged to a real minimum* -- always
    filter on `fitted_valid` before using `fitted_red`/`fitted_green`/
    `fitted_depth`: `df[df['fitted_valid']]`. In practice the paraboloid is
    valid for about 60% of subject/sessions and the Gaussian for about 80%
    (checked against this project's real data) -- a subject failing one
    method doesn't necessarily fail the other, so if you need every subject
    covered, try both and fall back method-by-method rather than dropping
    the failures outright.
  - *Get raw (not baseline-normalized) fitted depth* -- pass `normalize=None`
    to `subject_troughs`, same as `trough_location`'s argmin columns already
    do (see "Trough location" above).

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

All boxplot/histogram functions use one uniform fill color
(`DISTRIBUTION_COLOR`) -- category identity is carried by the x-axis tick
labels, not color.

### Trough scatter (M2)

- **`plot_trough_scatter(troughs_df, label_col, *, ax=None) -> Axes`**
  Scatter of `(red, green)` trough locations from a `subject_troughs`/
  `group_troughs` table, one marker **shape** per distinct `label_col` value
  (`'group'` or `'label'`) -- shape rather than color, since a scatter's
  all-pairs color comparisons only stay colorblind-safe up to 3 categories.

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
  one group and for several groups side by side; trough summary tables
  (`subject_troughs.csv`/`group_troughs.csv`) and a trough-location scatter.
  *Edit:* `SESSION`, `SUB_ID` (single-subject sections), `categories` (group
  sections), `PERCENT` (or any other `normalize=` dict) -- e.g. swap
  `PERCENT` for `{'scope': 'session', 'trials': 'first2', 'method': 'zscore'}`
  to redo every normalized plot with a different normalization strategy.
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
  `subject_troughs.csv`. *Edit:* the `sub_id` passed to `mean_grid`/
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
