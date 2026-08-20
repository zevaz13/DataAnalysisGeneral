# SSVEP grid analysis: conventions

Established during M1-M5 of the SSVEP project (`ssveps/`). These are the
non-obvious decisions and conventions that are easy to get wrong if
re-derived from scratch -- see `PLANssveps.md` for the full history and
reasoning behind each.

## The experiment

Each subject/session runs a red x green intensity grid (10x10 levels each,
`redArray` 0-3200, `greenArray` 0-2000) with 3-4 runs, plus 4 baseline trials
per run. `METxxx` is the subject id; `a`/`b`/`c` suffix on the raw filename
(none/`b`/`c`) is session 1/2/3. `MET037-040` (group `PD`) only have 3 runs
instead of 4 -- every function here reads the run count from the data rather
than assuming 4, so this "ragged" case is handled automatically, not as a
special case.

## Baseline trial split

Baseline trials 1-2 are pre-grid, 3-4 are post-grid (confirmed against the
raw data's trial ordering). `analysis.baseline_values(..., trials=)` selects
`'all'` (1-4), `'first2'` (pre only), or `'last2'` (post only).

`scope='run'` uses only that run's own 4 baseline trials; `scope='session'`
pools baseline trials across every run of the session. Aggregate/group
functions (`mean_grid`, `group_grid`, etc.) always operate on one fixed
`session` at a time -- passing a `group`/`subgroup` filter across sessions
would double-count the ~19 subjects who have both session 1 and 2.

## Normalization formulas

`analysis.normalize_grid(raw, baseline_vals, method=)`, given `base_mean =
baseline_vals.mean()`:

| method | formula |
|---|---|
| `percent` | `(raw - base_mean) / base_mean` |
| `db` | `10 * log10(raw / base_mean)` |
| `zscore` | `(raw - base_mean) / baseline_vals.std()` |

`zscore`'s `std()` is over the same `baseline_vals` used for `base_mean`, so
`scope`/`trials` selects the same trial subset for both the mean and the
spread.

## Axis convention: grids are [red_idx, green_idx], transposed for display

Every grid array in this codebase is indexed `[red_idx, green_idx]`, and every
plot puts red on the x axis and green on the y axis. Because `imshow` puts an
array's axis 0 on the *y* axis, `plotting._plot_heatmap` displays `grid.T`.

**The raw `runMap` array is the other way round**: its first axis is green and
its second is red, despite `mapDIM` reporting `RED_GREEN_RUN`.
`loader.to_rows` unpacks it in that order and emits truthful `red_idx` /
`green_idx` columns, so this is the one place the raw layout is visible and
everything downstream is consistent.

This was established three ways, after an earlier version of the code took
`mapDIM` at face value and had red and green swapped in every reported
coordinate (the heatmaps were unaffected -- they were drawn correctly by a
compensating error):

1. The MATLAB templates plot with `imagesc(redArray, greenArray, M)`
   (`group_permTesting_01JULY25.m:124`, `ICC_grids_22oct25.m:94`), and MATLAB
   maps an array's *columns* to x. So `M`'s rows are green -- and `M` comes
   straight from `runMap` with no transpose (`computeICC_gridMaps.m:25-33`).
2. `ssveps/CTRdata.png`, an independently produced reference for the CTR group,
   has its minimum at red 2133 / green 889. This pipeline now reports exactly
   that for CTR at session 1; the earlier code reported 1422 / 1333.
3. Decoding that image cell-by-cell and correlating against this pipeline's
   grid gives r=0.92 in this orientation and r=0.70 transposed.

Note that a correlation against the reference image cannot by itself validate
the *naming* -- the rendered pixels are identical either way. That is what let
the original error survive an r=0.99 image check. `ssveps/tests/test_ssveps.py`
pins the orientation at both ends: `test_loader_reads_runmap_green_first`
against the raw `.mat`, and `test_ctr_trough_matches_reference_image` against
the reference's coordinates.

## Trough depth: normalized by default

`analysis.trough_location`/`subject_troughs`/`group_troughs` locate each
subject's/group's minimum on the native 10x10 grid (argmin, no
interpolation). Depth defaults to **% change from baseline**
(`analysis.DEFAULT_NORMALIZE`), not raw value, because raw SSVEP
amplitude varies a lot subject-to-subject and isn't comparable across
subjects/groups -- pass `normalize=None` for raw depth instead.
`DEFAULT_NORMALIZE` is the same constant `permutation.py`'s and
`reliability.py`'s functions default to, for the same reason.

## Parametric trough surface fit (M4)

Grid argmin can only ever land on one of the 100 sampled points, and
individual subjects are noisy. `analysis.fit_trough_surface(grid, red_vals,
green_vals, method=)` fits a continuous surface to a grid and locates *that*
surface's own minimum instead (which can fall between grid points):

- `method='paraboloid'` (default) -- `z = a x^2 + b y^2 + c xy + d x + e y +
  f` via linear least squares (closed-form, no initial guess). More
  numerically stable given the trough's already-established broad, flat
  shape (M1).
- `method='gaussian'` -- an inverted 2D Gaussian dip via nonlinear least
  squares (`scipy.optimize.curve_fit`), seeded from the grid argmin. More
  flexible for a sharply localized trough, but can fail to converge.

Both report `fit_valid` (paraboloid: the Hessian must be positive-definite,
i.e. a genuine minimum, not a saddle; gaussian: the fitted amplitude must be
positive; both: the fitted location must fall inside the sampled red/green
range, not extrapolated) and `r_squared`. **The fitted minimum's *value* is
often notably higher than the observed grid's minimum pixel** -- expected,
not a bug: a smooth surface's best-fit vertex doesn't need to coincide with
the single noisiest/most extreme sampled point, especially for a trough
that's broad and flat rather than a sharp bowl. `subject_troughs(...,
surface_method=)` adds this fit's columns (`fitted_red`/`fitted_green`/
`fitted_depth`/`fitted_r_squared`/`fitted_valid`) alongside the existing
argmin ones in the same table.

## Test-retest reliability via per-pixel ICC (M5)

`reliability.py` replicates `ssveps/templateCode/ICCs/computeICC_gridMaps.m`
-- for subjects with both sessions (`paired_subjects`, checked at session 1
by default), compute each subject's session 1 and session 2 mean grids, then
for every one of the 100 grid cells compute the intraclass correlation
coefficient between the two sessions across subjects (`icc_grid`/`icc_map`)
-- an "ICC map" of which pixels are more or less reliable test-retest.

Python ICC: [`pingouin`](https://pingouin-stats.org/)'s `intraclass_corr`.
Its `'ICC(A,1)'` row (two-way random, absolute agreement, single
measurement -- McGraw & Wong 1996 notation) is exactly the template's MATLAB
`ICC(..., 'A-1')`, including matching CI/F/p columns.

**The CVD/protan/deutan test-retest sample is currently too thin to use.**
Of the 19 subjects with both sessions, only 2 are protan and 0 are deutan
(so `group='CVD'` combined is n=2) -- `pingouin`'s underlying ANOVA needs at
least 3 subjects, and `icc_grid` raises a clear `ValueError` rather than
silently running on too little data. Only `group='PD'` (n=4), `group='CTR'`
(n=13), and the unfiltered full paired set (n=19) currently have enough
paired subjects for a reliability analysis. This will change if/when more
session-2 data for the CVD subgroups is collected -- no code change would be
needed, just enough subjects for the existing `ValueError` to stop firing.

## Ramp-only fit, extrapolation, and bootstrap CIs (M6)

`analysis.fit_ramp` fits just the linear term (`z = c0 + c1*x + c2*y`) that
`fit_ramp_gaussian` already includes alongside its dip -- no dip, closed-form
least squares. The reason it exists as its own function rather than just
reading `fit_ramp_gaussian`'s ramp coefficients: `fit_ramp_gaussian` doesn't
expose them, and more importantly, a dedicated ramp fit has no interior
minimum to fail to find, so `ramp_slope_red` is defined for every subject --
including the CVD subjects whose trough lies beyond the sampled red range and
whose `fit_ramp_gaussian` fit therefore pegs (`at_bound=True`). See
`docs/ssvep_analyses.md` proposal 2 for the motivating finding (11/15 CVD
subjects pegged at session 1 vs 4/21 CTR) and `08_cvd_gamut.ipynb` for the
full worked analysis.

**Extrapolation target.** `analysis.extrapolate_ramp_crossing` solves the
fitted ramp line for the red value at which it would reach a given
`target_depth` at a given `green_ref`. For a pegged subject, that target
must **not** come from the subject's own `fit_ramp_gaussian` fit -- that's
exactly the fit `at_bound` says is unreliable there. `08_cvd_gamut.ipynb`
uses the median `fitted_depth`/`fitted_green` among each subgroup's own
`fitted_valid` subjects instead (decided explicitly, not defaulted to). That
reference is thin (2 valid protan, 2 valid deutan, project-wide) -- the
notebook says so directly rather than quoting the resulting extrapolated
positions as more precise than they are.

**The extrapolated position is unstable per-subject.** Dividing by a fitted
slope that happens to be close to zero for a given subject blows up both the
point estimate and its bootstrap CI (one pegged subject's 95% CI spans
roughly [-190000, 84000]; two pegged subjects' point estimates even land at
negative red, which is unphysical). Use it only as group-level, qualitative
support ("the trough is out there somewhere beyond the sampled range") --
`ramp_slope_red` itself is the stable, comparable per-subject measure, and
should be preferred for any actual group comparison.

**Bootstrap CIs generally.** `analysis.bootstrap_ci` is a generic percentile
bootstrap: it takes a `replicate_fn(rng)` that does its own resampling and
returns one statistic, calls it `n_boot` times, and returns the percentile
CI. Two different resampling units are used in this project depending on
what's being estimated: resampling *subjects* (with replacement) for a group
proportion's CI (e.g. `fitted_at_bound` sensitivity/specificity), and
resampling *runs* via `analysis.run_grids` (with replacement, then
refitting) for a single subject's fitted-statistic CI (e.g. the ramp-crossing
extrapolation above). `run_grids` was made public specifically to support the
latter.

## Within/between-subject variance decomposition (M7)

`variance.py` replaces the point-estimate within/between SD split in
`docs/ssvep_analyses.md` proposal 3 with a random-intercept MixedLM
(`statsmodels`) fit **per group** -- `value ~ 1`, grouped by subject, where
`value` is `analysis.run_mean_values`: one scalar per run, the mean of that
run's percent-change grid. The residual variance is within-subject
(run-to-run) spread; the random-intercept variance is between-subject spread.

**Why per group, not one pooled model.** The originally proposed alternative
was a single MixedLM across all subjects with group as a fixed effect and
`vc_formula` giving each group its own between-subject variance component.
That's closer to "one model, group as fixed effect," and would let you test
group differences in variance within one framework -- but it bakes in a
shared-residual-variance assumption across groups, and is materially more
complex to build and interpret. Decided against it (2026-08-20): fit each
group separately instead. This is justified by this project's own prior
finding that within-subject CV is roughly flat across groups already, so a
shared-residual assumption wasn't expected to change much, and the simpler
per-group models are what directly produces the per-group table this
milestone's checklist asked for.

**CI method.** `statsmodels`' own asymptotic standard errors on variance
components are unreliable at small n, so `variance.variance_components` uses
a subject-level percentile bootstrap instead (resample subjects with
replacement, refit, repeat -- `n_boot=2000` by default, matching the
bootstrap convention `docs/ssvep_analyses.md` already established elsewhere
in this project). Each bootstrap resample relabels subjects with fresh
synthetic ids (0..n-1) rather than reusing the real `sub_id` -- otherwise
drawing the same real subject twice in one resample would be misread by
`MixedLM` as one subject contributing double the runs, silently distorting
the within/between split for that replicate.

**Real-data finding worth flagging directly.** PD's within-subject SD is not
elevated (confirms the earlier point estimate), and its between-subject SD's
CI (`[0.12, 0.56]`) is wide and overlaps CTR's (`[0.19, 0.35]`) -- also
consistent with the earlier finding. Deutan's between-subject SD (`[0.00,
0.13]`) does **not** overlap CTR's -- lower, not higher. That's the opposite
of what "a neurological condition increases heterogeneity" would predict, and
it only showed up once the decomposition was done properly (`09_variance_
components.ipynb`) -- worth treating as a real result to revisit as more
session-2 CVD data comes in, not explaining away.

## Gain vs. shape decomposition (M8)

`analysis.fit_gain_shape(grid, template)` fits `grid ~= gain*template +
intercept` by linear least squares over all 100 cells -- `template` is
typically the CTR group mean grid (`analysis.group_grid(..., group='CTR')`).
`analysis.trough_region_residual(residual, red_idx, green_idx)` then asks
whether what's left over after removing that uniform gain is concentrated in
a window around a *fixed* location -- the **template's own trough**
(`analysis.trough_location(template, ...)`), not each subject's own -- versus
spread evenly across the rest of the grid. Using the template's trough
location rather than the subject's own is deliberate: it's exactly what lets
this analysis say something about subjects whose own trough couldn't be
located at all (most protan/deutan subjects, per M6).

**This does not reproduce `docs/ssvep_analyses.md` proposal 1's "PD is 16%
below CTR" number, and that's expected.** Proposal 1's number came from
*trough depth* alone (`subject_troughs.csv`'s `depth` column, one localized
quantity); `gain` here is a regression over the *whole* 100-cell grid,
dominated by the ramp rather than the trough. Different statistics, expected
to diverge -- don't treat a mismatch between the two as a bug.

**Real-data finding.** After removing gain, PD's and deutan's residuals at
the CTR template's trough are indistinguishable from zero (one-sample t-test
vs. 0: p=0.56, p=0.63) -- no trough-specific effect beyond gain for either.
Protan's is not (mean -0.10, p=0.030, n=8, one test, uncorrected) -- a
genuine shape effect. This connects to M6: protan had the shallowest
`ramp_slope_red` of the three groups, i.e. the trough sitting furthest beyond
the sampled range on average, which is exactly what would put a protan
subject's response at the CTR template's trough location still on their own
descending ramp rather than recovering the way CTR's template does past its
own dip.

**Cross-check against M6's separable measures.** `gain` (this decomposition)
correlates strongly with `ramp_intercept` (M6's `fit_ramp`, r=0.87,
p<1e-13) -- two independently-derived gain proxies agree well, good evidence
"gain" is a real, robustly-measurable axis here. `trough_region_residual`
does **not** correlate with `fitted_amp` (M4/M6's `fit_ramp_gaussian`, r=0.04,
p=0.79) -- not a failure, they measure different things: `fitted_amp` is
subject-centered (this subject's own dip depth, wherever their dip is);
`trough_region_residual` is template-centered (the residual at one fixed
external location). They can disagree completely for a subject whose own
trough is nowhere near the template's, which is exactly the case
`trough_region_residual` exists to handle.

## Reliability-first outcome selection (M9)

`reliability.feature_icc` extends the per-pixel `ICC(A,1)` machinery (M5) to
per-subject scalar features: same computation (`_icc_a1`, shared with
`icc_grid`), applied to a candidate outcome measure's session-1/session-2
values instead of one grid cell's. Three features are defined for every
paired subject regardless of fit quality (`depth`, M6's `ramp_slope_red`, M8's
`gain`); three depend on `fit_ramp_gaussian` locating an actual dip
(`fitted_green`/`fitted_amp`/`fitted_red`) and are restricted to the subjects
where that fit was `fitted_valid` at both sessions -- 14 of the 19 paired
subjects, matching how `docs/ssvep_analyses.md` proposal 5 originally
computed these three (confirmed: this project's ICC on that same 14-subject
filter reproduces the document's plain-Pearson-correlation numbers closely,
e.g. `fitted_red` 0.18 ICC vs. the document's r=0.17).

**Primary outcome measure, updated (2026-08-20).** `depth` (ICC=0.76) was the
best of the original four candidates and the previous recommendation. Since
then, M6's `ramp_slope_red` (ICC=0.85) and M8's `gain` (ICC=0.90) turned out
to be *more* reliable, not just comparably reliable -- both are now the
recommended primary outcome for anything involving the CVD/subtype
comparisons M6-M8 are about, since they were purpose-built for exactly that
question. `depth` remains a fine choice outside that context, or for
continuity with the argmin-based MATLAB templates. `fitted_red` (ICC=0.18)
should not be used as a primary outcome in any comparison -- see the minimum
detectable effect argument below for why that's not just "somewhat worse."

**Minimum detectable effect.** `reliability.minimum_detectable_effect(n1, n2,
icc=)` connects a feature's ICC directly to this project's actual power,
via classical test theory's attenuation result: unreliable measurement
shrinks an observed effect size relative to the true one by a factor of
`sqrt(icc)` (`d_observed = d_true * sqrt(icc)`, because ICC =
var(true)/var(observed) implies SD_observed = SD_true/sqrt(icc), and the raw
mean difference is unaffected by measurement noise on average). Dividing the
standard two-sample-t-test minimum detectable *observed* effect by
`sqrt(icc)` gives the smallest *true* effect that could still survive that
much attenuation: `d_true = d_observed / sqrt(icc)`. At this project's
PD-vs-CTR sample size (n=6, 21), `fitted_red`'s ICC pushes the minimum
detectable true effect past d=3 -- larger than the largest effect size seen
anywhere in this dataset so far (proposal 1's PD-vs-CTR trough-depth effect,
d=0.45). That's what makes `fitted_red` unusable, not just "less good."

## PCA of the response grid, with permutation-based component selection (M10)

`pca.py` treats each subject's 10x10 grid as one 100-dimensional
observation and runs ordinary PCA via SVD (`pca.fit_pca`) -- no covariance
shrinkage or other regularized-covariance estimator.

**Why permutation-based component selection instead of literal covariance
regularization.** `docs/ssvep_analyses.md` proposal 7 flagged that PCA at
n=43 subjects vs. 100 features "needs regularisation." The literal reading
(shrinkage-regularized covariance, e.g. Ledoit-Wolf) would add a new
dependency (`sklearn.covariance`) and a technique with no other precedent in
this codebase. Decided against it (2026-08-20) in favor of
`pca.permutation_component_count`: permute each grid cell independently
across subjects (destroys cross-cell correlation, keeps each cell's own
marginal distribution), redo PCA, repeat many times to build a null
explained-variance-ratio spectrum per component rank, and only trust
components whose observed ratio beats their own rank's null. This is a
numpy-native technique (Horn's 1965 parallel analysis) that reuses the same
permutation-testing idea `permutation.py` (M3) and the bootstrap CIs (M6,
M7) already use elsewhere in this project, rather than introducing a new
paradigm for one milestone.

**Real-data finding.** PC1 alone explains 75% of the variance and is the
only component that clears the permutation noise floor -- stricter than
proposal 7's own expectation of "two or three" trustworthy components (PC2's
observed ratio, 5.4%, sits just below its rank's null threshold, 6.1%). This
doesn't mean PC2/PC3 carry zero signal, just that they aren't statistically
distinguishable from what 100 correlated-but-otherwise-unstructured cells
would produce by chance at n=43.

**PC1 is the gain axis, found a third independent way.** PC1's loading is
uniform in sign across almost the whole grid (a flat, whole-surface pattern,
not something localized near the trough), and its scores correlate at r=-0.93
with M8's `gain` and equally strongly with M6's `ramp_intercept` -- three
completely independent derivations (unsupervised PCA with no group labels or
template; a template regression; a ramp fit's intercept) converging on the
same axis. Good evidence "gain" is the dominant real axis of variation in
this dataset, not an artifact of one fitting choice. PC1 doesn't separate PD
from CTR (p=0.63, same underpowered story as everywhere else for PD), but
comes closer to separating protan from deutan (p=0.092) than any single
M6/M8 measure did -- consistent with proposal 7's claim that combining all
100 cells into one component improves SNR over any individual derived
measure, though "closer" is not "significant."

## Cluster-based permutation testing (M3)

`permutation.py` replicates `ssveps/templateCode/permTestingcomparisons/*.m`
-- cluster-based permutation testing (Maris & Oostenveld style) between two
groups' mean grids, generalized to any `group`/`subgroup` pair instead of the
template's hardcoded-subject-list scripts. Three functions, one per
sophistication level in the template (kept separate, not collapsed into one,
matching the template's own progression):

- `permutation_test_size` -- two-tailed z-threshold, clusters kept only if
  their size exceeds the null distribution's 95th percentile.
- `permutation_test_weighted` -- adds a second correction criterion (cluster
  weight = sum of `|z|` in the cluster) and a per-cluster p-value.
- `permutation_test_directional` -- separates positive- and negative-going
  clusters, each with its own one-tailed null and size+weight correction.

**No subject is discarded.** `n1`/`n2` (how many subjects each permutation
draws per group) default to the **full group sizes**, so each permutation is a
plain relabelling of everyone, computed over exactly the subjects the observed
difference map uses.

This is a deliberate departure from the MATLAB templates, which hardcoded a
subsample per comparison (`group_permTesting_01JULY25.m` used 30 of 33 HC and
5 of 7 CVD). An earlier version of this code generalized that to "balance both
groups to the smaller one's size", which was much more aggressive than the
template ever was -- for PD vs CTR at session 1 it drew 6 of 21 controls,
throwing away 15 subjects. Discarding subjects widens the null distribution
and shrinks every z-score: measured on that comparison, max |z| fell from 1.81
to 1.43. It also leaves the permuted statistic computed at a different sample
size than the observed one, which a permutation null should not do.

`n1`/`n2` remain parameters, so the template's behaviour can still be
reproduced deliberately.

**One correctness fix vs. the template** (confirmed): in
`group_permTesting_positive_negative_clusters.m`, the negative-cluster null
used `max()` over an array of negative cluster-weight sums -- which picks the
value *closest to zero* (the weakest negative cluster) rather than the most
extreme one. This biased the negative null toward small magnitudes, making
the negative-cluster significance threshold too lenient. `permutation_test_
directional` uses `min()` for the negative tail, symmetric with the positive
tail's `max()`.

Cluster connectivity is 8-connected (`scipy.ndimage.label` with a full 3x3
structuring element) to match MATLAB `bwconncomp`'s 2D default -- `scipy`'s
own default is 4-connected (cross-shaped), so this must be passed explicitly.

## `metadata.csv`: hand-edits are permanent, and preserved by default

`group`/`subgroup` in `ssveps/files/metadata.csv` were hand-corrected for
some subjects (e.g. `MET043-046`) after the raw `.mat` files' own labels were
found stale (`UNKNOWN`/`NA`). Two rebuild scripts exist with different
policies:

- `scripts/build_derived.py` -- full from-scratch rebuild, **always**
  regenerates `group`/`subgroup` from the raw files. This wipes any hand-edit.
  Intentional-reset-only.
- `scripts/update_derived.py` -- incremental: a new subject/session is added
  directly; an existing one prompts `[y/N]` before overwriting, and even then
  only refreshes `runmap.csv`/`baselines.csv` -- `group`/`subgroup` in
  `metadata.csv` is set once at first creation and never touched again. Use
  this for day-to-day updates.

## Grid-file naming (`ssveps/files/`)

All CSVs are tidy/long-format, keyed by `sub_id`/`session` (and `run` where
applicable), rebuilt from the raw `.mat` files -- safe to delete and rerun
`build_derived.py`, except `metadata.csv`'s hand-edited `group`/`subgroup`
values (see above). `subject_troughs.csv`/`group_troughs.csv` are a further
derived layer (via `scripts/build_troughs.py`) on top of the others, with no
hand-edits of their own -- always a straight recompute.
