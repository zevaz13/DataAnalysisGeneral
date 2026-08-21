# ssvepBeh scripts and notebooks: reference

Everything lives in `ssvepBeh/scripts/`. Notebooks (`ssvepBeh/notebooks/`)
call these directly. See `ssvepBeh/README.md` for the data dictionary,
the orientation-bug fix (critical -- read before touching this code), and
the cross-project import gotcha between `overlap.py` and `plotting.py`.

## `overlap.py` -- behavioral/EEG spatial overlap

Depends only on `ssveps/scripts/analysis.py` (for grid access) -- every
function takes already-loaded DataFrames (`beh_df`, `runmap_df`,
`baselines_df`, `metadata_df`), the caller's job, same convention as
`ssveps/scripts/analysis.py` itself.

- **`DEFAULT_RED`, `DEFAULT_GREEN`** -- the canonical 10-value grid axes
  (same values as `ssveps/`'s grid).
- **`closest_grid_indices(points, *, red=DEFAULT_RED, green=DEFAULT_GREEN) -> ndarray[N, 2]`**
  Nearest `(red_idx, green_idx)` for each `(red, green)` point. Refactored
  from the template, dropping its `outMat`/MATLAB-orientation transpose
  (see README's orientation-bug section).
- **`behavioral_density_map(beh_df, sub_ids, *, red=DEFAULT_RED, green=DEFAULT_GREEN) -> ndarray[10, 10]`**
  Click counts per grid cell, pooled across every session/click of every
  subject in `sub_ids` -- `[red_idx, green_idx]`. Pass a single-element list
  for one participant, or a whole group's IDs to pool.
- **`weighted_overlap_test(B, E, *, n_perm=5000, seed=None) -> dict`**
  Toroidal-shift permutation test: `obs_stat = sum(E * B/B.sum())`,
  `p_value = P(null_stat <= obs_stat)` under `n_perm` random 2D circular
  shifts of `B`. Returns `{p_value, obs_stat, null_stats}`. `B`/`E` must be
  the same shape and orientation. Seeded (`np.random.default_rng`), unlike
  the template's unseeded `np.random.randint`.
- **`subject_overlap(beh_df, runmap_df, baselines_df, sub_id, session, *, normalize=analysis.DEFAULT_NORMALIZE, n_perm=5000, seed=None) -> dict`**
  One participant: `B` from their own clicks, `E` from
  `analysis.mean_grid`. `normalize` is `analysis.mean_grid`'s own
  scope/trials/method dict (or `None` for raw) -- exposed as a parameter,
  not fixed, since the best normalization for this specific comparison is
  still an open question.
- **`group_overlap(beh_df, runmap_df, baselines_df, metadata_df, session, *, group=None, subgroup=None, sub_ids=None, normalize=analysis.DEFAULT_NORMALIZE, n_perm=5000, seed=None) -> dict`**
  A group: every matching subject's clicks pooled into one `B`, their EEG
  grids averaged into one `E` (`analysis.mean_grid_across_subjects`) -- one
  test per group, not one per subject. `sub_ids` overrides `group`/
  `subgroup` for an arbitrary hand-picked set (same convention as
  `beh`/`ssveps`). Adds `n_subjects` to the returned dict.
- **`centroid_distance(beh_df, runmap_df, baselines_df, sub_id, session, *, normalize=analysis.DEFAULT_NORMALIZE) -> dict`**
  A second, simpler metric: Euclidean distance between a participant's
  behavioral centroid (mean red/green across every click) and their EEG
  trough location (`analysis.trough_location`'s argmin). Returns
  `{beh_red, beh_green, eeg_red, eeg_green, distance}`.
- **`click_value_test(B, E, *, n_perm=5000, seed=None) -> dict`**
  A second, differently-constructed spatial test: is the EEG value *at*
  cells actually clicked lower than a null of the same number of clicks
  landing on uniformly random cells (no toroidal shift -- click position
  structure is discarded entirely)? Returns `{p_value, obs_mean,
  null_means}`, `obs_mean = sum(E*B)/B.sum()`. Deliberately a different null
  model from `weighted_overlap_test`, so their agreement is corroborating
  evidence, not the same test twice.
- **`subject_click_value_test(...)` / `group_click_value_test(...)`**
  `click_value_test` versions of `subject_overlap`/`group_overlap` -- same
  signatures, same `B`/`E` construction (`_subject_grids`/`_group_grids`,
  shared internally with the `weighted_overlap_test` wrappers), different
  test.

Both permutation tests use the `(1 + count) / (1 + n_perm)` p-value
correction -- `docs/ssvep_summary.md` finding 2.7 flagged this as still
missing in `ssveps/scripts/permutation.py` itself; a permutation p-value
can never legitimately be exactly 0 (the observed arrangement is itself one
of the `n_perm + 1` possible arrangements under the null).

## `correlation.py` -- individual-differences convergent validity

Complements `overlap.py`'s spatial tests with a different question: not
"do clicks land where EEG is low" but "does a subject's EEG-derived
severity track their behavioral severity, relative to other subjects." EEG
features come from `ssveps/files/subject_troughs.csv` (read directly, the
same reuse-not-rebuild convention `beh/`/`standardizedScores/FM100/` use for
`ssveps/files/metadata.csv`), not recomputed -- `ramp_slope_red`/
`ramp_slope_green`/`ramp_intercept` are always defined (ssveps' M9: its most
reliable outcomes; `ramp_intercept` correlates r=-0.93 with M8's `gain`, so
it stands in for `gain` without that pipeline's CTR-template dependency),
unlike `fitted_red`/`green`/`depth`, NaN for roughly half of CVD subjects.

- **`DEFAULT_BEH_FEATURES`** = `["beh_red", "beh_green", "orientation_deg", "along_var", "perp_var"]`,
  **`DEFAULT_EEG_FEATURES`** = `["eeg_red", "eeg_green", "ramp_slope_red", "ramp_slope_green", "ramp_intercept"]`
- **`subject_features_table(beh_df, session, *, subject_troughs_path=SUBJECT_TROUGHS_PATH) -> DataFrame`**
  One row per subject present in both `beh_df` and the EEG trough table at
  `session`: `sub_id, group, subgroup` plus every `DEFAULT_BEH_FEATURES`/
  `DEFAULT_EEG_FEATURES` column. Behavioral features come from that
  subject's pooled clicks across every session (beh has no session-level
  structure that corresponds to the EEG's) via `beh/scripts/features.py`'s
  `subject_shape_features`, plus an inline centroid mean.
- **`feature_correlations(table, *, beh_features=DEFAULT_BEH_FEATURES, eeg_features=DEFAULT_EEG_FEATURES, group=None, subgroup=None, method='spearman') -> DataFrame`**
  `pingouin.corr` between every `beh_features` x `eeg_features` pair in
  `table`, optionally filtered to one group/subgroup first. Returns a tidy
  long table: `beh_feature, eeg_feature, r, p_value, n, group, subgroup`
  (`'all'` where unfiltered). `method='spearman'` default (robust to the
  small, possibly-nonlinear per-group samples here, same reasoning as M2's
  Mann-Whitney choice); pass `method='pearson'` for a linear-only check.
  **Not corrected for multiple comparisons** -- with 25 pairs in the default
  feature sets, treat any single result as exploratory unless corrected
  first (see `01_explore.ipynb`'s "Is this analysis enough?" section).

## `plotting.py` -- overlap visualization

- **`plot_overlap(beh_df, eeg_grid, sub_ids, *, red=DEFAULT_RED, green=DEFAULT_GREEN, title=None) -> Figure`**
  Two heatmap panels side by side: `eeg_grid` (e.g. from
  `analysis.mean_grid`/`mean_grid_across_subjects`) and the behavioral
  density map for the same `sub_ids` (`behavioral_density_map`). Red on x,
  green on y in both panels (transposed internally for `imshow`, since
  grids here are `[red_idx, green_idx]` but `imshow` wants
  `[row, col] = [y, x]`).

## Notebooks

- **`01_explore.ipynb`** -- M1: one participant's EEG-vs-behavioral overlap
  (`plot_overlap`, `subject_overlap`); group overlap for all five
  categories on both `weighted_overlap_test` and `click_value_test` (every
  group significant on both); EEG-vs-behavioral-density heatmaps for all
  five groups (not just HC); a centroid-distance table by group
  (`centroid_distance`); the individual-differences correlation analysis
  (`correlation.py`), pooled and per-group/subtype; a critical "is this
  analysis enough" assessment; suggested further methods not built this
  pass (cross-session reliability, multiple-comparisons correction).
  *Edit:* `session` (top cell), `categories` (top cell) to look at
  different group pairs/sessions.
