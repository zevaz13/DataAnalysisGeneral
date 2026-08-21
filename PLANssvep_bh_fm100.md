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
- **`severity.py`/`type_axis.py` are written feature-set-agnostic from the
  start** (take any two per-subject feature tables/angle arrays, not
  hardcoded to behavioral data) specifically so M2 reuses the same CCA and
  circular-correlation machinery against EEG features instead of
  duplicating it.

## Structure

```
ssvep_beh_fm100/
  scripts/
    fm100_features.py   -- FM100 reliability (ICC) + per-subject severity/type feature table
    eeg_features.py       -- EEG reliability (ICC) + per-subject severity/type feature table (M2)
    severity.py            -- CCA + permutation significance test (feature-set-agnostic)
    type_axis.py            -- circ_axial + circ_corrcc test (feature-set-agnostic)
    plotting.py              -- canonical-variate scatter, circular scatter, ICC table/plot
  tests/test_ssvep_beh_fm100.py
  notebooks/
    01_fm100_reliability.ipynb
    02_fm100_vs_behavioral.ipynb
    03_eeg_reliability.ipynb        -- M2
    04_fm100_vs_eeg.ipynb            -- M2
  README.md
docs/ssvep_beh_fm100_api_reference.md
```

## M1: FM100 reliability, then FM100 vs. behavioral

- [x] Add `scikit-learn` to `pyproject.toml` -- was already present
  transitively (via `pandas-flavor`) but not declared; `uv add scikit-learn`
  makes it intentional.
- [x] `fm100_features.py`: per-subject, per-session FM100 severity/type
  features (`TES`, `VKS_Angle`, `VKS_MajRad`, `VKS_MinRad`), reusing
  `standardizedScores/FM100/scripts/scores.py`. Also a per-subject *pooled*
  version (mean across that subject's available sessions, `VKS_Angle`
  pooled circularly), for merging with `beh/`'s own already-pooled-across-
  sessions convention.
- [x] FM100 cross-session reliability: ICC(A,1) for the three magnitude
  features, `circ_corrcc` for `VKS_Angle` (periodic -- a linear ICC would
  be wrong for it), `01_fm100_reliability.ipynb`. **Result: `TES`
  (ICC=0.92), `VKS_MinRad` (ICC=0.93), `VKS_MajRad` (ICC=0.84) all
  reliable; `VKS_Angle` is not** (circular r=0.44, p=0.15, n=19 paired) --
  carried forward as an explicit caveat on the type/axis test rather than
  discovered after the fact, the exact mistake `ssvepBeh/` made once
  already.
- [x] Merge FM100 (pooled) with `beh/`'s M2 shape features
  (`orientation_deg`, `along_var`, `perp_var`) and centroid, one row per
  subject present in both datasets -- **47, matching the overlap check
  above exactly.**
- [x] `severity.py`: CCA between `{TES, VKS_MajRad, VKS_MinRad}` and
  `{along_var, perp_var}`, seeded permutation test for the top canonical
  correlation's significance.
- [x] `type_axis.py`: `circ_axial` + `circ_corrcc` between `VKS_Angle` and
  `orientation_deg`.
- [x] Univariate feature-correlation table (context only, not a
  significance claim) between the full FM100 and behavioral feature sets.
- [x] `02_fm100_vs_behavioral.ipynb`: reliability results, the merged
  table, both primary tests (severity CCA, type circular correlation) with
  plots, the context table, pooled and per-group/subtype where n allows.
- [x] `README.md` + `docs/ssvep_beh_fm100_api_reference.md`, matching every
  other project's documentation convention here.
- [x] Update `docs/findings.md` once M1 has real results.

### M1 results

**Severity (CCA, `{TES, VKS_MajRad, VKS_MinRad}` vs. `{along_var,
perp_var}`): strong and significant pooled (r=0.73, p<0.001, n=47), but
does not hold up within any single group** (HC r=0.58 p=0.23, n=21; CVD
r=0.66 p=0.28, n=15; PD r=0.995 p=0.15, n=6; protan/deutan underpowered at
n=8/7). Honest read: likely at least partly a between-group effect (CVD
scores worse on both measures than HC, which alone can inflate a pooled
correlation) rather than a confirmed within-group continuum -- not ruled
out (CTR's own r=0.58 isn't small), just not yet confirmed at this n.

**Type/axis (circular correlation, `VKS_Angle` vs. `orientation_deg`):
significant pooled (r=0.37, p=0.009, n=47) *and significant within CVD
alone*** (r=0.56, p=0.031, n=15) -- unlike severity, this one isn't just a
between-group artifact. The more solid of the two results, though it rides
on `VKS_Angle`'s own weaker cross-session reliability (real signal, noisier
measurement, same situation `ssveps/`'s M9 found for `ramp_slope_red`
relative to `gain`).

