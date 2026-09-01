A side project: a 3-channel (red/green/blue) hue sensor added to the same
grid experiment/optical stimulator used for the SSVEP work, sampled at
~110ms in place of a human participant. Full background:
`hue/hue_sensor_experiment_notes.md`. Code under `/hue`.

## Documents

- `hue/README.md` -- data dictionary and the raw-file Stim-numbering
  quirk (three different baseline-encoding schemes across files,
  normalized in `loader.py`). **Read this first.**
- `hue/hue_sensor_experiment_notes.md` -- the three goals in the
  researcher's own words: characterizing the stimulus, simulating CVD
  optically via filters, relating channel-level brightness to the SSVEP
  responses.
- `docs/experiment_summary.md` -- how the shared stimulus (fixed
  yellow=2400, red 0-3200, green 0-2000) relates to `beh/` and `ssveps/`.

## M1. Exploration only: raw channel data, per-trial aggregation, grid view

- [x] `scripts/loader.py`: `load_filters` (six `filters/{solid,flash}_
  {F,NF,Or}.txt` files) and `load_flashdiff` (nine `flashDiff/flash_*.txt`
  files), each concatenated and tagged with its condition columns.
  Normalizes three different raw Stim-numbering schemes (single baseline
  at 999, six baseline blocks at 1000-1005, or `flash_RGY_1.txt`'s own
  999+1000-1099 scheme) into one consistent `is_baseline`/`grid_index`/
  `baseline_id`. Confirmed every `grid_index` maps to exactly one
  `(Red, Green)` pair, identical across every condition and both
  datasets, matching `ssveps/files/grid.json`'s grid exactly.
