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

## `plotting.py` -- overlap visualization

- **`plot_overlap(beh_df, eeg_grid, sub_ids, *, red=DEFAULT_RED, green=DEFAULT_GREEN, title=None) -> Figure`**
  Two heatmap panels side by side: `eeg_grid` (e.g. from
  `analysis.mean_grid`/`mean_grid_across_subjects`) and the behavioral
  density map for the same `sub_ids` (`behavioral_density_map`). Red on x,
  green on y in both panels (transposed internally for `imshow`, since
  grids here are `[red_idx, green_idx]` but `imshow` wants
  `[row, col] = [y, x]`).

## Notebooks

- **`01_explore.ipynb`** -- M1: one participant's EEG-vs-behavioral
  overlap (`plot_overlap`, `subject_overlap`); group overlap for
  HC/PD/CVD/protan/deutan (`group_overlap`, every group p<0.05); a
  centroid-distance table by group (`centroid_distance`); suggested further
  methods (not built in this pass) for testing the beh-EEG relationship
  differently. *Edit:* `session` (top cell), `categories` (group-overlap
  section) to look at different group pairs/sessions.
