# Findings so far

Hi! This is a guided tour of everything we've learned from the color-vision
data so far, across all four ways we've looked at it. Nothing here is final
-- the point of this document is to give you a readable map of where things
stand today, with a direct link to the notebook behind every claim, so you
can open any of them, poke at the parameters, and push the story further
yourself. Treat every number below as an invitation to go check it in
context, not a conclusion to take on faith.

For the experimental background (what the stimulus is, why we're comparing
these particular measures), see `docs/experiment_summary.md`. This document
assumes that context and focuses on what we've actually found.

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
real test sessions. **Every score matched bit-for-bit.** That's the kind of
boring-but-essential check that makes everything downstream trustworthy.

With that settled, the scores tell a clean, expected story: protan and
deutan participants both show the classic signature of a red-green
deficiency (their error concentrates on the red-green axis of the test, not
the blue-yellow axis). Two participants stood out as genuinely interesting
edge cases rather than noise:

- **MET047**, new to this project (no SSVEP or behavioral data yet), has a
  total error score about as high as our CVD group's average -- but unlike
  protan/deutan, their errors are *evenly* split between the red-green and
  blue-yellow axes. That's not the usual pattern, which is exactly why you
  flagged them as worth a closer look for a different kind of deficiency.
- **MET021**, currently labeled a healthy control from the SSVEP side,
  scores noticeably worse than the control average on this independent
  test -- a hint your instinct about them was onto something, even before we
  touch the other two datasets.

## 2. Behavioral: what your own clicks say

`beh/notebooks/01_explore.ipynb`, `02_shape_features.ipynb`, `03_centroids.ipynb`

This is where the story gets exciting. The first pass (M1) just compared
each group's average click location, and every comparison came back
significant -- including protan vs. deutan (p=0.0042), which is a *cleaner*
split than the EEG task manages on its own best measure (p=0.44). That
alone was worth noting: a direct behavioral report of "this looks the same
color to me" turns out to be a sharper instrument than the indirect neural
signal, at least for telling the two CVD subtypes apart.

Then M2 asked a better question: instead of just *where* someone's clicks
center, what does the *shape* of their click cloud look like? We fit a line
through each person's clicks (PCA) and measured three things about it: which
way it points, how far the clicks spread along it, and how tight they are
around it. The orientation of that line turned out to be remarkable:

> **`orientation_deg` separates every single protan participant from every
> single deutan participant, perfectly** (p=0.0003, and the effect size is
> literally the maximum possible -- every protan subject's line points one
> way, every deutan subject's points another). That's the single strongest
> finding of the whole project so far.

M3 turned this into pictures: plotting each subject's own centroid, and
each group's centroid with error bars, makes the same story visible at a
glance -- protan and deutan's line orientations sit in two completely
separate, tight clusters, while deutan turns out to be the least
internally-consistent group we have (its subject-to-subject spread is
roughly double every other group's, on both the raw clicks and the shape
features).

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
  predicts CVD with 73% sensitivity / 81% specificity (p=0.0019).
- **Protan vs. deutan is a real but stubborn question.** Three independent
  angles on the EEG data -- a shallower response ramp, a residual pattern
  right at the trough after removing overall response strength, and the
  first principal component of the whole grid -- all point the same
  direction, but none individually reaches statistical significance at our
  current sample size (n=7-8 per subtype). This is consistent with, and
  motivated, the reliability work below.
- **Reliability matters, and it changed our recommendations.** When we
  checked which EEG measures are actually consistent test-to-retest, the
  ramp slope and overall gain of a subject's response turned out to be
  *more* trustworthy (ICC 0.85-0.90) than the measure we'd started with,
  trough depth (0.76) -- and one early candidate measure was so unreliable
  (ICC 0.18) it's not usable at all. Good news buried in this: this is
  exactly the kind of check that keeps us from building a clinical claim on
  a number that just happens to be noisy.

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
from session 1 and session 2 are nearly identical.

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
data would actually help).

## 5. FM100 vs. behavioral: chasing the continuous severity spectrum

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
Pooled across everyone, FM100 error magnitude and your behavioral spread
line up strongly (about as strong a relationship as this project has found
anywhere). But split apart by group, that relationship doesn't hold up on
its own within any single group at our current sample sizes -- most likely
because it's substantially "sicker people score worse on both tests,"
which we already knew, rather than a fine-grained continuum. Not
disproven, just not yet confirmed -- worth revisiting once we have more
participants per group.

**Type/axis: the more exciting result.** FM100's confusion-ellipse
direction and your click-line orientation line up significantly overall,
*and* that relationship holds up within the CVD group on its own -- not
just because CVD and healthy participants differ, but because CVD
participants who differ from each other in one measure tend to differ from
each other the same way in the other. That's a genuinely more convincing
kind of evidence for a real, continuous, shared signal, even though it's
riding on FM100's noisier direction feature.

## Where this leaves us

- **Solid and ready to lean on:** behavioral group separation (especially
  click-line orientation for protan/deutan), the CVD-vs-control EEG signal,
  the spatial agreement between clicks and EEG response, and (new) FM100's
  own severity features being reliably measured.
- **Promising but not yet proven:** whether EEG severity tracks behavioral
  severity person-by-person; whether FM100's severity spectrum is a true
  within-group continuum or mostly a between-group difference we already
  knew about. Both are real, honestly-documented open questions, not dead
  ends.
- **The more convincing new result:** FM100's confusion-ellipse direction
  and your behavioral click-line orientation track each other even within
  the CVD group alone -- the clearest evidence so far for your "masked
  continuous spectrum" idea.
- **Not yet started:** extending this same FM100 comparison to the EEG
  data (`PLANssvep_bh_fm100.md`'s M2).

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
- Anywhere you see a `seed=` parameter, changing it re-shuffles the
  permutation test's random draws -- a good way to build intuition for how
  stable a given p-value really is.
- In `ssvep_beh_fm100/notebooks/02_fm100_vs_behavioral.ipynb`, the
  `categories` list controls which group breakdowns get tested -- try a
  hand-picked `sub_ids` list (e.g. just protan, or MET047/MET021 again) to
  see if the severity or type/axis relationship looks any different for a
  subset you're curious about.

Nothing breaks by experimenting -- every notebook reloads its data fresh
from the raw files each time, so there's nothing to accidentally corrupt.
Go see what you find.
