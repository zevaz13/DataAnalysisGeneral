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
- **Permutation p-value correction, applied here and not yet in `ssveps/`.**
  `docs/ssvep_summary.md` finding 2.7 flagged `ssveps/scripts/permutation.py`'s
  `p = (null > obs).mean()` (no `+1`) as a real bug -- a permutation p-value
  can never legitimately be exactly 0. Both of this project's permutation
  tests use `p = (1 + count) / (1 + n_perm)` instead, rather than
  propagating a known issue into new code.
- **Two independently-constructed spatial tests, not one.**
  `weighted_overlap_test` (toroidal-shift null) and the newly added
  `click_value_test` (random-cell null, click-position structure discarded
  entirely) ask the same question two different ways, so their agreement
  is corroborating evidence rather than the same computation run twice.
- **EEG per-subject features reuse `ssveps/files/subject_troughs.csv`
  directly** (the persisted, canonical ramp_gaussian table), not recomputed
  -- same reuse-not-rebuild convention as `beh/`'s/`FM100/`'s use of
  `ssveps/files/metadata.csv`. `ramp_slope_red`/`ramp_slope_green`/
  `ramp_intercept` used as the EEG severity features (M9's most reliable,
  always defined) rather than `fitted_*` (NaN for ~half of CVD subjects).

## M1
- [x] read /docs/ExperimentalContext.txt -- see `docs/experiment_summary.md`
  for the write-up.
- [x] Implement the code in ssvepBeh/template code
  (`ssvepBeh/scripts/overlap.py`, `plotting.py`).
- [x] Suggest different ways of testing the relation between the ssvep grid
  data and the behavioral results -- implemented three:
  `weighted_overlap_test` (the template's method, refactored/fixed/seeded),
  `click_value_test` (a second, differently-constructed spatial test), and
  `correlation.py`'s individual-differences convergent-validity analysis
  (does EEG severity track behavioral severity across subjects, not just
  spatial overlap) -- plus `centroid_distance` as a simple complementary
  metric. One more suggested but not built this pass: cross-session
  reliability of the beh-EEG relationship itself.
- [x] produce plots and tables with results for each participant, each
  group, each subgroup -- `ssvepBeh/notebooks/01_explore.ipynb`.
- [x] Make plots showing the steps for HC, PD, CVD, protan and deutan --
  `01_explore.ipynb`'s EEG-vs-behavioral-density heatmap section now covers
  all five, not just HC.
- [x] With the knowledge you have about the data and experiments can you
  provide other ways of testing this relationship between the tests? Is
  this analysis we have now enough? -- see `01_explore.ipynb`'s "Is this
  analysis enough?" section: spatial overlap is well-established (two
  independent nulls agree completely, every group p<0.05); individual-
  differences convergence is present but partial and uncorrected for
  multiple comparisons. Full assessment and next steps below.

**Spatial overlap: every group's behavioral clicks concentrate where the
EEG response is low, significantly more than chance, on two independently-
constructed null models that agree completely** (p<0.05 for HC, PD, CVD,
protan, and deutan on both `weighted_overlap_test` and `click_value_test`)
-- consistent with the metamer hypothesis holding even in HC, not just as a
CVD-specific signal, directly relevant to the researcher's question of
whether subtle color-vision trends are visible in nominally healthy
participants too.

**Individual-differences correlation (justifying the EEG test against
behavior, not just spatial agreement):** pooled across all 43 subjects,
`orientation_deg` (M2's cleanest behavioral subtype signal) correlates with
both `ramp_slope_red` (r=0.35, p=0.020) and `ramp_intercept` (r=-0.37,
p=0.015) -- ssveps' most reliable EEG features. Within deutan alone,
`beh_red` (behavioral centroid) vs. `eeg_green` (EEG trough location) is
r=-0.92 (p=0.003, n=7); PD shows `beh_red` vs. `eeg_red` r=0.88 (p=0.021,
n=6). Protan and CTR's own best pairings don't reach significance at
their n. **None of this is corrected for multiple comparisons (25 pairs
tested)** -- read as exploratory, not confirmatory, until that correction
is applied.

Separately, **CVD's behavioral-centroid-to-EEG-trough distance (mean ~789)
is roughly double HC's (~422) and PD's (~406)** -- consistent with CVD
participants' perceived color match diverging more from their EEG's
minimal-response point, plausibly linked to `ssveps/`'s M6 finding that CVD
trough fits are more likely to peg at the sampled range boundary.

**What would make this fully "safe and sound" before moving on:**
multiple-comparisons correction on the correlation matrix, and (the single
most important remaining gap) cross-session reliability of the beh-EEG
relationship itself -- a real signal today that isn't stable session to
session isn't a usable clinical justification.

## M1, continued: closing the two gaps

- [x] Multiple-comparisons correction
  (`correlation.correct_multiple_comparisons`, Holm/FDR via `statsmodels`)
  -- **nothing survives, pooled or in any group/subtype**, under either
  method. The strongest pooled pair (`orientation_deg` vs.
  `ramp_intercept`, uncorrected p=0.015) corrects to p=0.11 under FDR.
- [x] Cross-session reliability (`ssvepBeh/scripts/session_reliability.py`,
  `ssvepBeh/notebooks/02_reliability.ipynb`) -- **spatial overlap is
  reliable** (near-identical obs/p-values session 1 vs. session 2,
  everywhere testable: pooled n=19, HC n=13, PD n=4 paired subjects).
  **The correlation analysis is not** (r-values shift substantially
  session to session for the same feature pair) -- and protan (n=2),
  deutan (n=0), and CVD-combined (n=2) can't be assessed for reliability
  at all with today's paired-subject counts.
- [x] "If we don't reach significance, leave a document explaining the
  steps we'll take" -- `docs/ssvepbeh_reliability_gaps.md`: confirms your
  own hypothesis (multidimensionality of the 25-pair univariate test, and
  small per-subtype n, especially for reliability specifically) as the
  root cause, and lays out concrete next steps (more repeated-session
  CVD/protan/deutan data; a multivariate joint test -- CCA or a composite
  PC1-based severity score, mirroring `ssveps/`'s own M10 -- instead of 25
  univariate pairs).

**Revised, final verdict for M1:** spatial overlap between behavioral
clicks and EEG response is solid and can be cited as-is -- significant in
every group, on two independent null models, stable across sessions.
Individual-differences correlation is a documented, honestly-reported
negative result with a concrete path forward, not silently dropped or
overstated. `01_explore.ipynb`'s correlation findings should be read
through `02_reliability.ipynb`'s revision, not on their own.

## Next milestones

FM100-vs-behavioral and FM100-vs-EEG (the researcher's stated higher
priority per `docs/ExperimentalContext`) -- to be scoped together. Worth
carrying `docs/ssvepbeh_reliability_gaps.md`'s lesson forward: check
paired/per-subtype sample sizes before designing that analysis's
statistical approach, not after.
