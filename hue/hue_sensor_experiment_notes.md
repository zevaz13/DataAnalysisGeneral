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

