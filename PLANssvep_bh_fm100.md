Cross-modality analysis connecting the FM100 standardized score to the
behavioral (manual match) data, and later to the EEG (SSVEP grid) data --
the piece `docs/ExperimentalContext` flagged as the more pressing priority,
after `ssvepBeh/` established that behavioral-vs-EEG spatial overlap is
solid but individual-differences correlation needs a smarter approach (see
`docs/ssvepbeh_reliability_gaps.md`).

**The core hypothesis this project tests:** FM100 scores may encode a
continuous "severity of color perception deficiency" spectrum that the
categorical protan/deutan/HC/PD labels currently mask -- and that spectrum
may correlate with behavioral and/or EEG features in ways a purely
categorical group comparison can't see.

New code and notebooks live under `/ssvep_beh_fm100`, matching the
per-project convention already established (`beh/`, `ssveps/`,
`standardizedScores/FM100/`, `ssvepBeh/`).

## Context: why this is structured the way it is

`ssvepBeh/`'s correlation work (`docs/ssvepbeh_reliability_gaps.md`) looked
promising uncorrected, then failed both a multiple-comparisons correction
and a cross-session reliability check. Two root causes, both directly
relevant here:

- **Multidimensionality** -- 25 independent univariate tests on
  internally-correlated features spends a lot of statistical budget without
  using the joint covariance structure a real relationship would show up in.
- **Small n, especially per subtype and per paired-session subset.**

Subject overlap is *not* the bottleneck for FM100, unlike EEG session
pairing was: **all 47 behavioral subjects have FM100 data, and all 43 EEG
subjects have FM100 data too** (protan n=8, deutan n=7 -- the full expected
sample), checked directly against the raw data before writing this plan.
The design below is built to avoid repeating the multidimensionality
mistake regardless.

## Decisions

- **Severity vs. type framing, not one blended score.** FM100's own
  features already split naturally: `TES`/`VKS_MajRad`/`VKS_MinRad` measure
  overall error *magnitude* (severity); `VKS_Angle` measures the confusion
  ellipse's *direction* (type/axis) -- structurally parallel to `beh/`'s M2
  split between `along_var`/`perp_var` (spread/consistency) and
  `orientation_deg` (which perfectly separates protan from deutan). Two
  parallel questions, not one.
- **One multivariate test for severity, not many univariate ones.** CCA
  (Canonical Correlation Analysis) between a lean, deliberately
  non-redundant FM100 severity bundle (`{TES, VKS_MajRad, VKS_MinRad}`) and
  a behavioral severity bundle (`{along_var, perp_var}`), with a seeded
  permutation test for significance (shuffle subject correspondence, refit,
  same pattern every other permutation test in this repo uses). One
  pre-specified hypothesis, structurally immune to the multiple-comparisons
  problem that sank `ssvepBeh`'s correlation work. TES and PES_RG/PES_BY
  are deliberately excluded together (PES splits TES by axis, so including
  both invites collinearity for no informational gain at this n).
- **New dependency: `scikit-learn`, for CCA.** Consistent with this
  project's established "prefer a package over hand-rolling" precedent (the
  same call made for Hotelling T² in `beh/`).
- **One focused, pre-registered test for type/axis**, not fished from a
  matrix: `VKS_Angle` vs. `orientation_deg`, via `pingouin.circ_axial`
  (transforms 180°-periodic "axial" data -- both these angles describe a
  *line*, not a direction, exactly like `orientation_deg`'s own existing
  fold-to-[0,180) convention) followed by `pingouin.circ_corrcc`
  (circular-circular correlation). Both functions already exist in
  `pingouin` (already a dependency) -- no naive Pearson/Spearman on raw
  degrees, which would be wrong for a periodic quantity.
- **A univariate feature-correlation table as context, not a claim** --
  same `feature_correlations`-style pattern `ssvepBeh/scripts/correlation.py`
  already has, computed and shown, but explicitly labeled descriptive/
  exploratory. Never used to claim significance, which sidesteps needing to
  correct it.
