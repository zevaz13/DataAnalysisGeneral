## Documents

- `ssvepBeh/README.md` -- data dictionary, the orientation-bug fix (read
  before touching this code), and the cross-project import gotcha.
- `docs/ssvepbeh_api_reference.md` -- every function's signature.
- `docs/experiment_summary.md` -- experimental context (stimulus, the three
  data modalities, the metamer construct, the researcher's priorities).

## Decisions made while implementing M1

- **Scope: behavioral-vs-EEG only.** `docs/ExperimentalContext` calls the
  FM100-vs-behavioral and FM100-vs-EEG relationships "the more pressing
  issue," but per your call M1 stays scoped to what `ssvepBeh/`'s template
  code and this plan file actually cover (behavioral vs. EEG) -- FM100
  cross-modality comparisons are a separate, not-yet-started milestone.
- **Orientation bug found and fixed (not just avoided).** The template's
  `closest_grid_indices` returns `outMat = subs.T` ("MATLAB orientation"),
  which is `[green_idx, red_idx]` -- the same axis-swap bug `ssveps/`
  already found and fixed once (`docs/ssvep_summary.md` finding 2.1).
  Verified empirically on real data before trusting either orientation:
  MET001's behavioral centroid's nearest grid cell is
  `(red_idx=5, green_idx=4)`; the untransposed `idx`/`subs` peaks there
  correctly, `outMat` peaks at `(4, 5)` -- swapped. `overlap.py` uses the
  untransposed indices only, pinned by a regression test.
- **EEG grid normalization is a parameter, not fixed** (`subject_overlap`/
  `group_overlap`'s `normalize=`), defaulting to `ssveps/`'s own
  `DEFAULT_NORMALIZE` -- which normalization is most appropriate for this
  specific cross-modality comparison is still an open question.
- **Group-level = pool clicks + mean grid, one test per group** (not one
  test per subject then aggregated) -- matches how `beh/`'s and `ssveps/`'s
  own "group" plots already pool.
- **Seeded RNG.** The template's `permWeighted2Dshifts` used unseeded
  `np.random.randint`; `weighted_overlap_test` uses
  `np.random.default_rng(seed)`, matching every other permutation/bootstrap
  function in this repo (`ssveps/scripts/permutation.py`, `variance.py`).

## M1
- [x] read /docs/ExperimentalContext.txt -- see `docs/experiment_summary.md`
  for the write-up.
- [x] Implement the code in ssvepBeh/template code
  (`ssvepBeh/scripts/overlap.py`, `plotting.py`).
- [x] Suggest different ways of testing the relation between the ssvep grid
  data and the behavioral results -- implemented two:
  `weighted_overlap_test` (the template's method, refactored/fixed/seeded)
  and `centroid_distance` (behavioral centroid vs. EEG trough location, a
  simpler complementary metric). Three more suggested but not built this
  pass, documented in `01_explore.ipynb`'s closing section: an orientation
  correlation against `beh/`'s M2 PCA feature, a simpler click-value
  permutation test, and a cross-session reliability check.
- [x] produce plots and tables with results for each participant, each
  group, each subgroup -- `ssvepBeh/notebooks/01_explore.ipynb`.

**Every group's behavioral clicks concentrate where the EEG response is
low, significantly more than chance (p<0.05 for HC, PD, CVD, protan, and
deutan alike)** -- consistent with the metamer hypothesis holding even in
HC, not just as a CVD-specific signal, directly relevant to the researcher's
question of whether subtle color-vision trends are visible in nominally
healthy participants too. Separately, **CVD's behavioral-centroid-to-
EEG-trough distance (mean ~789) is roughly double HC's (~422) and PD's
(~406)** -- consistent with CVD participants' perceived color match
diverging more from their EEG's minimal-response point, plausibly linked to
`ssveps/`'s M6 finding that CVD trough fits are more likely to peg at the
sampled range boundary.

## Next milestones

FM100-vs-behavioral and FM100-vs-EEG (the researcher's stated higher
priority per `docs/ExperimentalContext`) -- to be scoped together.
