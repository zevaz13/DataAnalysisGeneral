# Blue/red linear (BRtest): first-insight analysis design

Date: 2026-11-12. Plan/checklist lives in `PLANblueredLinear.md`.

## Intent

Pilot test of blue perception with SSVEPs. Blue (0-1700 DAC, 11 steps of
170) flickers at 10 Hz against fixed red (1800 DAC), with and without a
yellow filter (YF) that blocks blue. The sample is small (6 older adults,
all labeled CTR, 5 with two sessions about a week apart) and still growing.
We want the most defensible early insights, and an analysis that just
re-runs as new files arrive.

## Data (as it exists)

- `/home/sebas/data/blueRedLinear/BRtest/MET0xx[b].mat`, read in place with
  `loadmat(..., squeeze_me=True, struct_as_record=False)["testData"]`.
  `b` suffix = session 2. Participants: every `.mat` in the folder.
- Six runs per file, in recording order: `base_NF` (8 trials, red vs blue 0),
  `BR_NF_1`, `BR_NF_2`, `base_YF`, `BR_YF_1`, `BR_YF_2`. BR runs:
  `baselines` = 2 leading non-flickering red trials, `runData` = 11 steps,
  blue = `np.linspace(0, 1700, 11)`.
- Each value is an FBCCA score on a 3 s epoch (weighted sum of sub-band
  canonical correlations). Not an amplitude: it has a non-zero chance floor
  (~0.6-0.8 on non-flicker trials) and saturates.
- Known anomaly: `MET052` `BR_YF_2` has 10 steps (12 raw samples); which
  blue step is missing is unknown.
- FM100: `standardizedScores/FM100/scripts` (`loader.load_fm100_raw`,
  `scores.build_scores`) gives `PES_BY` per (sub_id, session). All current
  BRtest sessions are covered. FM100 shows a practice effect (session 2
  tends to be better).

## Normalization

Updated 2026-11-12 (user decision): `norm = trial / baseline`, baseline =
median (switchable to mean via `BASE_STAT`) of that participant x session x
filter's 8-trial base run. NF uses `base_NF`, YF uses `base_YF`. The floor
(mean of the 4 leading non-flicker trials) is plotted for reference only.

## Goals

1. **Main: does the NF vs YF difference track FM100 blue-yellow?**
   Hypothesis: with intact blue vision the NF curve dips below the red
   baseline near luminance match while YF stays flat near it, so NF - YF
   is negative; with blue deficits the two curves converge (NF - YF -> 0).
   Expected: mean NF - YF more negative with better vision, i.e. a
   positive Spearman rho with `PES_BY` (higher = worse). One-sided
   expectation, two-sided test reported.
   Update after first run: the data show NF above YF (gap > 0), so the
   "converge with deficit" idea predicts a *negative* rho (gap shrinks as
   PES_BY rises). Read the sign accordingly.
   - Primary feature per session: mean over the 11 steps of
     (NF - YF), each filter's curve averaged over its 2 reps.
   - Also explore the two ends (low-blue steps 0-340 and high-blue steps
     1360-1700, 3 steps each -- builder's call on exact width) and a
     per-step profile: Spearman rho of the per-step NF-YF difference vs
     `PES_BY` across sessions, plotted against blue level. User suspects
     something may show up away from the average; this is exploratory and
     labeled as such.
   - Plot feature vs `PES_BY`, one point per session, lines joining a
     participant's two sessions. Spearman over sessions, plus a
     one-point-per-participant version (session mean) so the result
     doesn't rest on treating sessions as independent.
   - Pairing is within session (session-k SSVEP with session-k FM100).
2. **Is the minimum at or around 1360 (luminance-matched blue)?**
   - Pooled normalized NF curve across sessions with bootstrap CIs
     (resample participants, not trials).
   - Direct contrast: value at 1360 vs mean of the two ends (0, 1700),
     bootstrapped. Per-session argmin shown descriptively only (too noisy
     to trust individually). Same for YF as a reference.
3. **Later (raw EEG pending): improve SNR at the source.** Separate plan
   when the user brings the raw EEG (format/montage/rate TBD). Reproduce
   the FBCCA scores, then compare alternatives (sub-band/harmonic/channel
   choices, TRCA, spatial filter learned on the 8-trial baselines) on one
   yardstick: separation of flicker trials from the non-flicker floor.
   Artifact handling: ICA has been unreliable (blinks not separated);
   evaluate simpler options (epoch rejection/thresholds, EOG/frontal
   regression) and measure whether blinks even affect the 10 Hz score.

Secondary, light-touch: session 1 vs session 2 scatter of the Goal 1
feature and of `PES_BY`, plus session-2-minus-session-1 for both, to
separate real change from FM100 practice effect. No ICC yet.

## Non-goals

- No group comparisons (no CVD group in this dataset yet).
- No formal ICC, no multiple-comparison claims on the exploratory per-step
  profile.
- No EEG reprocessing until Goal 3.

## Anti-goals

- Claiming a per-person minimum location from 2 noisy reps.
- Treating 11 sessions as 11 independent people without the per-participant
  check.

## Constraints

- `uv` only. Keep it simple, no persisted intermediates; read in place.
- One notebook: `blueredLinear/notebooks/04_brtest_fm100.ipynb`
  (existing 01-03 untouched). It imports FM100 loader/scores via
  `sys.path`. Small helpers inline unless they get reused.
- Participant list built by globbing the BRtest folder.

## Left to the builder

- MET052 `BR_YF_2` handling: exclude that run from that session's YF mean
  (use rep 1 only) rather than guess the missing step -- builder's call,
  noted in the notebook.
- Exact end-window width, bootstrap iteration count, plot styling (follow
  `dataviz` guidance and existing notebook colors: NF gray, YF goldenrod).
