# ssvepBeh (behavioral vs. EEG overlap)

Tests whether a participant's/group's behavioral (manual) click density
spatially concentrates where the EEG (SSVEP grid) response is weakest --
i.e. whether the two independent measures of the "metamer" (see
`docs/experiment_summary.md`) agree on where it is. `PLANssvepvsBeh.md`'s
scope; the standardized-score (FM100) comparisons the researcher flagged as
higher priority are a separate, not-yet-started milestone.

No raw data of its own -- reuses `beh/`'s tidy behavioral table and
`ssveps/`'s tidy CSVs/grid functions directly (see the module docstrings).
Function-by-function reference: `docs/ssvepbeh_api_reference.md`. Plan and
milestone status: `../PLANssvepvsBeh.md`.

## Orientation bug found and fixed

`templateCode/grid_mapping.py`'s `closest_grid_indices` returns a second
value, `outMat = subs.T`, described as matching "MATLAB orientation" --
that's `[green_idx, red_idx]`, the same axis-swap bug `ssveps/` already
found and fixed once (`docs/ssvep_summary.md` finding 2.1). Verified
empirically on real data (MET001): the behavioral centroid's nearest grid
cell is `(red_idx=5, green_idx=4)`; the untransposed `idx`/`subs` peaks
there correctly, `outMat` peaks at `(4, 5)` -- swapped. `scripts/overlap.py`
builds its density map from the untransposed indices, never `outMat`, so
it's genuinely `[red_idx, green_idx]` like every `ssveps/` grid -- pinned by
`tests/test_ssvepbeh.py::test_behavioral_density_map_orientation_matches_template_subs_not_outmat`.

## Cross-project imports: a real gotcha

`overlap.py` needs `ssveps/scripts/analysis.py` for grid access/
normalization/trough location, and adds `ssveps/scripts` to `sys.path` as
an import-time side effect. **`ssveps/scripts` also has its own
`plotting.py`** -- so if anything imports `overlap` before resolving the
bare name `plotting`, `import plotting` will silently resolve to *ssveps'*
`plotting.py` instead of this project's own (they don't error, they just
each have different public functions, so the failure shows up as a
confusing `AttributeError` later, not an import error). Every notebook and
test file here re-asserts `ssvepBeh/scripts` at `sys.path[0]` (and drops any
stale cached `plotting` module) between `import overlap` and
`import plotting` -- see either file's import cell/block for the exact
pattern, and don't reorder those two imports without it. (Beyond this pair,
the usual multi-project `loader`/`plotting` name collision applies too --
see `beh/README.md`'s Tests section.)

## Scripts

- `scripts/overlap.py` -- `behavioral_density_map`; two independently-
  constructed spatial tests, `weighted_overlap_test` (toroidal-shift null,
  seeded, refactored from `templateCode/grid_mapping.py`'s
  `permWeighted2Dshifts`) and `click_value_test` (random-cell null); one-call
  wrappers for both (`subject_overlap`/`group_overlap`,
  `subject_click_value_test`/`group_click_value_test`); and
  `centroid_distance` (a third, simpler metric: behavioral centroid vs. EEG
  trough location). Both permutation tests use the `(1 + count) / (1 + n_perm)`
  p-value correction (see below).
- `scripts/correlation.py` -- individual-differences convergent validity:
  does a subject's EEG-derived severity track their behavioral severity
  (not just spatial overlap)? `subject_features_table` (merges beh centroid
  + M2 PCA shape features with `ssveps/files/subject_troughs.csv`'s
  ramp features) + `feature_correlations` (Spearman, pooled or per-group).
- `scripts/plotting.py` -- `plot_overlap`, EEG heatmap + behavioral density
  map side by side, for one participant or a pooled group/list.

## A permutation p-value can't legitimately be exactly 0

`docs/ssvep_summary.md` finding 2.7 flagged `(null > obs).mean()` (no `+1`
correction) as a real, still-unfixed issue in `ssveps/scripts/permutation.py`
itself. `overlap.py`'s two permutation tests apply the fix here
(`p_value = (1 + count) / (1 + n_perm)`) rather than propagating a known bug
into new code -- worth porting back to `ssveps/` at some point, out of
scope for this project.

## Tests

`uv run pytest ssvepBeh/tests -q`. Includes a regression test pinning the
orientation fix against the original template's output on real data, an
`obs_stat`/`obs_mean` formula check against the template's math for both
spatial tests, and a synthetic-data sanity check for `feature_correlations`.

## Notebooks

- `01_explore.ipynb` -- M1: one participant's EEG-vs-behavioral overlap;
  group overlap for all five categories on both spatial tests (every group
  significant on both, including HC); EEG-vs-behavioral-density heatmaps
  for all five groups; a centroid-distance table by group (CVD's distance
  is roughly double HC's/PD's); the individual-differences correlation
  analysis (pooled: `orientation_deg` vs. `ramp_slope_red`/`ramp_intercept`
  both p<0.02; per-subtype: deutan's `beh_red` vs. `eeg_green` r=-0.92,
  p=0.003); a critical assessment of whether this is enough (spatial
  overlap: yes; individual-differences convergence: present but partial and
  uncorrected); suggested further methods not built this pass (cross-session
  reliability -- the single most important gap, multiple-comparisons
  correction).
