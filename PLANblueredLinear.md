Blue/red linear experiment. Data: `/home/sebas/data/blueRedLinear/`
(`blueExpdataStruct_06OCT26.mat`, `expRun_06_oct_26.xlsx`). Code under
`/blueredLinear`.

## Data

`blueExpdataStruct_06OCT26.mat` (pre-v7.3, read with `scipy.io.loadmat`)
holds one variable, `testData`: a 1x12 cell array of 1x1 structs.

- `name`: run name (matches `FileName` in the xlsx)
- `rawData`: Nx1 samples
- `typeRun`: 1 = blue/red run (16 samples), 2 = baseline run (10 samples)
- `baselines` (type 1 only): 1x4, samples 1, 2, 15, 16 of `rawData`
- `runData`: the remaining samples (12 for type 1, all 10 for type 2)

Runs: `BR_{NF,YF}_{1,2}`, `BR_LO_{NF,YF}_{1,2}`, `base_{NF,YF}`,
`base_LO_{NF,YF}`.

## Data explanation and hypotheses. 
- This is a pilot experiment to assess the participants ability to see blue light (related to blue color perception), using ssveps. The stimulus mechanism is similar to that of the ssveps notebooks in this project. However, the stimulus changes only in one dimension (linearly, instead of as a 2D grid).
- Conditions are presented with and without the use of a yellow filter that blocks blue light. See /light_meter/notebooks/01_comare.ipynb. It blocks blue light, while minimally affecting the red light. These changes are to be measured more formally. 
- Each participant performed the following runs of the linear Blue-red experiment, in the following order (aware of ordering effects, but did it this way because of small sample size): 
    1. red baseline no filter. 
    2. red blue no filter run 1. 
    3. red blue no filter run 2. 
    4. red baseline with yellow filter. 
    5. red blue with yellow filter run 1. 
    6. red blue with yellow filter run 1. 
- These experiments only apply to participants starting latter than MET050 and less than MET099.
- The goal is to have all participants come to the lab for 2 sessions. The experiment is repeated exactly in the same condition, about one week apart. We wonder if whatever results we get is repeatable. This is measuring ICCs for features, and plotting curves between sessions for the different participants. 
- The stimulus for the experiment are the following:
  - The red color is set up at 1800 DA units in the visual stimulator. The stimulus always flicker against this color.
  - Blue light is blinked against the red color (at 1800 DA units), at 10 Hz. Blue amount changes linearly in 11 steps between 0 and 1700. Blue = [0 170 340 510 680 850 1020 1190 1360 1530 1700]
  - Stimulus duration is 3 seconds. That is 3 seconds of stimulation blinking between current blue vs. red color (at 1800 DA), after that there is a 750 ms inter stimulus gap. 
  - Blue at 1360 DA units is the closest measured luminance to red at 1800 DA units (this was measured and presented in /light_meter/notebooks/ 02_stim_fitting). The brigtness measured with the light meter is pretty much the same.
- During the red baseline no filter and with yellow filter runs. The participant is presented with 8 stimulus of blue = 0 DA units, vs red = 1800 DA units. This is to quantify with certainty the ssvep size to the higest contrast in the red dimension. Said in other workds, these are 8 trials of red flickering against nothing. 
- During the red blue no filter and with yellow filter runs, the participant sees initially 2x 3 second trials of red no blinking at 1800 DA units, this is similar to what we do in the grid experiments, there we present 2 yellows at the start. These first stimulus dont flicker. Then the experiment proceeds linearly with blue changing every new trial. 
- There is a repetition of the red blue linear experiment for both conditions, introduced withe the idea of increasing the signal to noise ratio, by having 2 measurements of the ssveep at each blue setting.
- We seek to quantify how the SSVEP size changes as a function of blue setting. Blue changes against red at 1800 DA units. 
- We introduced the yellow filter as a ground condition. Since we know it blocks blue light, participants that already have a blue color vision deficiency should show less of a difference between the no filter and the yellow filter conditions. On the other hand, participants without Blue color vision deficiency, should show a marked relationship between the no filter and yellow filter conditions. For them, the yellow filter condition should look like the red no filter baseline value. Effectively this is red flickering at 1800 DA (although minimally affected by the filter) flickering against a blue filtered light, almost totally removed. 
- I believe that the minimal value for the ssveps in the blue red linear conditions should be when blue is 1360 DA units. My hypohteses in these experiments is that the ssvep size is a measure of contrast between the colors (current setting of blue vs red at 1800). Since the difference in brightness is minimal between blue = 1360 DAU and red = 1800DAU , the ssvep should be mnimal at this setting. This point could also indicate of blue perception deficits, for participants that dont see blue as well, it might change.  
- There should be a relationship between the results of this test and the results of the FM100. Especially compared to the Blue-yellow subscore.

