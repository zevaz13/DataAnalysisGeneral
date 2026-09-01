"""Per-trial aggregation for the hue-sensor grid experiment
(hue_sensor_experiment_notes.md, PLANhue.md M2). Confirmed in
notebooks/01_filters_explore.ipynb and 02_flashdiff_explore.ipynb: a Stim
block's edges are contaminated by the neighboring trial (see
hue/README.md), so aggregation drops samples from both ends rather than
just an onset ramp.

aggregate_trials -- mean of each channel within a Stim block, trimmed.

additivity_prediction -- per-grid-cell predicted-vs-actual comparison for
the Goal-3 additivity hypothesis (hue_sensor_experiment_notes.md): does a
multi-channel condition equal the sum of its single-channel conditions,
corrected for the shared NN (nothing-flashes) environmental offset?
"""

import pandas as pd

from plotting import CORE_CHANNELS

TRIM = 5

_KEEP = ["is_baseline", "grid_index", "baseline_id", "Red", "Green", "Yellow"]


def aggregate_trials(df: pd.DataFrame, *, group_cols: list[str], channels: list[str] = CORE_CHANNELS, trim: int = TRIM) -> pd.DataFrame:
    """One row per block (grid or baseline) named by group_cols (e.g.
    ['flicker','filter','Stim'] for load_filters, ['condition','Stim']
    for load_flashdiff): the first/last `trim` samples of the block are
    dropped before averaging `channels`, clearing the neighbor-
    contaminated edges documented in hue/README.md. is_baseline/
    grid_index/baseline_id/Red/Green/Yellow are constant within a block
    and carried through unchanged."""
    ordered = df.sort_values("sample_idx")
    grouped = ordered.groupby(group_cols, sort=False)
    rank = grouped.cumcount()
    count = grouped["sample_idx"].transform("count")
    trimmed = ordered[(rank >= trim) & (rank < count - trim)]
    aggregations = {col: "first" for col in _KEEP} | {ch: "mean" for ch in channels}
    return trimmed.groupby(group_cols, as_index=False).agg(aggregations)


def additivity_prediction(agg: pd.DataFrame, *, components: list[str], target: str, offset_multiplier: float, offset_condition: str = "NN", condition_col: str = "condition", channels: list[str] = CORE_CHANNELS) -> pd.DataFrame:
    """Tests hue_sensor_experiment_notes.md's working hypothesis -- that
    conditions combine additively -- against a candidate offset
    correction: predicted = sum(components) - offset_multiplier *
    offset_condition, one row per grid_index. offset_multiplier is a free
    parameter, not derived from len(components): whether the right
    correction is a flat 1x or scales with the number of components
    summed (each extra summed condition adds one more copy of the shared
    NN offset) is exactly what M2 is exploring, not assumed here."""
    grid = agg[~agg["is_baseline"]]
    by_condition = {cond: grid[grid[condition_col] == cond].set_index("grid_index")[channels] for cond in [*components, target, offset_condition]}
    predicted = sum(by_condition[c] for c in components) - offset_multiplier * by_condition[offset_condition]
    actual = by_condition[target]
    out = predicted.add_suffix("_predicted").join(actual.add_suffix("_actual"))
    return out.reset_index()
