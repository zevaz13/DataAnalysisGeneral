"""Load the multichannel hue-sensor grid experiment data: bench
characterization of the same red/green/yellow optical stimulator ssveps/
and beh/ use, via a 3-channel (R/G/B) brightness sensor sampled every
~110ms in place of a human participant. See
hue/hue_sensor_experiment_notes.md and ../../PLANhue.md.

Raw data: /home/sebas/data/hue/grid/{filters,flashDiff}/*.txt (read in
place, not copied into the repo), tab-separated, one row per sample. No
sub_id/session -- this is instrument characterization, not participant
data.

Stim runs 1-100 for grid rows -- the same 10x10 red/green grid ssveps/ and
beh/ share (Red/Green here are the actual D/A values, confirmed against
ssveps/files/grid.json's redArray/greenArray; Yellow is a constant 2400,
the same fixed yellow reference beh/'s manual-match task uses). Baseline
rows use a separate Stim range per file -- normalized into a consistent
is_baseline/grid_index/baseline_id here rather than left as three
different raw numbering schemes (see load_filters/load_flashdiff)."""

import glob
import os
import re

import pandas as pd

RAW_DIR = "/home/sebas/data/hue/grid"
FILTERS_DIR = os.path.join(RAW_DIR, "filters")
FLASHDIFF_DIR = os.path.join(RAW_DIR, "flashDiff")

FILTERS_BASELINE_STIM = 999


def _read_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t")
    df["sample_idx"] = df.groupby("Stim").cumcount()
    return df


_FILTERS_FILENAME_RE = re.compile(r"^(?P<flicker>solid|flash)_(?P<filter>NF|F|Or)$")


def load_filters(dir: str = FILTERS_DIR) -> pd.DataFrame:
    """All six filters/{solid,flash}_{F,NF,Or}.txt files, concatenated,
    tagged with flicker ('flash'=10Hz, matching the SSVEP stimulus;
    'solid'=no flicker) and filter ('F'=yellow, 'Or'=orange, 'NF'=no
    filter) parsed from the filename (hue_sensor_experiment_notes.md's
    Goal 2). Stim 1-100 is the grid (grid_index=Stim); Stim 999 is one
    longer reference/baseline reading per file (103 samples vs. ~34-35 for
    a grid cell) -- is_baseline=True, grid_index=NaN, baseline_id=0."""
    frames = []
    for path in sorted(glob.glob(os.path.join(dir, "*.txt"))):
        name = os.path.splitext(os.path.basename(path))[0]
        m = _FILTERS_FILENAME_RE.match(name)
        if not m:
            raise ValueError(f"unrecognized filters filename: {name}")
        df = _read_raw(path)
        df["flicker"] = m["flicker"]
        df["filter"] = m["filter"]
        df["is_baseline"] = df["Stim"] == FILTERS_BASELINE_STIM
        df["grid_index"] = df["Stim"].where(~df["is_baseline"])
        df["baseline_id"] = pd.NA
        df.loc[df["is_baseline"], "baseline_id"] = 0
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


_FLASHDIFF_CONDITIONS = ["NN", "R", "G", "Y", "RG", "RY", "GY", "RGY", "RGY_1"]


def load_flashdiff(dir: str = FLASHDIFF_DIR) -> pd.DataFrame:
    """All nine flashDiff/flash_*.txt files, concatenated, tagged with
    condition -- which channel(s) flash, per
    hue_sensor_experiment_notes.md's Goal 3 table (NN=nothing/baseline
    check, R/G/Y=one channel alone, RG/RY/GY=two together, RGY=all three;
    RGY_1 is a second RGY run, logged differently -- see below).

    Normalizes two different raw Stim-numbering schemes into one
    consistent is_baseline/grid_index/baseline_id:

    - Every condition except RGY_1: Stim 1-100 is the grid (grid_index=
      Stim); Stim 1000-1005 are six longer baseline blocks (is_baseline=
      True, baseline_id=Stim-1000, distinguishing which of the six a row
      belongs to).
    - RGY_1: logged with load_filters' single-baseline convention instead
      -- Stim 999 is the one baseline reading (is_baseline=True,
      baseline_id=0), Stim 1000-1099 is the grid, offset by 999
      (grid_index=Stim-999).

    Both schemes collapse to the same three columns, so a caller doesn't
    need to know which raw convention a given condition happened to use."""
    frames = []
    for path in sorted(glob.glob(os.path.join(dir, "*.txt"))):
        name = os.path.splitext(os.path.basename(path))[0]
        if not name.startswith("flash_"):
            raise ValueError(f"unrecognized flashDiff filename: {name}")
        condition = name[len("flash_") :]
        if condition not in _FLASHDIFF_CONDITIONS:
            raise ValueError(f"unrecognized flashDiff condition: {condition!r} (from {name})")
        df = _read_raw(path)
        df["condition"] = condition
        if condition == "RGY_1":
            df["is_baseline"] = df["Stim"] == 999
            df["grid_index"] = (df["Stim"] - 999).where(~df["is_baseline"])
            df["baseline_id"] = pd.NA
            df.loc[df["is_baseline"], "baseline_id"] = 0
        else:
            df["is_baseline"] = df["Stim"] >= 1000
            df["grid_index"] = df["Stim"].where(~df["is_baseline"])
            df["baseline_id"] = (df["Stim"] - 1000).where(df["is_baseline"])
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
