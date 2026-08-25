## Documents

- `ssvepBeh/README.md` -- data dictionary, the orientation-bug fix, the
  cross-project import gotcha, and the rest of the implementation decisions
  (Hotelling/permutation seeding, `+1` p-value correction, EEG feature reuse).
  **Read this first.**
- `docs/ssvepbeh_api_reference.md` -- every function's signature.
- `docs/experiment_summary.md` -- experimental context (stimulus, the three
  data modalities, the metamer construct, the researcher's priorities).
- `docs/findings.md` section 4 -- results narrative and interpretation.
- `docs/ssvepbeh_reliability_gaps.md` -- the correlation reliability gap and
  the concrete next steps out of it.

## M1. Behavioral vs. EEG

- [x] Implement the template code (`ssvepBeh/scripts/overlap.py`,
  `plotting.py`), fixing the inherited orientation bug along the way.
- [x] Three independently-constructed tests: `weighted_overlap_test`
  (toroidal-shift null), `click_value_test` (random-cell null), and
  `correlation.py`'s individual-differences convergent-validity analysis,
  plus `centroid_distance` as a complementary metric.
- [x] Plots and tables per participant, group, and subgroup
  (`ssvepBeh/notebooks/01_explore.ipynb`).

**Spatial overlap: solid.** Every group's behavioral clicks concentrate
where the EEG response is low, significantly more than chance, on two
independent null models that agree completely (p<0.05 for HC, PD, CVD,
protan, deutan). **Individual-differences correlation: present but partial**
-- see the M1-continued closure below. Full numbers: `docs/findings.md`
section 4.

## M1, continued: closing the two gaps

- [x] Multiple-comparisons correction (`correlation.correct_multiple_comparisons`)
  -- **nothing survives**, pooled or in any group/subtype, under Holm or FDR.
- [x] Cross-session reliability (`ssvepBeh/scripts/session_reliability.py`,
  `02_reliability.ipynb`) -- **spatial overlap is reliable**; the correlation
  analysis is not, and protan/deutan/CVD-combined can't be assessed at
  today's paired-subject counts.
- [x] Root-cause and next-steps document for the non-significant part --
  `docs/ssvepbeh_reliability_gaps.md`.

**Revised, final verdict for M1:** spatial overlap between behavioral clicks
and EEG response is solid and citable as-is. Individual-differences
correlation is a documented, honestly-reported negative result with a
concrete path forward, not silently dropped or overstated.

## Next milestones

FM100-vs-behavioral and FM100-vs-EEG (the researcher's stated higher
priority per `docs/ExperimentalContext`) -- to be scoped together. Worth
carrying `docs/ssvepbeh_reliability_gaps.md`'s lesson forward: check
paired/per-subtype sample sizes before designing that analysis's
statistical approach, not after.
