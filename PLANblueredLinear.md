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

## M1. Load and explore

- [x] `notebooks/01_explore.ipynb`: load the .mat into a dict of runs,
  summary table, dropdown to pick a run and plot `rawData` with the
  baseline/run samples highlighted
- [ ] Decide what the values represent and which comparisons matter
  (NF vs YF, LO vs not)
- [ ] Decide on intermediate data handling (none so far)

## M2. Frequency comparison (10 vs 20 Hz)

Data: `/home/sebas/data/blueRedLinear/BRfreq/` (`blueRed_14OCT26.mat`,
`BRexp_14_10_26.xlsx`). 14 runs, `typeRun` in fixed / linear / grid. Linear
runs share a name, so key by xlsx `RunNumber`. Grid `sequence` is 1-based
(red, green) indices; `matrix[red, green]` matches `runData`.

- [x] `notebooks/02_freq_explore.ipynb`: summary, fixed, linear, grid
  (presentation order, per-green lines, raw heatmap; x red, y green)
- [ ] Compare 10 vs 20 Hz in the grid (baseline normalization, difference map)

## M3. NF vs YF test (BRtest)

Data: `/home/sebas/data/blueRedLinear/BRtest/MET0xx.mat` (same `testData`
format). Per participant: `base_{NF,YF}` (8 trials), `BR_{NF,YF}_{1,2}` (2
leading baseline samples + 11 steps). Steps are blue DAC 0-1700 (linear)
against fixed red 1800. MET050, MET051: CTR. Hypothesis: blue-deficient
participants show YF ~ NF, controls separate.

- [x] `notebooks/03_brtest_explore.ipynb`: raw BR curves, normalised to
  8-trial base mean (per filter), normalised to leading baselines, NF-YF
  difference
- [ ] Decide on a per-participant NF-vs-YF summary number
- [ ] Add participants as they come in (list `PARTICIPANTS` in the notebook)
