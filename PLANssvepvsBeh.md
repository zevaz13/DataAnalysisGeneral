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

## M2. Clicks-on-grid plots, permutation seed stability, step-by-step explainer

- [x] **`03_clicks_on_grid.ipynb`** -- new `plotting.plot_grid_with_clicks`:
  the EEG grid as a heatmap with actual click points scattered on top, one
  combined view. Individual participants (mean grid + their own clicks),
  repeated with behavioral outliers removed (`beh/`'s M4
  `subject_outliers`/`group_outliers`, cross-project reuse), then groups/
  subgroups (mean group grid vs. every member's pooled clicks), same
  with/without-outliers pair. x/y limits capped to `[0, 3200]`/`[0, 2000]`
  throughout. **7 subjects run past green=2000**: MET030, MET032, MET033,
  MET034, MET040, MET041, MET043 (1-7 such clicks each, up to green=2380).
- [x] **`04_permutation_stability.ipynb`** -- `overlap.group_overlap` at
  200 seeds each for HC, PD, protan, deutan. **Every group stays
  significant at every single seed** (`fraction_p<0.05` = 1.0 for all
  four) -- extends `docs/ssvepbeh_reliability_gaps.md`'s cross-session
  stability finding with a second, independent kind: robust to the
  permutation RNG too, for every group without exception. One checked-and-
  confirmed-not-a-bug curiosity: HC and deutan's p-values matched exactly
  at every seed tested (different subjects/grids/statistics, but the same
  null-crossing count throughout) -- PD vs. protan doesn't show this, so
  it's specific to this pair's actual data, not a systematic issue; noted
  in the notebook, not treated as a finding to build on.
- [x] **`05_toroidal_shift_explained.ipynb`** -- step-by-step from-scratch
  walkthrough (synthetic 5x5 grid, then MET001), matching `ssveps/`'s own
  "Understanding..." notebook style.

## Next milestones

FM100-vs-behavioral and FM100-vs-EEG (the researcher's stated higher
priority per `docs/ExperimentalContext`) turned out to already be
implemented, in `ssvep_beh_fm100/` (`PLANssvep_bh_fm100.md` M1-M3) -- see
`docs/findings.md` section 5. This plan's own next milestone is open, to be
defined together.