- **FM100's own cross-session reliability, checked first.** ICC(A,1) (same
  method and `pingouin` call `ssveps/`'s own M5 uses) for `TES`,
  `VKS_Angle`, `VKS_MajRad`, `VKS_MinRad` across each subject's repeat FM100
  sessions (up to 3) -- before leaning on any of them as a severity/type
  measure. Directly prevents repeating `ssvepBeh`'s mistake of finding out a
  measure wasn't reliable only after building on top of it.
- **Feature loading reuses existing pipelines, not rebuilt.**
  `standardizedScores/FM100/scripts/scores.py` (`build_scores`) and
  `beh/scripts/features.py`/`comparisons.py` directly -- same
  reuse-not-rebuild convention every project here already follows for
  `ssveps/files/metadata.csv`/`subject_troughs.csv`.
- **Scope: FM100-vs-behavioral now, FM100-vs-EEG deferred to M2.**
  Behavioral is the higher-signal, more direct measure per everything found
  so far (M1 `beh/` Hotelling T², M2 `orientation_deg`'s perfect protan/
  deutan split) -- validate the severity/type approach there first, then
  extend the same structure to the noisier EEG data once it's proven out.

## Structure

```
ssvep_beh_fm100/
  scripts/
    fm100_features.py   -- FM100 reliability (ICC) + per-subject severity/type feature table
    severity.py          -- CCA + permutation significance test
    type_axis.py          -- circ_axial + circ_corrcc test
    plotting.py            -- canonical-variate scatter, circular scatter, ICC table/plot
  tests/test_ssvep_beh_fm100.py
  notebooks/
    01_fm100_reliability.ipynb
    02_fm100_vs_behavioral.ipynb
  README.md
docs/ssvep_beh_fm100_api_reference.md
```

## M1: FM100 reliability, then FM100 vs. behavioral

- [ ] Add `scikit-learn` to `pyproject.toml`.
- [ ] `fm100_features.py`: per-subject, per-session FM100 severity/type
  features (`TES`, `VKS_Angle`, `VKS_MajRad`, `VKS_MinRad`), reusing
  `standardizedScores/FM100/scripts/scores.py`. Also a per-subject *pooled*
  version (mean across that subject's available sessions), for merging with
  `beh/`'s own already-pooled-across-sessions convention.
- [ ] FM100 cross-session reliability: ICC(A,1) for each of the four
  features above, `01_fm100_reliability.ipynb`. Decide, from the result,
  whether any feature needs dropping or caveating before M1's later steps
  lean on it.
- [ ] Merge FM100 (pooled) with `beh/`'s M2 shape features
  (`orientation_deg`, `along_var`, `perp_var`) and centroid, one row per
  subject present in both datasets (expected: 47, per the overlap check
  above).
- [ ] `severity.py`: CCA between `{TES, VKS_MajRad, VKS_MinRad}` and
  `{along_var, perp_var}`, seeded permutation test for the top canonical
  correlation's significance.
- [ ] `type_axis.py`: `circ_axial` + `circ_corrcc` between `VKS_Angle` and
  `orientation_deg`.
- [ ] Univariate feature-correlation table (context only, not a
  significance claim) between the full FM100 and behavioral feature sets.
- [ ] `02_fm100_vs_behavioral.ipynb`: reliability results, the merged
  table, both primary tests (severity CCA, type circular correlation) with
  plots, the context table, pooled and per-group/subtype where n allows.
- [ ] `README.md` + `docs/ssvep_beh_fm100_api_reference.md`, matching every
  other project's documentation convention here.
- [ ] Update `docs/findings.md` once M1 has real results.

## M2 (later): extend to EEG

Same severity/type structure, against `ssveps/files/subject_troughs.csv`'s
`ramp_slope_red`/`ramp_intercept` (severity) and a ramp-direction analog
(type) -- once M1's approach is validated on the higher-signal behavioral
data. To be scoped in detail once M1 is done.

## Next milestones

To be defined together.
