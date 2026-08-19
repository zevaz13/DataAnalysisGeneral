# SSVEP scripts: function reference

Everything lives in `ssveps/scripts/`. Notebooks (`ssveps/notebooks/`) call
these directly after `sys.path.append('../scripts')`. See `docs/methods.md`
for the conventions (baseline split, normalization formulas, axis
orientation) these functions implement.

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
- **`subject_troughs(runmap_df, baselines_df, metadata_df, *, normalize=DEFAULT_TROUGH_NORMALIZE) -> DataFrame`**
  One row per `(sub_id, session)` in `metadata_df`:
  `sub_id, session, group, subgroup, red, green, depth, red_idx, green_idx`.
- **`group_troughs(runmap_df, baselines_df, metadata_df, sessions, categories, *, normalize=DEFAULT_TROUGH_NORMALIZE) -> DataFrame`**
  One row per `(session, category)` with >=1 subject:
  `label, session, n, red, green, depth, red_idx, green_idx`. `categories` is
  a list of `{"label": str, "group": str|None, "subgroup": str|None}` (same
  shape as `plotting.plot_groups_side_by_side`'s `categories`).
  `DEFAULT_TROUGH_NORMALIZE = {"scope": "run", "trials": "all", "method": "percent"}`.

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

## Build scripts

- **`scripts/build_derived.py`** -- full from-scratch rebuild of
  `metadata.csv`/`grid.json`/`runmap.csv`/`baselines.csv` from every raw
  `.mat` file. Wipes hand-edits to `metadata.csv`; intentional-reset-only.
- **`scripts/update_derived.py`** -- incremental version of the above that
  preserves hand-edited `group`/`subgroup` values. Use this day to day.
- **`scripts/build_troughs.py`** -- builds `subject_troughs.csv` and
  `group_troughs.csv` from the other derived CSVs (straight recompute, no
  hand-edits to preserve, safe to rerun anytime).
