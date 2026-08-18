## SSVEP project
data located in '/home/sebas/data/ssveps'. These are matlab files. Each file has information about SSVEPs for a grid experiment. METxxx is the unique subject id. the letter a, b, or c tells information about the session number (sessions 1, 2 or 3 respectively).
### Milestone 1 (M1)
- [x] Scaffold `ssveps/` (README.md, notebooks/, scripts/)
- [x] `scripts/loader.py` — `load_ssvep(path)`, plain `scipy.io.loadmat` wrapper (files are non-v7.3, no HDF5 needed)
- [x] `notebooks/01_explore.ipynb` — loads and inspects `MET000.mat`
  - `SubID`, `session`, `group`, `subgroup`, `baseDIM`, `mapDIM` — labels/scalars
  - `redArray`, `greenArray` — 10-level grid axes (0-3200 red, 0-2000 green)
  - `runMap` — `(10, 10, 4)` = red x green x run
  - `baselines` — `(4, 4)` per `baseDIM` (`TR_RUN`)
- [x] `ssveps/files/metadata.csv` — one row per file (62): `filename, sub_id, session, group, subgroup`. Confirmed group/subgroup/SubID are stable per subject across sessions (0 conflicts across 43 subjects)
- [x] `ssveps/files/grid.json` — shared `redArray`, `greenArray`, `baseDIM`, `mapDIM`. Confirmed byte-identical across all 62 files, so one copy suffices
- [x] Decided: extract into tidy long-format CSVs rather than keep raw structs (user choice, over per-file .npz or raw-.mat-only)
  - `ssveps/files/runmap.csv` (24,200 rows) — `sub_id, session, run, red_idx, green_idx, value`
  - `ssveps/files/baselines.csv` (968 rows) — `sub_id, session, run, trial, value`
  - handles the ragged run count naturally: `MET037-040` (group `PD`) have only 3 runs instead of 4, so they just contribute fewer rows
  - `ssveps/scripts/build_derived.py` builds all of the above from the raw `.mat` files (reproducible, rerun anytime)
- [x] Confirmed semantics before building: baseline trials 1-2 = pre-grid, 3-4 = post-grid; baseVal for percent/db = mean of selected trials (consistent with z-score's mean/std); session-level normalization pools baseline trials across all runs of that session
- [x] `ssveps/scripts/analysis.py` — data access + normalization on the tidy CSVs
  - `raw_grid(runmap_df, sub_id, session, run)`, `mean_raw_grid(runmap_df, sub_id, session)` — 10x10 grids
  - `baseline_values(baselines_df, sub_id, session, scope='run'|'session', run=, trials='all'|'first2'|'last2')`
  - `normalize_grid(raw, baseline_vals, method='percent'|'db'|'zscore')` and `normalized_grid(...)` combining both steps
- [x] `ssveps/scripts/plotting.py` — `plot_run`, `plot_all_runs`, `plot_mean_run`, each taking an optional `normalize={scope, trials, method}` dict, so raw and every normalization strategy reuse the same three plot functions (satisfies "repeat all the plots above with different normalization strategies" without duplicating them)
  - raw = sequential blue colormap (magnitude); normalized = diverging blue/red colormap centered on zero (signed) — dataviz skill's default palette
  - `plot_all_runs`/mean read the run count from the data, so the ragged 3-run subjects (`MET037-040`) plot correctly
- [x] `ssveps/notebooks/02_plots.ipynb` — demonstrates all of the above: raw single run/all runs/mean for `MET000`, the ragged `MET037` case, and normalized examples across scope/trials/method combinations
- [x] Investigated before fixing: `metadata.csv`'s newer mtime + `MET043-046` showing `group=CVD, subgroup=deutan/protan` there while their raw `.mat` files still say `UNKNOWN/NA` confirmed this was a direct hand-edit to `metadata.csv`, already agreeing with what was added -- runmap.csv/baselines.csv (built after the raw files' last real change) were already consistent too. Nothing needed correcting; the real risk was a future rebuild silently wiping the edit, addressed below.
- [x] `scripts/update_derived.py` — incremental pipeline (item 28): new subject-session -> added directly; existing -> `[y/N]` prompt, and if overwritten only `runmap.csv`/`baselines.csv` are refreshed -- `metadata.csv`'s group/subgroup is set once at first creation and never touched afterward (your choice: preserve hand-set metadata permanently over always-refresh-from-raw). Verified with 3 isolated tests: (1) full no-op run against the real data with every prompt answered "no" produces byte-identical output (also caught and fixed two real bugs this surfaced: pandas silently turning the literal string "NA" into blank via default NA-parsing, and pandas' to_csv not round-tripping float64 precision by default -- both fixed), (2) a brand-new subject gets added cleanly, (3) overwriting an existing subject with changed raw data refreshes runmap.csv but leaves metadata.csv's group untouched
- [x] `scripts/build_derived.py` kept as the full-from-scratch rebuild (will still wipe hand-edits -- documented as intentional-reset-only); both scripts now share row-extraction logic via `loader.to_rows()`
- [x] Fixed `plot_run`/`plot_all_runs`/`plot_mean_run`: red is now the x-axis, green the y-axis (was swapped); all three take optional `clim=(vmin, vmax)` and `cmap` overrides; `plot_all_runs` now auto-computes and shares one color scale across all its panels by default (previously each run panel scaled independently -- the bug you found)
- [x] New cross-subject aggregate plots in `scripts/analysis.py` (`mean_grid`, `subjects_in_group`, `mean_grid_across_subjects`) and `scripts/plotting.py`:
  - `plot_mean_across_subjects` — grand mean (no filter), or filtered by `group`/`subgroup`, or an explicit `sub_ids` list
  - `plot_subjects_side_by_side` — one panel per subject (each subject's own mean-across-runs grid), same filtering options, shared color scale by default
  - both take `normalize`/`clim`/`cmap` like the single-subject plots, and operate on one fixed `session` shared across the whole group/list (your choice, so 2-session subjects aren't double-counted)
- [x] `ssveps/notebooks/02_plots.ipynb` updated: axis-fixed raw/normalized plots, a clim/cmap override demo, grand mean, CVD group mean, CVD side-by-side (confirms `MET043-046` now included correctly), and an explicit-list side-by-side example
### Next
- [ ] Decide what to explore/analyze across subjects and sessions (e.g. group/subgroup comparisons on the red/green grid response)