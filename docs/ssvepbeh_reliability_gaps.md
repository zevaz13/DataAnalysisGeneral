# Behavioral-EEG relationship: what's established, what isn't, and next steps

Closes the two gaps `ssvepBeh/notebooks/01_explore.ipynb` left open before
the beh-EEG relationship could be called "safe and sound" -- multiple-
comparisons correction on `correlation.py`'s feature matrix, and
cross-session reliability. Full analysis: `02_reliability.ipynb`. This
document is the honest summary for future reference: one gap closed
cleanly, the other did not, and this records why and what would fix it,
per your standing request not to force a positive result where the data
doesn't support one.

## What's established

**Spatial overlap** (`overlap.py`'s `weighted_overlap_test`/
`click_value_test`): solid. Significant in every group on two
independently-constructed null models, and stable across EEG sessions
everywhere reliability is testable (pooled n=19, HC n=13, PD n=4 paired
subjects -- `obs_stat`/p-values nearly identical session 1 vs. session 2).
This part of the EEG test's validity against behavior is well supported at
this project's current sample size.

## What isn't established

**Individual-differences correlation** (`correlation.py`): not currently
real evidence, despite looking promising uncorrected. Two independent
checks agree:

1. **Multiple-comparisons correction.** Of 25 pairwise
   behavioral-x-EEG-feature correlations, pooled or in any group/subtype,
   **none survive Holm or the more permissive Benjamini-Hochberg FDR
   correction.** The strongest pooled pair (`orientation_deg` vs.
   `ramp_intercept`, uncorrected p=0.015) corrects to p=0.11 under FDR.
2. **Cross-session reliability.** Where testable at all (pooled, HC, PD --
   protan/deutan/CVD-combined can't be assessed, see below), r-values shift
   substantially between EEG sessions for the same feature pair -- e.g.
   HC's `beh_red` vs. `eeg_green` goes from r=-0.35 (session 1) to r=-0.06
   (session 2). None of the pooled analysis's headline pairs even rank
   among the top hits once restricted to the smaller paired-subject subset.

## Root cause: your own hypothesis, confirmed

### 1. Multidimensionality

`feature_correlations` runs 5 behavioral features x 5 EEG features = 25
independent univariate tests. This has two costs:

- **Statistical**: 25 tests spend a lot of multiple-comparisons budget.
  Real signal spread across a few features, none individually huge, can
  fail to survive correction even though a *joint* test using the same
  data would detect it.
- **It ignores that the features aren't independent of each other.**
  `beh_red`, `beh_green`, and `orientation_deg` are all derived from the
  same click cloud; `eeg_red`, `eeg_green`, `ramp_slope_red`,
  `ramp_slope_green`, and `ramp_intercept` are all derived from the same
  fitted surface. Running 25 univariate correlations throws away that
  internal covariance structure, which a multivariate method uses directly.

### 2. Lack of points, especially per subtype

Paired-subject counts (EEG data at both sessions), computed directly from
`ssveps/files/subject_troughs.csv`:

| category | n (main analysis) | n (paired, both EEG sessions) |
|---|---|---|
| pooled | 43 | 19 |
| HC (CTR) | 21 | 13 |
| PD | 6 | 4 |
| CVD (combined) | 15 | 2 |
| protan | 8 | 2 |
| deutan | 7 | **0** |

**deutan has zero subjects with EEG data at both sessions; protan and
CVD-combined have two each.** Reliability for the subtyping comparison
that matters most for the project's bifold clinical goal
(`project_ssvep_analysis_scope` memory) literally cannot be assessed with
today's data. Even the categories that *can* be tested sit at roughly half
the main analysis's n once restricted to paired subjects -- and small
samples are exactly where a correlation's sign and magnitude are least
stable, consistent with what session 1 vs. session 2 actually showed.

## Next steps

1. **More repeated-session CVD/protan/deutan data.** The direct fix for
   the sample-size half of the problem. Even getting deutan to n=3 paired
   (the minimum `session_reliability.py` requires to compute anything at
   all) and protan/CVD to n=5+ would let the reliability check run on the
   subtype comparisons that matter most. This is the same standing
   recommendation `ssveps/`'s own M6-M10 work has made throughout
   (`docs/ssvep_summary.md`) -- not a new ask, but this analysis adds a
   second, independent reason for it.
2. **A multivariate joint test instead of 25 univariate ones.** Two
   concrete options, in order of how much new infrastructure they need:
   - **Canonical Correlation Analysis (CCA)** between the 5-dimensional
     behavioral feature vector and the 5-dimensional EEG feature vector --
     finds the linear combination of each set that correlates best,
     directly using the joint covariance rather than testing each pair in
     isolation. One CCA + one permutation test for its significance
     replaces the 25-test multiple-comparisons problem with a single
     global null hypothesis. `scikit-learn`'s `CCA` or a hand-rolled
     permutation test (`np.random.default_rng`, shuffle one side's rows,
     refit, repeat -- the same pattern `ssveps/scripts/permutation.py`
     already uses) would both work; scikit-learn isn't currently a project
     dependency, so a permutation-test-only version (no new dependency) is
     the lower-friction path.
   - **A composite behavioral severity score**, mirroring `ssveps/`'s own
     M10 finding that EEG grid PC1 (75% of variance) is the dominant real
     axis and correlates >0.9 with `gain`/`ramp_intercept`. `beh/`'s M2
     work hasn't yet built an analogous single dominant behavioral
     severity axis across all features (though `orientation_deg` alone is
     a strong individual candidate, given it perfectly separates protan
     from deutan on its own -- `project_beh_m2_shape_features_finding`
     memory). Running PCA on the behavioral feature set and correlating
     its PC1 against the EEG's own PC1/`ramp_intercept` would be a lower-
     dimensional, single-test alternative to the 25-pair matrix, at the
     cost of losing per-feature interpretability.
3. **Re-run `01_explore.ipynb`'s correlation section once (1) or (2) lands**
   and update this document -- don't leave the "not yet established"
   verdict standing once the underlying problem (power, or test structure)
   has actually changed.

## What this means for moving on to FM100

Per your instruction, this is now a properly closed loop rather than an
open question: spatial overlap is solid and can be cited as-is; the
individual-differences correlation is documented as a real, honestly-
reported negative result with a concrete path forward, not silently
dropped or overstated. Safe to move on to the FM100 cross-modality work
next.
