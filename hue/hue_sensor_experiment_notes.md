# Multichannel Hue Sensor Side Project — Experiment Notes

## Overview

As a side project, I added a simple 3-channel hue (RGB brightness) sensor to the same grid experiment I use for my SSVEP (steady-state visual evoked potential) work, using the identical optical stimulator.

This montage has three goals:

1. Characterize the multichannel sensor's response to the stimulus. Using hue/grid/flashDiff
2. Test whether this setup can be used to simulate color vision deficiency data, using the hue/grid/filter measurements.
3. Understand how channel-level perceived brightness relates to the SSVEP responses recorded in the main experiment. Using hue/grid/flashDiff

## Sensor

The hue sensor reports brightness independently on three channels — blue, green, and red. A custom logger samples the sensor at approximately every 110 ms.


## Goal 1 — Characterizing the Stimulus

The first goal is to understand the stimulus itself in more detail: specifically, how much of each channel's value (red / green / blue) is present at each point in the grid.

## Goal 2 — Filter Comparison (Toward Simulating Color Vision Deficiency)

We repeated the experiment with a filter placed between the sensor and the stimulus, to see how each filter shifts the measured channel values.

Three filter conditions were tested:

- **Yellow filter** — condition labels end in `F`
- **Orange filter** — condition labels end in `Or`
- **No filter** — condition labels end in `NF`

Each filter condition was tested in two modalities:

- Stimulus flickering at 10 Hz (matching the SSVEP experiment)
- Stimulus with no flicker

Comparing these two modalities isolates the effect of flicker on perceived brightness, independent of the filter itself. It will be interesting to compare how each filter, in each modality affects the perception of each channel.

## Goal 3 — Relating SSVEPs to Cone Activation

This is the most important goal: understanding what SSVEP signals actually reflect in terms of the specific cone activations driving them.

To test this, I ran the grid experiment multiple times with the hue sensor, changing which channel(s) flash each time:

| Condition | Description |
|---|---|
| `Flash_NN` | Nothing flashes (baseline, to measure environmental/ambient effects) |
| `Flash_R` | Only the red LED flashes, at its current grid value |
| `Flash_G` | Only the green LED flashes, at its current grid value |
| `Flash_Y` | Only flashes at the yellow reference value |
| `Flash_RG` | Red and green LEDs flash together at their current grid values (no yellow reference) |
| `Flash_RY` | Current red configuration flashes against the yellow reference |
| `Flash_GY` | Green LED flashes at its current value, then at the yellow reference value |
| `Flash_RGY` / `Flash_RGY_1` | All channels (red, green, and yellow reference) flash together |

## Working Hypothesis

Before comparing these results to the SSVEP data, I want to relate the `Flash_*` conditions to one another. My working hypothesis is that the responses combine additively and linearly across conditions. This is that GY is a combination of G, Y and maybe NN. And that RGY is the combination of R, G, Y, NN,  or RG, Y, NN, or RY, G, NN.

## Result: additivity confirmed, with an offset that scales

Tested against real data (`PLANhue.md` M2-M3, `notebooks/03_additivity_explore.ipynb`) -- the hypothesis holds, once the `NN` (nothing-flashes) term is corrected for properly.

`NN` is a shared environmental offset present in every condition's reading, not something to add once per combination. Summing *k* single/multi-channel conditions and subtracting `NN` only once (`RGY ≈ R + G + Y − NN`) under-corrects badly -- mean |residual| 340-460 raw counts, every channel offset uniformly high. Subtracting `NN` once per *extra* condition summed (`RGY ≈ R + G + Y − 2·NN`, i.e. `(k−1)·NN`) fixes it: residuals drop to 9-18 counts, matching the two-component combinations (`GY ≈ G + Y − NN`, `RY ≈ R + Y − NN`, `RG ≈ R + G − NN`, each 4-29 counts) and the sensor's own run-to-run repeatability floor (`02_flashdiff_explore.ipynb`'s two `RGY` runs: mean |diff| 3-19 counts, worst cell ~120). The three named `RGY` decompositions (`R+G+Y`, `RG+Y`, `RY+G`, each with the correct `(k−1)·NN` correction) land in the same band as each other -- no one grouping is privileged, consistent with genuine additivity.

Plotting predicted vs. actual against trial order, not just as an aggregate residual (`plotting.plot_prediction_trials`), confirms this holds across the *entire* grid sequence -- every peak and trough of the (non-raster-ordered, see `README.md`) grid is reproduced, not just the average. What daylight remains is small, consistent jitter, proportionally largest on whichever channel is least-flashed in a given condition (e.g. `HueR` under `GY`) -- noise, not a shape mismatch.

Not yet checked: whether `(k−1)·NN` holds for `filters/`'s conditions too, or whether a per-channel offset multiplier fits better than one shared value.

