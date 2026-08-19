# SSVEP: proposed analyses

Seven proposals for explaining the group differences in this dataset. Every
number below was computed from `ssveps/files/` at session 1 before writing —
none of it is generic advice, and where the data contradicts an intuition I say
so rather than proposing an analysis that will not survive contact with it.

Read section 1 first. It changes what the rest of the document is for.

---

## 1. The binding constraint is power, not method

You observed that PD has lower amplitude than CTR. That is real in the means:

| group | n | baseline | mean raw | mean % change | ratio raw/baseline |
|---|---|---|---|---|---|
| CTR | 21 | 0.783 | 1.275 | **0.642** | 1.629 |
| PD | 6 | 0.709 | 1.074 | **0.541** | 1.516 |
| protan | 8 | 0.729 | 1.075 | 0.468 | 1.473 |
| deutan | 7 | 0.754 | 0.993 | **0.320** | 1.316 |

PD sits 16% below CTR in percent change. But:

```
Welch t-test on subject mean % change, PD vs CTR:  t = -0.56, p = 0.597
PD  subject means: sd 0.419, range [0.12, 1.30]
CTR subject means: sd 0.290, range [0.23, 1.27]
```

The distributions almost completely overlap. On the fitted trough amplitude the
effect is Cohen's d = 0.45 — a genuinely modest effect. At n = 6 vs 21 the power
to detect it is **0.11**:

| n per group | power for d = 0.45 |
|---|---|
| 6 | 0.11 |
| 15 | 0.22 |
| 30 | 0.40 |
| 40 | 0.50 |

**You would need roughly 80 per group for 80% power.** No statistical method
recovers that. This is not a reason to stop — it is a reason to pick analyses
that either (a) target effects large enough to survive n = 6, or (b) produce
per-subject measures whose reliability you can establish now and use later on a
larger sample. Every proposal below is one or the other, and I say which.

The one comparison in this dataset that is *not* power-limited is CVD vs CTR.
That is where proposal 2 goes.

---

## 2. The strongest effect here: the CVD trough lies outside the sampled gamut

**This is the finding I would lead with.** It emerged from the new surface fit
and it is not something the argmin could ever have shown you.

The replacement fit (`fit_ramp_gaussian`) models the grid as a linear ramp plus
one localized dip, with the dip's centre bounded inside the sampled range. When
a subject's true trough lies beyond the measured red range, the optimiser pushes
the centre to the boundary and pegs there. The fit now reports this as
`fitted_at_bound`.

```
CVD  at_bound: 11/15 (73%)
CTR  at_bound:  4/21 (19%)
Fisher exact p = 0.0019, odds ratio = 11.7
sensitivity 0.73, specificity 0.81
```

For 5 of 8 protan subjects `fitted_red` pegs at exactly 3200 — the top of the
red axis — with the width simultaneously at its maximum.

**Why this makes sense physiologically.** A protanope needs far more red
radiance to match a given green, so their isoluminant point sits at a higher red
value than a trichromat's. If the stimulus grid tops out at 3200 and their null
is beyond it, no amount of fitting will find an interior minimum — the surface
is monotonic across the whole measured range. The pegging is not a fitting
artefact; it is the measurement telling you the grid is too small for this
population.

**What to do with it:**

1. Treat "trough outside the sampled gamut" as a binary diagnostic marker in its
   own right and report its sensitivity/specificity properly (with a
   leave-one-out or bootstrap CI, since 0.73/0.81 is computed on the same data
   that motivated the cutoff).
2. Fit a **ramp-only model** to the pegged subjects and use the *slope* along
   red as the continuous measure. Slope is well-identified even when the trough
   is not, so you get a usable number for all 15 CVD subjects instead of 4.
3. Extrapolate the ramp to find where it would cross the trough — with explicit
   confidence bounds, clearly labelled as extrapolation.
4. **For future data collection: extend the red axis.** This is the concrete
   experimental recommendation falling out of the whole analysis.

**Caveat I want to be explicit about:** this reframes the earlier permutation
results. Deutan vs HC came out at p = 0.012 and protan vs HC at p = 0.042, but
if most CVD troughs are outside the gamut, those clusters are largely detecting
a *slope* difference across the grid rather than a shifted trough. Same
statistical result, different interpretation.

---

## 3. Decompose the variance: is PD's variability about the people, or the measurement?

You asked directly whether PD's greater variability tells us something about the
people. This is answerable now, and the answer is partly yes and partly "the
data cannot say."

Splitting the variance in percent change into within-subject (run to run,
within one session) and between-subject:

| group | n | within SD | between SD | between/(between+within) |
|---|---|---|---|---|
| CTR | 21 | 0.243 | 0.334 | 0.65 |
| PD | 6 | 0.194 | **0.462** | **0.85** |
| protan | 8 | 0.206 | 0.258 | 0.61 |
| deutan | 7 | 0.188 | 0.168 | 0.44 |