## Plan (2026-11-12)

Design: `docs/superpowers/specs/2026-11-12-blueredlinear-brtest-design.md`. Findings: `docs/blueRedLinearFindings.md` (update after each new batch of data).
Notebook: `blueredLinear/notebooks/04_brtest_fm100.ipynb`. Earlier
exploration (01-03) stays as is.

### M1. NF vs YF against FM100 blue-yellow (main)
- [x] Floor-subtracted scores (floor = leading non-flicker trials), 0-1 normalized as secondary
- [x] Per-session mean NF - YF over 11 steps vs `PES_BY` (per session + per participant)
- [x] Low-blue and high-blue end windows, per-step rho profile (exploratory)

### M2. Is the minimum at ~1360?
- [x] Pooled NF (and YF) curves, participant-level bootstrap CIs
- [x] Contrast: 1360 vs ends (0, 1700)

### M3. Session repeatability (light)
- [x] Session 1 vs 2 for M1 feature and `PES_BY`; differences vs FM100 practice effect
- [x] ICC(A,1) per blue step (NF, YF) and per feature

### M4. EEG reprocessing (waiting on raw EEG)
- [ ] Reproduce FBCCA scores from 3 s epochs
- [ ] Compare SNR options (bands/harmonics/channels, TRCA, baseline-learned spatial filter)
- [ ] Artifact handling without ICA (epoch rejection, EOG regression); test blink impact on the 10 Hz score

Open: MET052 `BR_YF_2` has 10 steps (unknown which); session 1 YF uses rep 1 only.

### Findings so far (n = 6 participants, 11 sessions; updated 2026-11-12)
Normalization: score / median of the 8-trial baseline (same filter). Floor is reference only.
- NF sits above YF almost everywhere. The YF curve (relative to its own baseline) carries most of the FM100 relation: better PES_BY -> YF drops more at high blue. YF mean/high vs PES_BY: rho +0.59/+0.58 over sessions (p ~0.06), +0.83 over participants (p = 0.04). NF - YF gap: rho ~ -0.55 (p 0.06-0.09). Uncorrected, many tests; a lead, not a result.
- Dropping MET050 barely changes YF high (+0.62) or gap high (-0.60).
- No dip at 1360 under NF: 1360 is above the mean of the ends (+0.06, 95% CI [+0.04, +0.09]). The YF curve is what drops at high blue.
- Mean vs median baseline: per-condition differences < 0.08; correlations move by at most ~0.15 (median reported).
- Anchor: blue = 0 step falls inside the baseline min-max in 38/43 reps, but sits in the lower half of the baseline trials more often than not.
- Lead: NF curve shape repeats better across sessions than YF (mean s1-vs-s2 rho 0.23 vs -0.07); level differences are similar (mean |s1 - s2| 0.107 vs 0.109).
- Rep 1 vs rep 2 agreement per step is weak.
- ICC(A,1), n = 5: YF mean 0.84 [0.20, 0.98], YF low 0.80, YF high 0.58, NF high 0.53, NF mean 0.05, gap ~0, PES_BY 0.50. YF is the most repeatable measure. NF low is meaningless: blue 0-340 under NF is nearly the baseline stimulus, so norm ~1 for everyone and there is no between-person spread to repeat.
- Lead: pooled YF (normalized) shows two dips, ~510 and ~1360; NF is flatter.