- [x] `scripts/plotting.py`: `plot_channel_overview` (every raw sample of
  a condition's core channels, in recording order) and `plot_channel_grid`
  (10x10 heatmap per channel, red on x/green on y, matching `ssveps/`'s
  grid-heatmap convention -- from an already-aggregated table).
- [x] `hue/tests/test_hue.py` -- loader only (shape, columns, the
  Stim-scheme normalization, grid_index consistency). No aggregation
  tests yet -- that method isn't decided.
- [x] **`01_filters_explore.ipynb`** -- raw channel overview per
  flicker/filter condition; single-trial zoom; first per-trial
  aggregation attempt; resulting grid heatmap; a first coarse look at each
  filter's effect. **Real finding, not just plumbing:** a single `Stim`
  block is *not* a clean onset-plateau-offset -- edges are contaminated by
  the neighboring trial. Grid cells aren't presented in raster order
  (`grid_index=55` is `Red=3200, Green=0`; the very next block,
  `grid_index=56`, is `Red=355, Green=2000`, close to the largest jump on
  the grid), and the `Stim` label boundary lands mid-transition, so the
  LED driver's switching overshoot straddles both trials' edges. Documented
  in `hue/README.md`; the aggregation trims both edges of every block, not
  just an initial ramp.
- [x] **`02_flashdiff_explore.ipynb`** -- same raw overview and
  single-trial zoom across all nine `Flash_*` conditions; aggregation and
  grid heatmap for `NN`/`R`/`G`/`RGY`; a repeatability check between the
  two RGY runs. **Findings:** the same boundary contamination shows up
  here too, just as a plain neighbor-value leak rather than an overshoot
  spike (same cause, same fix). Every condition's baseline blocks read a
  strong, consistent `HueR` (~3290) even though their own `Red`/`Green`/
  `Yellow` columns all log `0` -- what baseline actually flashes isn't
  captured by those columns; worth asking about directly. `R`/`G` isolate
  cleanly onto their own grid axis (a clean single-direction gradient
  each), with real but small crosstalk -- green-into-blue looks more
  pronounced than red-into-green/blue. The two RGY runs agree to within a
  few counts on average (worst single-cell disagreement ~120 on `HueR`) --
  a rough repeatability floor to keep in mind before trusting small
  effects out of this aggregation.

**Per-trial aggregation is intentionally not yet in `scripts/`.** Confirmed
working approach from both notebooks: mean over each `Stim` block with
`EDGE_TRIM=3` samples dropped from each end (not just the start) to clear
the neighbor-contaminated edges. Holds up across both filters/ and
flashDiff/ conditions as tested. Next: promote to `scripts/aggregate.py`
with tests, once cross-checked on a condition with smaller neighbor-to-
neighbor jumps too (per `01_filters_explore.ipynb`'s note).

## Open questions from M1 -- resolved

- What does the baseline procedure actually flash? **Resolved:** a
  non-blinking yellow light for 3 seconds at 2400 D/A units. Not
  recording it as a column was a bug in the data logger, not a
  mysterious signal -- no code change needed, `is_baseline`/`baseline_id`
  already isolate those rows.
- Does `EDGE_TRIM=3` hold up on grid cells with smaller neighbor jumps,
  or does it need to scale? **Resolved:** no adaptive scaling -- just a
  bigger fixed trim, 5 samples off each end (grid *and* baseline blocks
  alike), confirmed sufficient without needing a real elapsed-time
  window.

## M2. Windowed aggregation, linear view, additivity exploration -- done

- [x] `hue/scripts/aggregate.py` (new module): `TRIM = 5`;
  `aggregate_trials(df, *, group_cols, channels=CORE_CHANNELS,
  trim=TRIM)` -- one row per `Stim` block (grid or baseline), first/last
  `trim` samples dropped before averaging, replacing the notebook-only
  `EDGE_TRIM=3` prototype from M1. `additivity_prediction(agg, *,
  components, target, offset_multiplier, offset_condition="NN", ...)` --
  per-grid-cell predicted-vs-actual table for the Goal-3 additivity
  hypothesis, joining on `grid_index`; `offset_multiplier` is a free
  parameter (not derived from `len(components)`), since which correction
  actually fits was exactly the open question.
- [x] `hue/scripts/plotting.py`: `plot_channel_trials` -- one panel per
  group, aggregated channel value vs. `grid_index` (trial order), the
  linear counterpart to `plot_channel_grid`'s heatmap; `show_baseline`
  (default `False`) adds baseline blocks as markers past the grid trials.
- [x] `hue/tests/test_hue.py`: trim-math correctness (synthetic block),
  one-row-per-block/baseline-included, constant-column carry-through,
  `additivity_prediction`'s formula, `plot_channel_trials` panel/marker
  counts. 250/250 full-suite pass, no regressions.
- [x] **`03_additivity_explore.ipynb`** -- tested the working hypothesis
  from `hue_sensor_experiment_notes.md` against real data. **Finding:** a
  flat `-NN` correction badly fails for the three-way sum
  (`RGY ~ R+G+Y`, mean |residual| 340-460 counts, all three channels
  uniformly offset above the diagonal) -- but `-2*NN` (the `(k-1)`
  scaling floated during brainstorming: each extra summed condition adds
  one more copy of the shared NN offset) drops that to 9-18 counts,
  in line with the two-component models (`GY~G+Y`, `RY~R+Y`, `RG~R+G`,
  each 4-29 counts) and with `02_flashdiff_explore.ipynb`'s own
  RGY-repeatability floor (mean |diff| 3-19, worst cell ~120). The three
  named `RGY` decompositions (`R+G+Y`, `RG+Y`, `RY+G`, each with its
  correct multiplier) land in the same 9-30 count band as each other --
  real support for additivity-with-offset-scaling, not just one
  privileged grouping. **Real finding, not just plumbing.**

## M3. Per-trial agreement plots -- done

- [x] `hue/scripts/plotting.py`: `plot_prediction_trials(pred, *,
  channels=CORE_CHANNELS, title="")` -- one panel per channel, from
  `aggregate.additivity_prediction`'s output, actual condition in that
  channel's own color (solid) vs. predicted/combined value in black
  (dashed), both against `grid_index` (trial order). Test added
  (panel count, actual+predicted line count, predicted line is black).
- [x] `03_additivity_explore.ipynb`: the four primary combinations
  (`GY~G+Y`, `RY~R+Y`, `RG~R+G`, each `offset_multiplier=1`; `RGY~R+G+Y`,
  `offset_multiplier=2`) plotted this way. **Finding:** predicted tracks
  actual's sawtooth shape trial-by-trial across the *entire* grid
  sequence, not just on average -- every peak/trough in the non-raster
  grid ordering is reproduced. Remaining daylight is small, consistent
  jitter (a few percent of each channel's own range), proportionally
  largest on the least-flashed channel per condition (e.g. `GY`'s `HueR`,
  small dynamic range ~1800-2020) -- matching the residual-size pattern
  from M2, not a new problem. Strongest evidence yet for additivity:
  agreement holds across the whole grid, not just in aggregate.
- [x] Remaining candidates plotted the same way: the flat `-NN`
  `RGY~R+G+Y` failure case, and the two alternate decompositions
  (`RG+Y`, `RY+G`). **Finding:** the flat-offset failure is a clean
  constant shift, not a shape mismatch -- predicted reproduces actual's
  exact sawtooth the whole way across the grid, just uniformly high by
  one under-subtracted `NN` copy, confirming it's an offset error, not a
  broken model. Both alternate decompositions track actual as tightly as
  `R+G+Y, x2` across the full sequence -- no decomposition is
  distinguishable from the others by eye, reinforcing that this is
  genuine additivity rather than one privileged grouping.

## Next milestones

To be defined together -- likely candidates: does the same `(k-1)*NN`
rule hold for `filters/`'s conditions too (not just `flashDiff/`); does a
per-channel `offset_multiplier` fit better than one shared value; the
alternate `RGY` decompositions (`RG+Y`, `RY+G`) plotted the same way; or
relating the now-validated additive model to `ssveps/`'s own response
grids per Goal 3.
