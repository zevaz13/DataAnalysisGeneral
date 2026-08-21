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

- [x] `eeg_features.py`: per-subject, per-session `ramp_magnitude`
  (derived) and ramp-angle (derived, stored as the *full* [0, 360)
  direction -- folded to axial only downstream, since unlike `VKS_Angle`
  the raw gradient direction is genuinely meaningful, not arbitrary-sign;
  see the module's own docstring), plus the raw `ramp_slope_red`/
  `ramp_slope_green`/`ramp_intercept`/`ramp_r_squared` columns passed
  through, reusing `ssveps/files/subject_troughs.csv` directly. A
  pooled-across-sessions version wasn't needed -- M2's cross-modality merge
  uses EEG session 1, matching `ssvepBeh/`'s own convention.
- [x] EEG reliability for the two *derived* features: ICC(A,1)
  (`fm100_features.reliability.feature_icc`, reused rather than
  re-resolving `ssveps/`'s reliability module) for `ramp_magnitude`,
  `circ_corrcc` (after `circ_axial` folding) for the ramp-angle,
  `03_eeg_reliability.ipynb`. **Result: both moderate, not strong**
  (`ramp_magnitude` ICC=0.65 -- notably *lower* than `ramp_slope_red`'s own
  established 0.85, apparently diluted by combining it with the untested
  `ramp_slope_green`; ramp-angle circular r=0.69, p=0.012). As expected
  going in, `group='CVD'` (combined, n=2), `subgroup='protan'` (n=2), and
  `subgroup='deutan'` (n=0) all correctly raise `ValueError` -- confirmed,
  not just anticipated.
- [x] Merge FM100 (pooled) with EEG (session 1) features, one row per
  subject present in both -- **43, exactly as expected.**
- [x] `severity.py` (reused, not rewritten): CCA between
  `{TES, VKS_MajRad, VKS_MinRad}` and `{ramp_magnitude, ramp_intercept}`,
  same permutation-test significance approach as M1.
- [x] `type_axis.py` (reused, not rewritten): `circ_axial` + `circ_corrcc`
  between `VKS_Angle` and the EEG ramp-angle.
- [x] Univariate feature-correlation table (context only, same convention
  as M1) between the full FM100 and EEG feature sets.
- [x] `04_fm100_vs_eeg.ipynb`: EEG reliability results, the merged table,
  both primary tests with plots, the context table, pooled and per-group
  (protan/deutan individually shown, not silently omitted).
- [x] Update `docs/ssvep_beh_fm100_api_reference.md` and `README.md` for
  the M2 additions.
- [x] Update `docs/findings.md` once M2 has real results.
- [x] Note the three-way type/axis comparison
  (`VKS_Angle`/`orientation_deg`/EEG ramp-angle) as a candidate M3, rather
  than building it now -- still open, not started.

### M2 results

**Severity (CCA, `{TES, VKS_MajRad, VKS_MinRad}` vs. `{ramp_magnitude,
ramp_intercept}`): significant pooled but more modest than the behavioral
version** (r=0.50, p=0.047, n=43, vs. M1's r=0.73, p<0.001) -- and, same
pattern as M1, doesn't hold up within any single group (all p>0.08). Likely
partly a between-group effect as in M1, further diluted by EEG's noisier
measurement.

**Type/axis (circular correlation, `VKS_Angle` vs. the EEG ramp-angle):
significant pooled** (r=-0.40, p=0.014, n=43 -- the sign isn't directly
comparable to M1's positive r; each pair of angle spaces has its own
coordinate convention). **Per-group: only `deutan` reaches significance**
(r=0.66, p=0.034, n=7) -- a lead worth re-testing with more deutan
subjects, not yet a confirmed finding at that n, and notably weaker than
M1's within-*CVD* result (n=15, p=0.031). CTR and CVD (combined) are both
essentially at r=0; protan trends negative but isn't significant (p=0.12).

**Overall: both EEG results replicate the direction of M1's findings but
weaker** -- consistent with everything else in this project (EEG is a real
but noisier window onto the same underlying spectrum than direct
behavioral report is). **The single most solid result across all of
M1+M2 remains M1's within-CVD `VKS_Angle`-vs-`orientation_deg` finding**
(n=15, p=0.031) -- more CVD/protan/deutan subjects would do more for this
line of work now than further methodological refinement.

## M3: the three-way type/axis comparison

M1 and M2 each tested one edge of a triangle: `VKS_Angle`-vs-
`orientation_deg` (M1) and `VKS_Angle`-vs-EEG-ramp-angle (M2). The third
edge -- `orientation_deg` vs. the EEG ramp-angle directly -- has never been
tested. M3 completes the triangle, then asks the sharper question all
three pieces make possible: do the three angles agree *jointly*, not just
pairwise?

Not in scope for M3: revisiting whether the severity CCA (M1/M2) holds up
within a single group. That needs more CVD/protan/deutan subjects, not new
analysis code -- a standing note for whenever more data arrives, not a
milestone to implement now.

### Decisions

- **Require all three datasets per subject**, not each pairwise test using
  its own maximal overlap -- checked directly: FM100 ∩ behavioral ∩ EEG
  (session 1) is **43 subjects, identical to M2's FM100 ∩ EEG overlap**
  (protan n=8, deutan n=7, the full expected sample -- behavioral data
  doesn't further restrict it). Keeps the joint test and all three pairwise
  tests running on exactly the same sample, directly comparable to each
  other.
- **Circular correlation sign is not comparable across pairs -- confirmed,
  not just suspected.** M2's `VKS_Angle`-vs-ramp-angle pooled r was
  negative (-0.40), opposite in sign to M1's `VKS_Angle`-vs-`orientation_deg`
  result (+0.37), because each pair of angle spaces has its own arbitrary
  coordinate convention. The joint statistic therefore uses
  **`mean(|r|)`** across the three pairwise `circ_corrcc` values, not a
  signed sum/mean -- a signed combination would let pairs partially cancel
  for no principled reason, understating real three-way structure whenever
  the pairs don't happen to share a sign convention (exactly the situation
  M1 vs. M2 already demonstrated).
- **One new function, `type_axis.py`'s `joint_concordance_test`**, not a
  new module -- same domain (angle data) as `circular_correlation_test`,
  same file. Takes a **list** of axial angle arrays (`>= 2`, not hardcoded
  to 3) for the same natural generality `severity.py`/`type_axis.py`
  already have.
- **Permutation scheme generalizes `severity.cca_test`'s** (shuffle `Y`
  relative to `X`) **to more than two arrays**: hold the first angle array
  fixed, independently permute the subject order of every other array,
  recompute `mean(|r|)` on the permuted arrangement, repeat `n_perm` times.
  Same `(1 + count) / (1 + n_perm)` p-value correction used everywhere else
  in this project.
- **Triangle-completion pairwise test reuses `type_axis.circular_correlation_test`
  unchanged**, a third time -- `orientation_deg` vs. EEG ramp-angle, same
  pooled + per-group breakdown convention as M1/M2's other two edges.

### Checklist

- [x] Merge FM100 (pooled), behavioral (M2 shape features), and EEG
  (session 1) features into one table, one row per subject in the triple
  overlap -- **43, exactly as expected.**
- [x] Pairwise triangle-completion: `type_axis.circular_correlation_test`
  between `orientation_deg` and the EEG ramp-angle, pooled and per-group
  (same `categories` convention as M1/M2).
- [x] `type_axis.py`: add `joint_concordance_test(angle_arrays, *, n_perm=5000, seed=None) -> dict`
  -- `mean(|pairwise circ_corrcc r|)` as the statistic, permutation null as
  described above. Returns `{statistic, p_value, null_stat, pairwise_r}`
  (`pairwise_r` a dict keyed by array-index pairs, so the joint result can
  still be decomposed back into its three components). Validated
  numerically against synthetic correlated/independent data before running
  on real data.
- [x] Run the joint test on all three angles (`VKS_Angle`, `orientation_deg`,
  EEG ramp-angle), pooled and per-group where n allows.
- [x] `plotting.py`: `plot_pairwise_bars` (the three pairwise `|r|` values,
  dashed line at the joint statistic) and `plot_joint_null_distribution`
  (same pattern as `plot_null_distribution`, for the joint statistic).
- [x] `05_three_way_type_axis.ipynb`: the completed triangle (all three
  pairwise results side by side, including M1's and M2's already-known
  ones for context), the joint concordance test with plots, pooled and
  per-group, a summary comparing the joint result against the three
  pairwise ones.
- [x] Update `docs/ssvep_beh_fm100_api_reference.md`, `README.md`, and
  `docs/findings.md` once M3 has real results.

### M3 results

**Triangle completed, and the third edge doesn't hold up on its own:**
`orientation_deg` vs. EEG ramp-angle, pooled, is **not significant**
(r=-0.23, p=0.13, n=43) -- unlike M1's edge (r=0.37, p=0.009) and M2's edge
(r=-0.40, p=0.014).

**The joint concordance test is significant pooled anyway** (mean
`|r|`=0.33, p=0.0012) -- real evidence that the three angle measures share
underlying structure *as a system*, surviving the one weak edge rather than
being undermined by it. This is the strongest whole-project argument yet
for the original continuous-spectrum hypothesis: not one strong pairwise
measurement, but a pattern consistent enough across three independent
instruments (FM100, behavioral, EEG) that a test built to be robust to any
single weak edge still finds it.

**No single group confirms the joint result on its own** at current n
(all per-group joint p-values > 0.08) -- same pattern M1/M2's severity CCA
already showed. One new, specific lead: **`protan` alone is significant on
the triangle-completion edge** (`orientation_deg` vs. EEG ramp-angle,
r=-0.57, p=0.023, n=8) -- the opposite of the pooled non-result, worth
re-testing with more protan subjects, not yet a confirmed finding at n=8.

**Verified before trusting the joint statistic's design**: with 3 pairs,
a signed mean can hide real structure when pairs don't share a sign
convention -- confirmed with a synthetic equal-and-opposite-correlation
example (`test_joint_concordance_test_uses_absolute_value_not_signed_mean`)
where `|r|`-mean correctly exceeds what a naive signed mean would report.

## Next milestones

M1, M2, and M3 are all complete for this session -- picking back up here
next time. Two candidate threads, neither scoped in detail yet:

- **`protan`'s significant triangle-completion edge** (M3, n=8) -- worth a
  closer look on its own before deciding whether it's a real subtype-
  specific signal or a small-n artifact.
- **More CVD/protan/deutan subjects**, the standing recommendation this
  entire project (not just this milestone) keeps arriving at -- would do
  more for every open question here (severity CCA's within-group status,
  M3's per-group joint test, `deutan`'s M2 lead) than further methodological
  refinement at this point.

To be defined together when we come back to this.
