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
Open: decide whether MET055b's YF features (interpolated) join the main analyses.
Open: MET055b, MET056, MET056b and MET057 (all 14-step runs) show the lowest NF at high blue; check for a setup change.

Blue grid change: from MET056 on, BR runs have 14 steps of 170 over 0-2210
(first 11 = old 0-1700 grid). MET055b is a setup error: 14 steps over 0-1700
(upper limit not raised), off the common grid. `04` plots it at its true
levels, excludes it from step-aligned/window analyses, and assesses it in its
last section. Cross-session analyses use the common 0-1700 grid.

### Findings so far (n = 8 participants, 14 on-grid sessions + MET055b, 6 on-grid pairs; updated 2026-11-25)
Normalization: score / median of the 8-trial baseline (same filter). Floor is reference only.
Detail and before/after numbers: `docs/blueRedLinearFindings.md`.
- NF sits above YF almost everywhere. The FM100 relation that lived in the YF curve is gone with MET056b: YF high vs PES_BY +0.36 over sessions (p = 0.21; was +0.58, p = 0.037), +0.31 over participants (p = 0.46). Gap high -0.15 (p = 0.61). Nothing significant now.
- MET056b (PES_BY 22): NF below baseline at every step again (high 0.79; MET056's two sessions are the two lowest), YF above baseline at high blue (1.19, highest of all), gap -0.39 (lowest). Low YF baseline that day (0.96 vs 1.14).
- All four 14-step sessions (MET055b, MET056, MET056b, MET057) have the lowest NF at high blue. MET056 repeats it a week apart, but it is still confounded with the setup change.
- No dip at 1360 under NF (+0.04, 95% CI [+0.01, +0.07]). YF: -0.08 [-0.15, -0.01].
- Anchor: blue = 0 step inside the baseline min-max in 50/59 reps, lower half more often than not.
- ICC(A,1), n = 6: NF high 0.77, YF low 0.83, YF mean 0.71, NF mean 0.58, gap 0.38-0.66, YF high 0.26, PES_BY 0.71 (n = 7). MET056 as the sixth pair moved most ICCs (n = 5: YF mean 0.84, NF high 0.53, YF high 0.58).
- 1870-2210 steps: MET056 s1 vs s2 close (NF 0.82/0.97/0.82 vs 0.79/0.90/0.80).
- NF curve shape repeats better than YF (mean s1-vs-s2 rho 0.15 vs -0.10). Rep 1 vs rep 2 agreement per step is weak.
