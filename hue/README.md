# Hue sensor (multichannel bench characterization)

A 3-channel (red/green/blue) brightness sensor placed on the same optical
stimulator `ssveps/` and `beh/` use, in place of a human participant --
characterizing the stimulus itself, simulating CVD optically via filters,
and isolating which LED channel(s) drive a given reading. Full background:
`hue_sensor_experiment_notes.md`. Plan and milestone status:
`../PLANhue.md`.

No `sub_id`/session -- this is instrument characterization data, not
participant data. See `docs/experiment_summary.md` for how the shared
stimulus (fixed yellow=2400, red 0-3200, green 0-2000) relates to `beh/`
and `ssveps/`.

Raw data: `/home/sebas/data/hue/grid/{filters,flashDiff}/*.txt` (read in
place, not copied into the repo), tab-separated, one row per ~110ms
sensor sample.

## Fields (tidy tables, as loaded by `loader.load_filters`/`load_flashdiff`)

Raw columns, unchanged: `Stim`, `HueR`, `HueG`, `HueB` (the three sensor
channels), `HueC` (clear/unfiltered channel), `HueCT` (color temperature),
`HueLux`, `Yellow`/`Red`/`Green` (the stimulus D/A values actually driving
the LEDs at that sample), `Trig`.

Derived:

- `sample_idx` -- row order within one `(file, Stim)` block (no timestamp
  column exists; sampling is ~110ms).
- `is_baseline` -- whether this `Stim` is a baseline/reference reading
  rather than a grid cell. The baseline procedure shows a non-blinking
  yellow light for 3 seconds at 2400 D/A units -- not recorded in
  `Yellow`/`Red`/`Green` (those all log `0` on baseline rows) due to a
  data-logger bug, not a mystery signal; `HueR`'s strong, consistent
  ~3290 reading during baseline is that yellow light.
- `grid_index` -- `1`-`100` for grid rows (`NA` for baseline rows). Maps
  1:1 to a `(Red, Green)` pair, confirmed identical across every
  condition and both `filters/` and `flashDiff/`
  (`tests/test_hue.py::test_grid_index_maps_to_one_consistent_red_green_pair`).
- `baseline_id` -- which baseline block a baseline row belongs to (`NA`
  for grid rows).

**Raw-file quirk: three different Stim-numbering schemes, normalized
here.** `filters/*.txt` use `Stim` 1-100 for the grid plus one longer
single baseline block at `Stim=999`. Most `flashDiff/flash_*.txt` files
use `Stim` 1-100 for the grid plus **six** baseline blocks at `Stim`
1000-1005 (`baseline_id = Stim - 1000`). `flash_RGY_1.txt` -- a second RGY
run -- was logged with `filters/`'s single-baseline convention instead:
`Stim=999` is the one baseline reading, `Stim` 1000-1099 is the grid,
offset by 999 (`grid_index = Stim - 999`). All three collapse to the same
`is_baseline`/`grid_index`/`baseline_id` columns, so downstream code
never needs to know which raw scheme a given file used.

`Red`/`Green` on grid rows are the same 10x10 grid `ssveps/files/grid.json`
defines (`redArray`/`greenArray`, int-truncated); `Yellow` is a constant
`2400` on the rows where the yellow LED is on, `0` otherwise -- the same
fixed yellow reference `beh/`'s manual-match task asks participants to
match (`docs/experiment_summary.md`).

**Grid cells are not presented in raster order, and trial boundaries
overshoot.** Within a file, `Stim` 1-100 appears in simple sequential
order (1, 2, 3, ..., 100), but consecutive `Stim` numbers do *not*
correspond to nearby `(Red, Green)` cells -- e.g. in `filters/flash_NF.txt`,
`Stim=55` is `(Red=3200, Green=0)` and the very next block, `Stim=56`, is
`(Red=355, Green=2000)`, close to the largest possible jump on the grid.
Switching between very different stimuli visibly overshoots (a brief spike
well above either cell's own steady value), and the `Stim` label boundary
falls in the middle of that transient rather than after it settles -- so
both the last few samples of the outgoing trial *and* the first few of the
incoming one are contaminated, not just one edge. See
`notebooks/01_filters_explore.ipynb`'s "One trial, up close" section for
the raw numbers. Any per-trial aggregation needs to trim both edges of a
`Stim` block, not just skip an initial onset ramp.

## Scripts

- `scripts/loader.py` -- `load_filters`, `load_flashdiff` (see Fields
  above for what each does to the raw Stim-numbering quirk).
- `scripts/plotting.py` -- `plot_channel_overview` (every raw sample of a
  condition's core channels, in recording order -- see one trial's
  onset-transient-then-plateau shape by slicing to one `Stim` first),
  `plot_channel_trials` (aggregated channel value vs. `grid_index`, one
  panel per group -- the linear counterpart to the grid heatmap), and
  `plot_channel_grid` (a 10x10 heatmap per channel, red on x/green on y
  matching `ssveps/`'s own grid-heatmap convention, from an
  already-aggregated one-row-per-grid-cell table).
- `scripts/aggregate.py` -- `aggregate_trials` (mean per channel per
  `Stim` block, first/last `TRIM=5` samples dropped from each end to
  clear the neighbor-contaminated edges above) and
  `additivity_prediction` (per-grid-cell predicted-vs-actual comparison
  for the Goal-3 additivity hypothesis in
  `hue_sensor_experiment_notes.md`, `NN` as the environmental offset --
  see `../PLANhue.md` M2 for the confirmed `offset_multiplier`).

## Tests

`uv run pytest hue/tests -q`. Same module-naming-collision defense as
every other project's test file (see `beh/README.md`'s Tests section) --
`loader`/`plotting`/`aggregate` dropped from `sys.modules` before import.

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- `01_filters_explore.ipynb` -- M1: `load_filters`; raw channel overview
  per flicker/filter condition; one trial's onset/plateau shape; a first
  per-trial aggregation attempt; the resulting grid heatmap.
- `02_flashdiff_explore.ipynb` -- M1: `load_flashdiff`; the same raw
  overview and single-trial zoom across all nine `Flash_*` conditions;
  aggregation and grid heatmap per condition, to compare which channel(s)
  respond where.
- `03_additivity_explore.ipynb` -- M2: `aggregate_trials`/
  `additivity_prediction` against the working additivity hypothesis --
  which offset correction and which `RGY` decomposition actually fit; see
  `../PLANhue.md` M2 for the finding.
