# SSVEPs

SSVEP (steady-state visual evoked potential) grid experiment data.

Raw data: `/home/sebas/data/ssveps/` (read in place, not copied into the repo).
62 MATLAB `.mat` files, one per subject/session, 43 unique subjects. Filename
is `METxxx[b].mat`: `METxxx` is the subject id, the optional trailing letter
is the session (no letter = session 1, `b` = session 2; the plan's `c`/session
3 does not occur in this dataset).

## Fields (per raw `.mat` file)

- `SubID` — subject id string (stable per subject across sessions)
- `session` — session number (1 or 2)
- `group` — `CTR`/`PD`/`HD`/`CVD`/`UNKNOWN` (stable per subject)
- `subgroup` — `protan`/`deutan`/`NA`, color-blindness type (stable per subject)
- `redArray`, `greenArray` — 10 intensity levels each, defining the grid axes (identical across all 62 files)
- `runMap` — grid of measurements, shape `(red, green, run)` per `mapDIM` (`RED_GREEN_RUN`); run count is usually 4, but only 3 for `MET037-040` (all group `PD`)
- `baselines` — shape `(trial, run)` per `baseDIM` (`TR_RUN`); 4 baseline trials per run, trials 1-2 pre-grid and 3-4 post-grid

## Derived files (`files/`)

- `metadata.csv` — one row per subject-session: `filename, sub_id, session, group, subgroup`.
  **`group`/`subgroup` are set once, when a row is first created, and are never
  overwritten automatically afterward** (see `scripts/update_derived.py`) --
  correct them by editing `metadata.csv` directly.
- `grid.json` — the shared grid constants: `redArray`, `greenArray`, `baseDIM`, `mapDIM`
- `runmap.csv` — tidy long format: `sub_id, session, run, red_idx, green_idx, value`
  (`red_idx`/`green_idx` are 0-based positions into `grid.json`'s arrays; `run` is 1-based)
- `baselines.csv` — tidy long format: `sub_id, session, run, trial, value` (1-based `run`/`trial`)

## Analysis

- `scripts/analysis.py` — `raw_grid`/`mean_raw_grid`/`mean_grid` (10x10 red x
  green grids from `runmap.csv`; `mean_grid` takes an optional `normalize=`
  dict and covers both the raw and normalized case), `baseline_values` (select
  baseline trials: `scope='run'` uses one run's own trials, `scope='session'`
  pools trials across every run of the session; `trials='all'/'first2'/'last2'`,
  where first2/last2 = pre-/post-grid), `normalize_grid`/`normalized_grid`
  (`method='percent'/'db'/'zscore'`, baseline reduced to its mean, z-score also
  uses its std), `subjects_in_group`/`mean_grid_across_subjects`/`group_grid`
  for cross-subject aggregation (`group_grid` composes the first two; one
  session at a time, so 2-session subjects aren't double-counted), and
  `interpolate_grid(grid, (n_red, n_green))` to resize a grid to an arbitrary
  (including rectangular) resolution via linear interpolation
- `scripts/plotting.py` — heatmaps, red on x-axis and green on y-axis throughout
  (axis labels/ticks only -- the underlying grid array and pixel data are
  plotted as-is, unchanged):
  - `plot_run`/`plot_all_runs`/`plot_mean_run` — single subject
  - `plot_mean_across_subjects`/`plot_subjects_side_by_side`/`plot_group_all_methods` —
    across subjects, filtered by `group`/`subgroup` or an explicit `sub_ids`
    list; `plot_group_all_methods` shows one group's raw + percent/db/zscore
    maps side by side, each independently color-scaled (different numeric
    scales, not comparable on one shared axis)
  - `plot_groups_side_by_side` — one panel per named category (mixing group
    and/or subgroup filters), titled with each category's sample size, e.g.
    `[{"label": "PD", "group": "PD"}, {"label": "protan", "subgroup": "protan"}]`
  - `plot_interpolated_grid(grid, (n_red, n_green), ...)` — heatmap of any
    already-computed grid resized via `interpolate_grid`, same orientation
    convention as every other function here (no data transpose, red on x /
    green on y), generalized to an arbitrary, including rectangular, resolution
  - every function takes an optional `normalize={scope, trials, method}` dict
    (raw if omitted) plus `clim=(vmin, vmax)` and `cmap` overrides; multi-panel
    functions share one auto-computed color scale across all their panels
    unless `clim` is given, and wrap to at most 5 columns per row
    (`plot_subjects_side_by_side`, `plot_groups_side_by_side`)
  - raw values use a sequential blue colormap (magnitude); normalized values use
    a diverging blue/red colormap centered on zero (signed), per the dataviz
    skill's default palette

## Scripts

- `scripts/loader.py` — `load_ssvep(path)` reads one `.mat` file into a plain
  dict; `to_rows(d, filename)` converts it to `(metadata_row, runmap_rows, baseline_rows)`
- `scripts/build_derived.py` — full from-scratch rebuild of `files/` from every
  raw `.mat` file. Always regenerates `metadata.csv` from the raw files, so it
  **will wipe any hand-edit made directly to metadata.csv**. Use only for an
  initial or intentional full reset.
- `scripts/update_derived.py` — day-to-day incremental update: for each raw
  `.mat` file, adds new subject-sessions directly; for a subject-session
  already present, asks `[y/N]` whether to overwrite its `runmap.csv`/
  `baselines.csv` rows with the current raw data (`metadata.csv`'s
  group/subgroup is never touched by this, even on overwrite). Run after
  adding a new `.mat` file to the raw data folder:
  `uv run python scripts/update_derived.py`

## Notebooks

- `notebooks/01_explore.ipynb` — load and look at `MET000.mat`
- `notebooks/02_plots.ipynb` — raw and baseline-normalized heatmaps (single run,
  all runs, mean across runs, ragged 3-run `MET037`), color-limit/colormap
  overrides, and cross-subject aggregation (grand mean, group mean, subjects
  side by side)
- `notebooks/03_group_comparisons.ipynb` — `PD`/`HC`(=`CTR`)/`CVD`/`protan`/`deutan`,
  each with all normalization methods and an interpolated 100x100 view, plus
  `PD`/`HC`/`protan`/`deutan` side by side with sample sizes
