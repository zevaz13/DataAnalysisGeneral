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

- `scripts/overlap.py` -- `behavioral_density_map`, `weighted_overlap_test`
  (seeded, refactored from `templateCode/grid_mapping.py`'s
  `permWeighted2Dshifts`), `subject_overlap`/`group_overlap` (one-call
  wrappers), and `centroid_distance` (a second, simpler metric: behavioral
  centroid vs. EEG trough location).
- `scripts/plotting.py` -- `plot_overlap`, EEG heatmap + behavioral density
  map side by side, for one participant or a pooled group/list.

## Tests

`uv run pytest ssvepBeh/tests -q`. Includes a regression test pinning the
orientation fix against the original template's output on real data, and a
`obs_stat` formula check against the template's math.

## Notebooks

- `01_explore.ipynb` -- M1: one participant's EEG-vs-behavioral overlap;
  group overlap for HC/PD/CVD/protan/deutan (every group significant,
  p<0.05, including HC); centroid-distance table by group (CVD's distance
  is roughly double HC's/PD's); suggested further methods not built in this
  pass (orientation correlation with `beh/`'s M2 PCA feature, a simpler
  click-value permutation test, cross-session reliability).
