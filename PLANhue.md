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

## Open questions from M1, worth resolving before the next milestone

- What does the baseline procedure actually flash? Its `Red`/`Green`/
  `Yellow` columns all log `0`, but `HueR` reads a strong, consistent
  ~3290 during it -- best asked directly rather than reverse-engineered.
- Does `EDGE_TRIM=3` hold up on grid cells with smaller neighbor-to-
  neighbor jumps than the `55`/`56` example, or does it need to scale with
  how different the neighboring `Stim`'s value is?

## Next milestones

To be defined together, once the above is resolved -- likely the goal-3
additivity hypothesis in `hue_sensor_experiment_notes.md`, or relating
aggregated grid values to `ssveps/`'s own response grids.