**The part that holds up.** PD's excess spread is entirely on the
between-subject axis. Their within-subject (run-to-run) variability is not
elevated at all — once you correct for the fact that noise scales with response
size (r = 0.295 between subject mean and subject within-SD across all 42
subjects, p = 0.058), the within-subject coefficient of variation is essentially
identical across groups:

```
within-subject CV (median):  CTR 0.396   PD 0.413   protan 0.423   deutan 0.554
```

So PD subjects are individually **just as internally consistent as controls**.
Whatever spread exists is not attention, fatigue, tremor, or a noisier
recording. It is differences *between* PD individuals. That is a meaningful
answer to your question: the variability is about the people, not the
measurement.

**The part that does not hold up.** Whether PD's between-subject SD is genuinely
larger than CTR's is not established:

```
bootstrap 95% CI on between-subject SD (2000 resamples)
  CTR  0.334  [0.259, 0.389]
  PD   0.462  [0.192, 0.603]      <- overlaps CTR entirely
Brown-Forsythe test of equal variance: W = 0.64, p = 0.43
```

At n = 6, an SD estimate is very unstable, and PD's range [0.12, 1.30] is driven
substantially by one high subject. **I would not claim PD is more variable on
this evidence.** I would claim the variability that exists is between-subject
rather than within-subject, which is a different and better-supported statement.

**The analysis to run.** A proper variance-components model (subject as a random
effect, nested runs, group as fixed) fitted across all subjects at once, giving
you within- and between-subject components with confidence intervals rather than
point estimates. `statsmodels`' `MixedLM` handles this. It also uses every
subject and every run instead of collapsing to group means, which is the only
way to buy back any power at these sample sizes.

**Why it matters clinically.** If PD's between-subject spread is real, it is a
candidate marker of disease heterogeneity — severity, duration, or dopaminergic
medication state, all of which affect retinal dopamine and hence contrast
response. That is a testable follow-up *if* you have those covariates. If you
do, this becomes the most interesting analysis in the set; if you do not,
collecting them is the highest-value addition to the dataset.

---

## 4. Separate a gain change from a shape change

PD's whole surface could be scaled down (a gain reduction), or its trough could
be selectively shallower (a chromatic-specific loss). These have different
interpretations and the current analyses do not distinguish them.

```
                                   CTR      PD      difference
trough region (3x3 around argmin)  0.349   0.217      -0.132
rest of the grid                   0.671   0.573      -0.098
```

The deficit is somewhat larger in the trough region but present everywhere — so
mostly a global gain reduction with a modest additional trough-specific
component. That is a real distinction worth testing rather than eyeballing.

**The analysis.** For each subject, fit
`PD_surface ≈ a * CTR_template + b`, where the template is the CTR group mean
grid. A pure gain change gives `a < 1` with good fit quality; a shape change
shows up as structured residuals concentrated near the trough. Then compare `a`
across groups. This turns "is it smaller or is it differently shaped" into two
numbers per subject, and it is far more powerful than a cell-wise test because
it uses all 100 cells to estimate two parameters.

The new fit already gives you a cleaner version of the same question:
`fitted_amp` (dip depth relative to the local ramp) is a shape measure, while
the ramp's intercept is a gain measure. They are separable by construction.

---

## 5. Choose outcome measures by their test-retest reliability, not their appeal

You have 19 subjects with two sessions. That is enough to rank candidate
measures by reliability, and reliability caps the effect size any measure can
ever detect. Doing this *first* is the cheapest power gain available.

Correlating each per-subject feature between session 1 and session 2 (14
subjects with a usable fit in both):

| feature | r (s1 vs s2) | p |
|---|---|---|
| `depth` (argmin trough depth) | **+0.78** | 0.001 |
| `fitted_green` (trough green position) | +0.54 | 0.045 |
| `fitted_amp` (dip amplitude) | +0.49 | 0.075 |
| `fitted_red` (trough red position) | **+0.17** | 0.563 |

**This should change what you report.** Trough *red position* — arguably the
most intuitive measure, and the one the whole trough-finding effort was aimed at
— is **not reliable within subjects** across sessions. Any group comparison on
`fitted_red` is fighting a measurement that does not reproduce in the same
person six months apart. Trough *depth* is reliable and should be the primary
outcome.

This is consistent with the existing ICC map work (mean ICC 0.77) and with the
trough being broad and flat: a flat basin means the horizontal position of the
minimum is poorly constrained even when its depth is well constrained.

**The analysis.** Extend the existing `reliability.py` ICC machinery from
per-pixel maps to the per-subject *features*, and report ICC with CIs for each
candidate outcome. Then compute, for each, the minimum detectable effect at your
actual n. That gives you a defensible reason for picking one primary endpoint.

---

