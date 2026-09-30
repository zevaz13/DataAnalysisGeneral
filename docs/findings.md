# Findings so far

Hi! This is a guided tour of everything we've learned from the color-vision
data so far, across all five ways we've looked at it. Nothing here is final
-- the point of this document is to give you a readable map of where things
stand today, with a direct link to the notebook behind every claim, so you
can open any of them, poke at the parameters, and push the story further
yourself. Treat every number below as an invitation to go check it in
context, not a conclusion to take on faith.

For the experimental background (what the stimulus is, why we're comparing
these particular measures), see `docs/experiment_summary.md`. This document
assumes that context and focuses on what we've actually found.

The figures below are generated straight from the raw data, same as every
number quoted around them -- `uv run python docs/make_figures.py`
regenerates all of them (here and in `docs/experiment_summary.md`) if the
underlying data or analysis changes.

## What changed when MET048 joined the deutan group

Every number in this document was re-run on 2026-09-18 after adding **MET048**
(deutan, one session, present in FM100, behavioral, and EEG). Deutan goes from
n=7 to n=8, and CVD overall from n=15 to n=16. To isolate what that one
subject does, every notebook was executed twice on otherwise identical data --
with and without MET048 -- and the "before" column below is that
without-MET048 run, not the older stored notebook outputs (those also predate
MET047's EEG data, which would blur the comparison).

| Result | Before (deutan n=7) | With MET048 (n=8) |
|---|---|---|
| EEG, protan vs deutan, cluster-based test: seeds (of 200) with a corrected-significant cluster, size variant | 173 | **0** |
| EEG, protan vs deutan, PC1 (Welch) | p=0.092 | p=0.64 |
| EEG, protan vs deutan, `ramp_slope_red` (Welch) | p=0.44 | p=0.38 |
| EEG, HC vs deutan, `ramp_slope_red` (Mann-Whitney) | p=0.048 | p=0.041 |
| EEG, CVD vs HC, trough runs off the grid: sensitivity, Fisher p | 73% (11/15), p=0.0019 | 75% (12/16), p=0.0010 |
| Behavioral, protan vs deutan, mean click location (Hotelling) | p=0.0042 | p=0.0061 |
| Behavioral, protan vs deutan, click-line orientation | p=0.0003, perfect separation | p=0.0002, perfect separation |
| Behavioral, protan vs deutan, `along_var` | p=0.072 | p=0.038 (uncorrected) |
| FM100, HC vs deutan, `VKS_Angle` | p=0.10 | p=0.32 |
| FM100 vs behavioral, type/axis, within CVD | r=0.557, p=0.031 (n=15) | r=0.559, p=0.029 (n=16) |
| FM100 vs EEG, type/axis, within deutan | r=0.661, p=0.034 (n=7) | r=0.629, p=0.028 (n=8) |
| Three-way joint concordance (FM100, clicks, EEG) | p=0.0012 | p=0.0012 |

**Most results barely move -- the one that flips is the EEG protan-vs-deutan
cluster.** The behavioral separation, the FM100 group differences, the
CVD-vs-control EEG signal, and the three-way agreement all survive intact
(several get slightly stronger). But the seed-stable, spatially localized
protan/deutan difference in the EEG grid, which the previous version of this
document called the most solid subtype signal in the SSVEP data, disappears:
no seed out of 200 finds a corrected-significant cluster once MET048 is in.
A leave-one-out check says it really is this one participant: dropping
MET048 alone brings the cluster back (17 of 20 seeds), while dropping any of
the other 15 protan/deutan subjects one at a time leaves it at 0 of 20.

Why this participant: MET048 is a *mild* deutan on the FM100 (total error 100,
the lowest of the eight deutan subjects, whose others run 136-300; HC averages
55) and, at the same time, the strongest EEG responder in the whole CVD group
-- an overall response of 1.04 (percent change from baseline) against 0.1-0.5
for the other seven deutan subjects, and 5th highest out of all 45 subjects at
session 1 (some healthy controls respond just as strongly). In the
low-red/high-green corner where the old cluster lived, MET048 responds at 0.8,
as strongly as the strongest protan subjects, versus 0.1-0.3 for the other
deutan subjects. Nothing points to a recording problem, but one thing is worth
keeping in mind: MET048's baseline level is on the low side (0.66, about the
10th percentile of subjects, similar to MET046's), and a lower baseline makes
percent-change values larger for the same raw response. So this looks like a
real high-responder deutan participant, possibly amplified a little by the
normalization -- either way, exactly what a small sample can't absorb. The old cluster was also
borderline to begin with (its p-value at seed 0 was 0.046), so "stable across
seeds" turned out to mean "stably just under 0.05", not "large".

Two caveats on reading the rest of this document. First, MET047 (one session,
odd data, no group) is still in the EEG file with group `UNKNOWN`: it is
excluded from every group comparison, but the pooled "all subjects" EEG
analyses (n=46 for FM100-vs-EEG and PCA) include them. Second, the FM100
session-to-session reliability numbers in section 5 are computed on 20 paired
subjects, where the previous version said 19. That difference is **not** from
MET048 (it is identical with and without them) -- it comes from something else
that changed in the FM100 data since the previous run, and we couldn't tell
what from the data alone.

## What changed when MET049 joined the protan group

Every number in this document was re-run on 2026-09-30 after adding **MET049**
(protan, one session, present in FM100, behavioral, and EEG). Protan goes from
n=8 to n=9, and CVD overall from n=16 to n=17. As with MET048, the "before"
column below is the without-MET049 state, checked directly against the live
data rather than assumed from the previous write-up -- the ssveps-side numbers
came back exactly matching what was already written down here, which is a
useful sanity check on the document itself.

| Result | Before (protan n=8) | With MET049 (n=9) |
|---|---|---|
| EEG, protan vs deutan, cluster-based test: seeds (of 200) with a corrected-significant cluster, size variant | 0 | 0 |
| EEG, protan vs deutan, PC1 (Welch) | p=0.64 | p=0.62 |
| EEG, protan vs deutan, `ramp_slope_red` (Welch) | p=0.38 | p=0.33 |
| EEG, HC vs protan, `ramp_slope_red` (Mann-Whitney) | p=0.0019 | p=0.0015 |
| EEG, CVD vs HC, trough runs off the grid: sensitivity, Fisher p | 75% (12/16), p=0.0010 | 76.5% (13/17), p=0.0008 |
| Behavioral, protan vs deutan, mean click location (Hotelling) | p=0.0061 | p=0.0029 |
| Behavioral, protan vs deutan, click-line orientation | p=0.0002, perfect separation | p=0.0001, perfect separation |
| Behavioral, protan vs deutan, `along_var` | p=0.038 | p=0.046 |
| FM100, HC vs protan, `VKS_Angle` | p=0.013 | p=0.0066 |
| FM100 vs behavioral, type/axis, within CVD | r=0.56, p=0.029 (n=16) | r=0.54, p=0.031 (n=17) |
| Three-way joint concordance (FM100, clicks, EEG) | p=0.0012 | p=0.0010 |

**Unlike MET048, nothing here flips.** Every result that was significant stays
significant, everything null stays null, and most of the already-strong
results get a little stronger rather than weaker -- the behavioral orientation
separation, the FM100 HC-vs-protan features, and the CVD-vs-control EEG
sensitivity all tightened. MET049's own trough fit runs off the grid
(`fitted_at_bound=True`), same as the typical CVD subject, which is exactly
why the sensitivity number moved the direction it did. The protan-vs-deutan
comparisons that were already underpowered (EEG PC1, EEG `ramp_slope_red`,
FM100 features) stay underpowered, moving a few points either way but not
crossing p=0.05 in either direction. In short: this addition behaved the way
you'd hope a new, unremarkable data point behaves -- it sharpens existing
signal instead of introducing a surprise, which is itself worth noting given
how much one participant (MET048) moved things just twelve days earlier.

## The shape of the project

Several ways of looking at the same underlying question -- does someone
have a color vision deficiency, and if so, which kind and how severe:

1. **`standardizedScores/FM100/`** -- the Farnsworth-Munsell 100 Hue test, a
   validated clinical reference standard, independent of our own stimulator.
2. **`beh/`** -- our stimulator's behavioral (manual match) task: participants
   click the (red, green) mix that looks the same as a fixed yellow.
3. **`ssveps/`** -- our stimulator's EEG task: the same physical judgment,
   measured indirectly via brain response across a 10x10 grid of red/green
   combinations.
4. **`ssvepBeh/`** -- do (2) and (3) actually agree with each other?
5. **`ssvep_beh_fm100/`** -- does (1) encode a continuous severity spectrum
   that (2) (and eventually (3)) also picks up on?

Below, one section per piece, roughly in the order we built them.

## 1. FM100: does our data even make sense against a known clinical test?

`standardizedScores/FM100/notebooks/01_explore.ipynb`

We took the classic 85-cap hue-ordering test, rebuilt its scoring math from
a template we'd used before, and -- before trusting a single number out of
it -- checked our new code against the original template's output on all 69
real test sessions we had at the time (MET048's session came later and has no
template output to check against). **Every score matched bit-for-bit.** That's the kind of
boring-but-essential check that makes everything downstream trustworthy.

With that settled, the scores tell a clean, expected story: protan and
deutan participants both show the classic signature of a red-green
deficiency (their error concentrates on the red-green axis of the test, not
the blue-yellow axis). Two participants stood out as genuinely interesting
edge cases rather than noise:

- **MET047** (one session; no behavioral data) has a total error score about
  as high as our CVD group's average -- but unlike protan/deutan, their errors
  are *evenly* split between the red-green and blue-yellow axes. That's not
  the usual pattern, which is why they were flagged as worth a closer look for
  a different kind of deficiency. In the end their data were too odd to place
  in any group, so they stay `UNKNOWN` and out of every group comparison.
- **MET021**, currently labeled a healthy control from the SSVEP side,
  scores noticeably worse than the control average on this independent
  test -- a hint your instinct about them was onto something, even before we
  touch the other two datasets.

![Mean FM100 error profile, +/-1 SD, for HC, protan, deutan, and the two flagged subjects](figures/findings_fm100_groups_radial.png)

*Protan and deutan both balloon out along roughly the same axis (the classic
red-green pattern), well past HC's tight center; deutan's band is the widest
of the four, the FM100 side of the same "deutan is the least
internally-consistent group" story section 2 tells. The flagged pair
(MET047 + MET021) sits between them and HC -- consistent with an elevated
but non-red-green-specific error, exactly why they were flagged as
different-deficiency candidates rather than folded into CVD.*

Three follow-on notebooks firmed this up. `02_group_comparisons.ipynb` ran
the same magnitude/direction features across every group pair: HC vs protan
and HC vs deutan are significant on every magnitude feature (p<0.02, most
p<0.001), and the confusion-ellipse direction (`VKS_Angle`) is significant
for protan (p=0.0066) but not deutan (p=0.32, up from 0.10 before MET048 --
deutan's directions are widely scattered) -- an asymmetry that echoes what section 5 finds in the behavioral/EEG type-axis
story. Protan vs deutan comes back with nothing significant on any FM100
feature (smallest p=0.17), the same underpowered story every protan-vs-deutan
comparison in this project tells at n=9 vs 8. `03_flagged_subjects.ipynb` is just MET020/MET047/MET021 side
by side, in both plot styles, for a closer look at the flagged pair.
`04_hc_vs_pd.ipynb` asked a sharper question: is PD's FM100 profile just
HC's, shifted by a constant? Every magnitude feature differs from HC
(TES p=0.017, PES red-green p=0.009, PES blue-yellow p=0.018, both VKS
radii p<0.02) but `VKS_Angle` doesn't (p=0.84) -- PD's error is bigger, not
differently-directed, the same magnitude-not-direction pattern
`02_group_comparisons.ipynb` already found. There genuinely is a real,
non-zero offset (c=1.04, 95% CI [0.32, 1.81], p=0.003) -- but it only
explains about half of PD's shape (R²=0.50), so "PD = HC + a number" is a
real partial description, not the whole story.

Two more checks (M3) sharpened both of those: correcting the per-feature
comparisons for testing 6 features at once (Holm) is a real, not just
procedural, tightening -- **CTR vs PD loses every feature** (smallest
corrected p is 0.052) and protan vs deutan still has nothing, though HC vs
protan and HC vs deutan both keep 11 of their significant rows. And the
offset finding survives a direct stress test: only one CTR subject
(MET020, already flagged elsewhere in this section) is an outlier on most
of the 6 features, and dropping them barely moves the offset (1.04 to
1.11) or its R² (0.50 to 0.47) -- "PD = HC + a number" isn't riding on one
unusual control.

## 2. Behavioral: what your own clicks say

`beh/notebooks/01_explore.ipynb`, `02_shape_features.ipynb`, `03_centroids.ipynb`

This is where the story gets exciting. The first pass (M1) just compared
each group's average click location, and every comparison came back
significant -- including protan vs. deutan (p=0.0029), which is a *cleaner*
split than the EEG task manages on its own best measure (p=0.33). That
alone was worth noting: a direct behavioral report of "this looks the same
color to me" turns out to be a sharper instrument than the indirect neural
signal, at least for telling the two CVD subtypes apart.

Then M2 asked a better question: instead of just *where* someone's clicks
center, what does the *shape* of their click cloud look like? We fit a line
through each person's clicks (PCA) and measured three things about it: which
way it points, how far the clicks spread along it, and how tight they are
around it. The orientation of that line turned out to be remarkable:

> **`orientation_deg` separates every single protan participant from every
> single deutan participant, perfectly** (p=0.0001, and the effect size is
> literally the maximum possible -- every protan subject's line points one
> way, every deutan subject's points another). That's the single strongest
> finding of the whole project so far, and it has now survived two real
> stress tests in a row: the new deutan participant (MET048) landed on the
> deutan side, taking the perfect separation from 7-vs-8 to 8-vs-8, and the
> newest protan participant (MET049) landed cleanly on the protan side too,
> taking it to 9-vs-8 (that p-value is the smallest possible for the sample
> size each time).

![Every protan and deutan subject's click-cloud orientation, one point each](figures/findings_beh_orientation_separation.png)

*Every subject reduced to two numbers: which way their click cloud points
(x) and how tightly the clicks hug that line (y). The x-axis alone fully
separates the two colors -- no protan point falls to the left of any deutan
point (the largest deutan orientation is about 159 degrees, the smallest
protan one about 170).*

One thing did shift: with 8 deutan subjects, the second shape feature --
how far clicks spread *along* the line (`along_var`) -- now also separates
protan from deutan (p=0.038 with MET048; it was 0.072 with 7 deutan). Adding
MET049 on the protan side moved it slightly the other way (p=0.046, still
under 0.05 but closer to the line), while `perp_var` still doesn't separate
the groups either way (p=0.67). That p-value is uncorrected across the three
features, so treat it as a hint next to orientation's clean result, not a
second finding.

M3 turned this into pictures: plotting each subject's own centroid, and
each group's centroid with error bars, makes the same story visible at a
glance -- protan and deutan's line orientations sit in two completely
separate, tight clusters, while deutan turns out to be the least
internally-consistent group we have (the subject-to-subject spread of where
its clicks land is about 1.7 to 4 times every other group's, and its spread
in how far clicks stretch along the line is the largest as well).

Three more notebooks tested how far that story holds up.
`04_reliability.ipynb` asked whether it's stable session-to-session (HC and
PD only -- CVD is excluded, most protan/deutan subjects have just one
session). For HC, mostly not: of centroid location and the three M2 shape
features, only `centroid_green` clears significance (ICC=0.60, p=0.0013);
`orientation_deg`, `along_var`, `perp_var`, and `centroid_red` don't. That
doesn't undercut M2's headline result -- that used clicks pooled across a
subject's sessions, a more forgiving question -- but it's a real caveat
before trusting any single session's numbers on their own. `05_hc_vs_pd.ipynb`
reran the M1 comparison on HC vs PD specifically (Hotelling p=0.0001,
matching M1; all three shape features individually significant too) and
found something new: PD subjects are significantly less consistent within
a single sitting (Mann-Whitney p=0.023, ~70% more within-session click
scatter than HC, 552 vs 320) -- a specific, confirmed answer to whether
PD's motor symptoms show up as noisier clicking. `06_outlier_rejection.ipynb`
added ellipse-based outlier detection (per-subject and per-group) and ran
it everywhere: flagged fractions come back similar and unremarkable across
every group (10.5%-15.5% of clicks) -- an honest "nothing alarming" result,
not grounds for adding automatic filtering to the pipeline.

## 3. EEG (SSVEP grid): the harder, indirect measure

`ssveps/notebooks/` -- start with `08_cvd_gamut.ipynb`, `09_variance_components.ipynb`,
`10_gain_shape.ipynb`, `11_reliability_outcomes.ipynb`, and `12_pca.ipynb` for the
headline work; `docs/ssvep_summary.md` has the full history including two
real bugs we found and fixed early on (an axis-swap and a permutation
subsampling issue -- worth knowing about if you're ever surprised by an old
number).

The EEG task is where things get harder, because the signal is indirect and
noisier than a button press. What holds up well:

- **CVD vs. healthy controls is a strong, reliable effect.** Whether a
  subject's response "trough" fit runs off the edge of what we sampled
  predicts CVD with 76.5% sensitivity (13 of 17) / 81% specificity (17 of 21),
Fisher exact p=0.0008 (it was 75% and p=0.0010 before MET049, whose trough
also runs off the grid, and 73%/p=0.0019 before MET048).
- **Protan vs. deutan is a stubborn question, and it's still stubborn.** Three
  independent angles on the EEG data -- a shallower response ramp (protan's
  is shallower, p=0.33), a residual pattern right at the trough after
  removing overall response strength (protan lower than deutan), and the
  first principal component of the whole grid (p=0.62) -- still point the
  same direction they did before, but none reaches statistical significance
  at n=9 vs 8, and both quoted numbers are about where they were after MET048
  (PC1 was p=0.092 back at n=7, the closest of the three then). This is
  consistent with, and motivated, the reliability work below.
- **Reliability matters, and it changed our recommendations.** When we
  checked which EEG measures are actually consistent test-to-retest, the
  ramp slope and overall gain of a subject's response turned out to be
  *more* trustworthy (ICC 0.85-0.90) than the measure we'd started with,
  trough depth (0.76) -- and one early candidate measure was so unreliable
  (ICC 0.18) it's not usable at all. Good news buried in this: this is
  exactly the kind of check that keeps us from building a clinical claim on
  a number that just happens to be noisy.

![HC, protan, and deutan mean SSVEP response grids, percent change from baseline](figures/findings_ssveps_gamut_groups.png)

*The same red/green grid as every other figure here, but now the EEG's own
response surface. HC's dip (paler patch) sits centrally, around red ~2100
/ green ~900. Protan's pale band runs right out to the grid's edge instead
of sitting in the middle, and deutan's pale region is more diffuse (spread
across the upper left and along the diagonal) -- the visual version of
"CVD subjects' troughs tend to lie beyond the sampled red range."*

Four more notebooks (`13_hc_vs_pd.ipynb` through `16_grid_shape_features.ipynb`)
pushed further into the CVD subtype question, and one of them is where
MET048 changes the story. `13_hc_vs_pd.ipynb` found HC vs PD not significant
on `ramp_slope_red` (p=0.89) -- consistent with PD being underpowered
everywhere else in this project. `14_hc_vs_subtypes.ipynb` ran the same
measure three ways: HC vs protan (p=0.0015) and HC vs deutan (p=0.041) are
both significant, protan vs deutan still isn't (p=0.48) -- matching M6's
Mann-Whitney number above exactly.

Then `15_permutation_stability.ipynb` reran protan vs deutan 200 times at
independent seeds, using the cluster-based permutation test instead of a
whole-grid scalar summary. With deutan at n=7, that test had found a
corrected-significant cluster in 173-196 of 200 seeds (86.5%-98%) -- a
spatially localized difference in the low-red/high-green corner of the grid,
protan higher than deutan -- and the previous version of this document called
it the most solid subtype signal in the SSVEP data. **With MET048 in, the
same test finds a corrected-significant cluster in 0 of 200 seeds, for all
three test variants.** The leave-one-out check in the section above shows it
is this one participant and not a general loss of power: MET048 responds in
exactly that corner (0.8) as strongly as the strongest protan subjects, versus
0.1-0.3 for the other deutan subjects, so the protan-minus-deutan difference
there mostly vanishes. What we can honestly say now: the localized
protan/deutan EEG difference was statistically significant for those 15
subjects but fragile (its seed-0 p-value was 0.046, just under the line), and
it does not hold at n=8 vs 8, nor at n=9 vs 8 now that MET049 (protan) has
joined -- still 0 of 200 seeds. It goes back to being a lead, not a finding.
The one comparison in this neighborhood that stays solid is deutan vs HC
(`05_permutation_testing.ipynb`): a cluster survives (p=0.007), just smaller
than before (26 grid cells rather than 55; p was 0.002).

Last, `16_grid_shape_features.ipynb` tried a new rotated (tilted) dip model
on top of this, but too few subjects have a valid fit to run the
protan/deutan comparison yet (25% and 38% valid fits, vs 90-100% for HC/PD)
-- the model itself works, the data just isn't there yet.

## 4. Does the EEG test actually agree with what people click?

`ssvepBeh/notebooks/01_explore.ipynb`, then `02_reliability.ipynb`

This is the newest and most carefully-checked piece, because it's the one
that would actually justify using the EEG test clinically. We asked two
different questions, and got two different answers -- which is itself the
finding worth remembering.

**Do clicks land where the EEG response is lowest?** Yes, robustly. We ran
two independently-built statistical tests (deliberately different from each
other, so agreement between them means something), and **every group --
including healthy controls -- shows clicks concentrating significantly
where the EEG signal is weakest.** That's a genuinely nice result: it means
the "metamer" concept the whole stimulator is built around shows up in the
brain data even for people with no diagnosed deficiency, which is exactly
the kind of subtle trend you were hoping to find a hint of. We double-checked
this holds up across repeat EEG sessions too, and it does -- the numbers
from session 1 and session 2 are nearly identical. `04_permutation_stability.ipynb`
pushed that stability check further, rerunning the same test 200 times at
independent seeds for HC, PD, protan, and deutan: **every group stays
significant at every single seed** -- robust to the permutation RNG, not
just to which session you check. `03_clicks_on_grid.ipynb` is the picture
that makes this finding visible at a glance -- the EEG grid as a heatmap
with each participant's actual clicks scattered on top, per subject and
per group, with and without `beh/`'s M4 outlier filter. And
`05_toroidal_shift_explained.ipynb` is a from-scratch, step-by-step
walkthrough of the toroidal-shift null model itself (a synthetic 5x5 grid,
then a real subject) for anyone who wants to understand the test, not just
its output.

![CVD group: EEG response grid next to behavioral click density, same axes](figures/findings_beh_eeg_overlap_cvd.png)

*The CVD group's version of `docs/experiment_summary.md`'s HC figure --
clicks (right) concentrate along the same diagonal band where the EEG
response (left) is weakest, the pattern the spatial-overlap tests confirm
statistically in every group, not just this one.*

**Does a person's EEG-measured severity track their behavioral severity?**
Here's the honest part: at first glance, yes -- your click-line orientation
(the same measure that perfectly splits protan/deutan) correlated with the
EEG's most reliable measures. But when we corrected for the fact that we'd
tested 25 different feature pairs at once, and when we checked whether the
relationship holds up across repeat EEG sessions, **it didn't survive either
check.** Rather than quietly dropping that or overstating it, we wrote up
exactly why (see `docs/ssvepbeh_reliability_gaps.md`): testing 25 separate
pairs instead of the joint pattern likely dilutes the signal, and -- this
is the sharper point -- **we currently have zero participants with deutan
who've done the EEG task twice**, so we can't even check reliability for
the comparison that matters most. That document lays out concrete next
steps (a smarter multivariate test, and how much more repeat-session CVD
data would actually help). MET048 (one session, like every deutan participant
so far) doesn't change that: zero deutan participants have a repeat EEG
session. It also illustrates why the multiple-testing caution matters -- the
strongest-looking click-vs-EEG pair within deutan alone changed from
`beh_red` vs `eeg_green` (r=-0.92, n=7) to a different pair, `beh_red` vs
`eeg_red` (r=0.83, n=8), the moment one participant was added.

## 5. FM100 vs. behavioral and EEG: chasing the continuous severity spectrum

`ssvep_beh_fm100/notebooks/01_fm100_reliability.ipynb`, then `02_fm100_vs_behavioral.ipynb`

This is the project born directly from your own hunch: that FM100's score
isn't just "protan or deutan or neither," but might carry a continuous
severity signal the categorical labels throw away -- and that this signal
should show up in the behavioral data too. We learned from `ssvepBeh/`'s
mistake and built this one differently from the start: instead of testing
every FM100 feature against every behavioral feature (the approach that
diluted itself last time), we picked exactly two pre-specified questions
going in -- does overall error *magnitude* line up (severity), and does
error *direction* line up (type/axis) -- and checked FM100's own test-retest
consistency before leaning on either.

**FM100's severity features are trustworthy; its direction feature is
shakier.** Total error and the confusion-ellipse's size are highly
consistent session-to-session. Which *way* that ellipse points is not
(barely half-reliable) -- worth knowing going in, not discovering after the
fact.

**Severity: a strong signal, but likely a between-group one for now.**
Pooled across everyone (n=49), FM100 error magnitude and your behavioral
spread line up strongly (r=0.73, p=0.0004 -- about as strong a relationship
as this project has found anywhere). But split apart by group, that relationship doesn't hold up on
its own within any single group at our current sample sizes -- most likely
because it's substantially "sicker people score worse on both tests,"
which we already knew, rather than a fine-grained continuum. Not
disproven, just not yet confirmed -- worth revisiting once we have more
participants per group.

**Type/axis: the more exciting result.** FM100's confusion-ellipse
direction and your click-line orientation line up significantly overall
(r=0.41, p=0.0029, n=49), *and* that relationship holds up within the CVD
group on its own (r=0.54, p=0.031, n=17) -- not
just because CVD and healthy participants differ, but because CVD
participants who differ from each other in one measure tend to differ from
each other the same way in the other. That's a genuinely more convincing
kind of evidence for a real, continuous, shared signal, even though it's
riding on FM100's noisier direction feature.

### Then we extended the same two questions to the EEG data

`ssvep_beh_fm100/notebooks/03_eeg_reliability.ipynb`, then `04_fm100_vs_eeg.ipynb`

Same two pre-specified tests, same reused code, now against the EEG
measures (steepness and direction of how the brain response ramps with
red/green) instead of your clicks. **Both EEG results echo the behavioral
ones, just weaker** -- which is itself a consistent, sensible pattern: EEG
has been the noisier, more indirect measure everywhere else in this
project too.

- **Severity** lines up significantly overall (r=0.50, p=0.031, n=46), but
  more weakly than with behavioral data, and (same as before) doesn't hold up
  within any single group at our current sample sizes.
- **Type/axis** also lines up significantly overall (p=0.015, n=46). Within
  groups, only deutan shows a significant relationship (r=0.63, p=0.028,
  n=8) -- it held up when MET048 joined (it was p=0.034 at n=7) and again
  when MET049 (protan) joined, which is encouraging, but at that size it's
  still a lead worth watching, not yet as solid as the behavioral version's
  within-CVD result (n=17).

**Put together, the clearest single result across this entire line of
work is still the behavioral one**: FM100's confusion-ellipse direction
tracking your click-line orientation within the CVD group alone. The EEG
extension confirms the same underlying pattern shows up a second way, just
more faintly -- more evidence for the idea, even if the EEG signal alone
wouldn't have been convincing on its own.

### Then we asked whether all three agree at once, not just two at a time

`ssvep_beh_fm100/notebooks/05_three_way_type_axis.ipynb`

FM100, your clicks, and the EEG each give a "which way does this
deficiency point" reading. We'd tested FM100-vs-clicks and FM100-vs-EEG;
the third pairing -- your clicks directly against the EEG reading, with
FM100 out of the picture -- had never been checked. So we checked it, and
then asked the more interesting question it sets up: do all three agree
*together*, as one combined pattern, even in a case where one of the three
individual pairings comes up empty?

**The third pairing (clicks vs. EEG) doesn't hold up on its own** -- no
real relationship there in isolation (p=0.15, n=45). That could have been a
discouraging result. **But testing all three together anyway, as one combined
question, found a real signal** (p=0.0010) -- FM100, your clicks, and the EEG
do share structure as a group, even though one of the three ways of pairing
them up individually comes up empty. This is honestly the most compelling
piece of evidence in the whole project for your original idea: it's not
resting on one strong measurement that might be a fluke, it's a pattern
that's consistent enough across three completely independent ways of
measuring the same thing that it survives one of them not lining up
directly.

![The three pairwise |circular correlation| values, with the joint concordance statistic marked](figures/findings_three_way_concordance.png)

*FM100-vs-behavioral and FM100-vs-EEG each carry real signal on their own;
behavioral-vs-EEG (right bar) is the weak edge, well below the joint
statistic (dashed line) -- and still doesn't drag the joint test below
significance.*

We also spotted a new, specific lead worth keeping an eye on: within the
protan group alone, that "empty" pairing (clicks vs. EEG) actually *does*
show a significant relationship (r=-0.55, p=0.013, n=9 protan participants --
it held up after MET049 joined; that's still a hint to chase with more data,
not a settled finding yet).

## Where this leaves us

- **Solid and ready to lean on:** behavioral group separation (especially
  click-line orientation for protan/deutan), the CVD-vs-control EEG signal,
  the spatial agreement between clicks and EEG response (now also confirmed
  robust to the permutation seed, not just the session), and FM100's own
  severity features being reliably measured -- plus a real (if partial)
  constant offset between HC's and PD's FM100 profile shape.
- **The protan/deutan EEG split is back to open:** for a while protan and
  deutan's EEG responses looked significantly different in one localized
  region of the grid (a cluster-based test, stable across seeds at n=7 deutan).
  Adding one deutan participant (MET048, a strong EEG responder) erased it --
  0 of 200 seeds -- and dropping only that participant brings it back; adding
  MET049 (protan) afterward left it at 0 of 200 too, so it stays erased.
  Behavior is the reliable place to separate the subtypes (click-line
  orientation, perfectly, now at 9 vs 8); in the EEG, protan vs deutan is
  unresolved at this sample size, and a reminder that a "stable across seeds"
  result can still be one participant away from disappearing.
- **Promising but not yet proven:** whether EEG severity tracks behavioral
  severity person-by-person; whether FM100's or the EEG's severity spectrum
  is a true within-group continuum or mostly a between-group difference we
  already knew about; the EEG version of the type/axis result, currently
  only significant within deutan at n=8 (it survived MET048); the
  protan-specific clicks-vs-EEG lead from M3 (n=9, it survived MET049); the
  rotated-dip shape-feature comparison for protan/deutan, blocked on too few
  valid fits (25%/38% valid). All real, honestly-documented open questions,
  not dead ends.
- **The most convincing result across the whole project:** the three-way
  finding -- FM100, your clicks, and the EEG all agree as a group on which
  way a deficiency points, a pattern robust enough to survive one of the
  three individual pairings coming up empty. Direct evidence for your
  "masked continuous spectrum" idea holding up across three independent
  instruments at once, not just one.
- **Not yet started:** everything in this line of work now comes back to
  sample size -- more CVD/protan/deutan participants would let us actually
  test whether the severity spectrum and the three-way agreement hold up
  *within* a single diagnostic group, and would unblock the rotated-fit
  shape comparison above -- the one recurring bottleneck across every
  piece of this project. MET048 is the clearest illustration so far: one
  participant out of 16 protan/deutan subjects was enough to flip a result
  that looked stable. MET049, right after, is the useful counter-example:
  one more participant, this time on the protan side, moved plenty of
  numbers a little but flipped nothing -- a reminder that both things are
  true at this sample size, a single participant can be decisive or can be
  business as usual, and you often can't tell which in advance.

## Come play

Every number above has a notebook behind it, and every notebook is meant to
be opened, not just read. A few easy ways to push further, if you're in the
mood:

- In any `beh/` or `ssvepBeh/` notebook, swap the `categories`/`sub_ids`
  lists for a different set of participants -- e.g. put MET047 and MET021
  side by side with protan/deutan and see where they fall.
- In `standardizedScores/FM100/notebooks/01_explore.ipynb`, try the
  `window=` smoothing parameter on a few individual participants' error
  profiles and see whose shape changes the most.
- In `ssveps/notebooks/12_pca.ipynb`, the PCA loadings are sitting right
  there as heatmaps -- worth a look even without changing anything.
- In `ssveps/notebooks/15_permutation_stability.ipynb`, add
  `metadata_df = metadata_df[metadata_df.sub_id != 'MET048']` right after
  the data loads and rerun: the old 173-196-of-200 cluster comes back. Then
  try dropping a different deutan subject instead (nothing else brings it
  back) -- a quick way to feel how much one participant can matter at n=8.
- In `beh/notebooks/06_outlier_rejection.ipynb`, try `n_std=1.5` or `2.5`
  instead of the default 2.0 and see how much the flagged fractions move.
- Anywhere you see a `seed=` parameter, changing it re-shuffles the
  permutation test's random draws -- a good way to build intuition for how
  stable a given p-value really is.
- In `ssvep_beh_fm100/notebooks/02_fm100_vs_behavioral.ipynb`,
  `04_fm100_vs_eeg.ipynb`, or `05_three_way_type_axis.ipynb`, the
  `categories` list controls which group breakdowns get tested -- try a
  hand-picked `sub_ids` list (e.g. just protan, or MET047/MET021 again) to
  see if the severity or type/axis relationship looks any different for a
  subset you're curious about.
- `05_three_way_type_axis.ipynb`'s joint test works with any number of
  angle features, not just three -- if you ever add a fourth angle-style
  measurement to this project, `type_axis.joint_concordance_test` is ready
  for it without changes.

Nothing breaks by experimenting -- every notebook reloads its data fresh
from the raw files each time, so there's nothing to accidentally corrupt.
Go see what you find.