**Both results support the core hypothesis** -- FM100 does encode
information correlated with behavioral severity/type beyond the
categorical labels -- with type/axis currently the stronger, more solid
finding of the two.

## M2: FM100 vs. EEG

Same severity/type structure M1 establishes, extended to
`ssveps/files/subject_troughs.csv`'s ramp features -- with one added
insight: `ramp_slope_red` and `ramp_slope_green` together form a 2D vector
in the same "which way does the deficiency point" family as `VKS_Angle` and
`orientation_deg`, not just a severity measure. That reframes the EEG
feature split cleanly:

- **EEG type/axis**: the angle of `(ramp_slope_red, ramp_slope_green)` --
  `atan2(ramp_slope_green, ramp_slope_red)` -- compared against `VKS_Angle`
  the same way M1 compares `VKS_Angle` against `orientation_deg`.
- **EEG severity**: `{ramp_magnitude, ramp_intercept}`, where
  `ramp_magnitude = sqrt(ramp_slope_red^2 + ramp_slope_green^2)` (overall
  steepness, direction-independent) and `ramp_intercept` (baseline gain).
  Deliberately excludes the raw slopes, which now feed the type/axis test
  instead -- avoiding the same severity/type redundancy M1's TES-vs-PES
  exclusion avoids.

Subject overlap is not a bottleneck for the main tests here either: all 43
EEG subjects have FM100 data (checked in "Context" above). It *is* a
bottleneck for checking whether the FM100-EEG relationship itself is
stable across EEG sessions -- `docs/ssvepbeh_reliability_gaps.md`'s numbers
apply unchanged here (pooled n=19 paired, HC n=13, PD n=4, protan n=2, CVD
n=2, **deutan n=0**), so M2 expects, going in, that a per-subtype
reliability check won't be possible -- not a surprise to discover partway
through, this time.

Kept out of scope for M2, deliberately: a three-way joint comparison of
`VKS_Angle`/`orientation_deg`/the EEG ramp-angle together. All three are
sitting right there once M2 is done, and it's a natural, low-effort next
step -- but M2 stays a direct pairwise extension of M1's structure; the
three-way version is a candidate for M3.

- [ ] `eeg_features.py`: per-subject, per-session `ramp_magnitude`
  (derived) and ramp-angle (derived), plus the raw `ramp_slope_red`/
  `ramp_slope_green`/`ramp_intercept`/`ramp_r_squared` columns passed
  through, reusing `ssveps/files/subject_troughs.csv` directly (not
  recomputed). A pooled-across-sessions version isn't needed the way FM100's
  is -- EEG features are already used per-session everywhere else in this
  repo (`ssvepBeh/`, `ssveps/` itself); M2's cross-modality merge uses EEG
  session 1 to match `ssvepBeh/`'s own convention, keeping results
  comparable across projects.
- [ ] EEG reliability for the two *derived* features: ICC(A,1) for
  `ramp_magnitude` and the ramp-angle (circular ICC, or `circ_corrcc`
  between session 1 and session 2 values directly if a circular ICC isn't
  readily available) across paired subjects, `03_eeg_reliability.ipynb`.
  `ramp_slope_red`/`ramp_intercept`'s own reliability is already
  established (`ssveps/`'s M9, ICC 0.85/0.90) -- this only needs to check
  the two new composite quantities.
- [ ] Merge FM100 (pooled, session-averaged as in M1) with EEG (session 1)
  features, one row per subject present in both (expected: 43).
- [ ] `severity.py` (reused, not rewritten): CCA between
  `{TES, VKS_MajRad, VKS_MinRad}` and `{ramp_magnitude, ramp_intercept}`,
  same permutation-test significance approach as M1.
- [ ] `type_axis.py` (reused, not rewritten): `circ_axial` + `circ_corrcc`
  between `VKS_Angle` and the EEG ramp-angle.
- [ ] Univariate feature-correlation table (context only, same convention
  as M1) between the full FM100 and EEG feature sets.
- [ ] `04_fm100_vs_eeg.ipynb`: EEG reliability results, the merged table,
  both primary tests with plots, the context table, pooled and per-group
  where n allows (protan/deutan individually, keeping
  `docs/ssvepbeh_reliability_gaps.md`'s "these are thin" caveat visible
  rather than silently omitted).
- [ ] Update `docs/ssvep_beh_fm100_api_reference.md` and `README.md` for
  the M2 additions.
- [ ] Update `docs/findings.md` once M2 has real results.
- [ ] Note the three-way type/axis comparison
  (`VKS_Angle`/`orientation_deg`/EEG ramp-angle) as a candidate M3, rather
  than building it now.

## Next milestones

To be defined together.