## 6. Pick the normalization deliberately — it changes the answer by 2x

The three normalizations do not agree on effect size:

| method | CTR | PD | PD vs CTR | deutan vs CTR |
|---|---|---|---|---|
| percent | 0.642 | 0.541 | **-16%** | -50% |
| db | 2.010 | 1.682 | **-16%** | -44% |
| zscore | 9.483 | 5.958 | **-37%** | -61% |

Percent and db agree closely (they are monotone transforms of the same ratio, so
this is a consistency check passing, not independent evidence). **z-score more
than doubles the apparent PD deficit** — and that is largely an artefact:

```
baseline SD by group:  CTR 0.0793   PD 0.0788   deutan 0.0949
baseline CV by group:  CTR 0.101    PD 0.112    deutan 0.122
```

z-score divides by the baseline's own standard deviation, so a group with a
noisier baseline is pushed toward zero. Deutan's baseline CV is 21% higher than
CTR's, which inflates the deutan gap under z-score without any additional signal
loss. The z-score column is measuring baseline stability as much as response
amplitude.

**The recommendation.** Use percent change as the primary measure (it is also
what the MATLAB templates used, so results stay comparable to prior work), and
report db as a sensitivity check. **Do not use z-score for cross-group
comparisons** unless baseline variance is explicitly equalised or modelled —
state this in `methods.md` so nobody re-derives it later.

Separately: PD's baseline is itself 9% lower than CTR's (0.709 vs 0.783). This
deserves its own test. If PD subjects have a genuinely lower baseline EEG
amplitude, then *every* normalized measure is a ratio of two group-different
quantities, and the interpretation gets murkier. Worth checking before any of
the above is written up.

---

## 7. Use all 100 cells jointly instead of collapsing to one number

The current pipeline either compares single summary numbers (loses information)
or runs cell-wise permutation tests (pays a heavy multiple-comparison price
across 100 cells). There is a middle path that fits this data much better.

**Functional / multivariate approach.** Treat each subject's 10x10 grid as one
observation of a smooth 2D function. Then:

- **PCA across subjects on the 100-cell vectors.** The first two or three
  components will almost certainly capture "overall gain", "trough depth" and
  "trough position" as separate axes. Group-compare the component scores — three
  tests instead of 100, on components with far better SNR than any single cell.
  With 42 subjects at session 1 and 100 features this needs regularisation, but
  the surfaces are extremely smooth so the effective dimensionality is low.
- **Then test on the scores.** A three-component comparison at n = 6 vs 21 is
  still underpowered for d = 0.45, but it is roughly an order of magnitude
  better than cell-wise testing, and the components are interpretable in a way
  individual cells are not.

**Why this suits your data specifically.** The grid is heavily oversampled
relative to its information content — neighbouring cells are highly correlated
because the underlying surface is smooth (the new fit gets r² = 0.89 on the CTR
group mean using 8 parameters for 100 cells). Cell-wise testing pretends you
have 100 independent measurements; you have closer to 5-8 effective ones. PCA
makes that explicit instead of paying a correction for independence you never
had.

---

## What I would actually do, in order

1. **Proposal 2 (CVD gamut)** — the only well-powered effect in the dataset,
   p = 0.0019, and it yields a concrete experimental recommendation.
2. **Proposal 5 (reliability-first outcome selection)** — cheap, uses data you
   already have, and it has already produced one result that should change your
   reporting (`fitted_red` is not reliable).
3. **Proposal 6 (normalization decision)** — a documentation fix as much as an
   analysis; prevents a 2x artefact reaching a manuscript.
4. **Proposal 3 (variance components)** — answers your question about PD
   variability properly, with CIs.
5. **Proposal 4 (gain vs shape)** — the most scientifically interesting question,
   but interpret cautiously at n = 6.
6. **Proposal 7 (PCA)** — best method for the data's structure, but no method
   rescues n = 6; treat as preparation for a larger sample.

**And the honest summary:** PD vs CTR is underpowered and will stay underpowered
until you have more PD subjects. The CVD findings are solid. The reliability and
normalization work is worth doing regardless because it makes every future
comparison better. If a single decision comes out of this document, it should be
either "collect more PD subjects" or "extend the red axis of the grid" —
both are experimental, not analytical.

---

## Appendix: reproducing these numbers

Every figure in this document came from scripts in the session that produced it,
operating on `ssveps/files/` after the axis fix and the `ramp_gaussian` fit
landed. The per-subject features are in `ssveps/files/subject_troughs.csv`
(`fitted_amp`, `fitted_sigma_red`, `fitted_sigma_green`, `fitted_at_bound`,
`fitted_valid`). Note that `fitted_valid` now requires `not at_bound`, so
43/62 rows carry a usable trough location — by group at session 1: CTR 17/21,
PD 6/6, protan 2/8, deutan 2/7.
