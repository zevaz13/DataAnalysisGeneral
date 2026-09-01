"""Plotting for the hue-sensor grid experiment
(hue/hue_sensor_experiment_notes.md). See PLANhue.md for which milestone
introduced each view:

plot_channel_overview -- every raw sample of a condition's core channels,
in original recording order, to see the onset-transient-then-plateau
shape within each Stim block before deciding how to aggregate it.

plot_channel_trials -- an aggregated channel's value vs. grid_index
(trial order), the linear counterpart to plot_channel_grid.

plot_channel_grid -- a 10x10 heatmap per channel, from an
already-aggregated one-row-per-grid-cell table.

plot_prediction_trials -- actual vs. predicted (additivity hypothesis)
value per channel, vs. grid_index, from aggregate.additivity_prediction.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CORE_CHANNELS = ["HueR", "HueG", "HueB"]
CHANNEL_COLORS = {"HueR": "#e34948", "HueG": "#1baf7a", "HueB": "#2a78d6"}  # FULL_PALETTE slots reused for their R/G/B mnemonic (beh/scripts/plotting.py)


def plot_channel_overview(df: pd.DataFrame, *, group_col: str, groups: list[str] | None = None, channels: list[str] = CORE_CHANNELS) -> plt.Figure:
    """One subplot per group_col value (e.g. 'condition', or 'filter' on a
    flicker-filtered df), each channel plotted across the full raw sample
    sequence in original recording order -- "plot the whole channel data
    completely." Stim-block boundaries aren't marked here; slice df to one
    Stim (df[df['Stim'] == n]) first to zoom into a single trial's onset/
    plateau shape instead."""
    if groups is None:
        groups = sorted(df[group_col].unique())
    fig, axes = plt.subplots(len(groups), 1, figsize=(12, 2.5 * len(groups)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, group in zip(axes, groups):
        sub = df[df[group_col] == group]
        for channel in channels:
            ax.plot(np.arange(len(sub)), sub[channel].to_numpy(), color=CHANNEL_COLORS.get(channel), linewidth=0.8, label=channel)
        ax.set_ylabel("raw counts")
        ax.set_title(str(group), fontsize=9, loc="left")
    axes[0].legend(fontsize=8, ncol=len(channels))
    axes[-1].set_xlabel("sample (recording order)")
    fig.tight_layout()
    return fig


def plot_channel_trials(agg: pd.DataFrame, *, group_col: str, groups: list[str] | None = None, channels: list[str] = CORE_CHANNELS, show_baseline: bool = False) -> plt.Figure:
    """One subplot per group_col value, aggregated channel value (from
    aggregate.aggregate_trials) plotted against grid_index (trial order)
    -- the linear counterpart to plot_channel_grid's heatmap, for reading
    off a channel's response as a simple curve across the grid sequence.
    Baseline rows (is_baseline=True) are excluded by default, since they
    don't carry a grid_index; pass show_baseline=True to include them as
    separate markers past the grid trials, one baseline_id apart, for a
    quick by-eye reference rather than a meaningful x-position."""
    if groups is None:
        groups = sorted(agg[group_col].unique())
    fig, axes = plt.subplots(len(groups), 1, figsize=(12, 2.5 * len(groups)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, group in zip(axes, groups):
        sub = agg[agg[group_col] == group]
        grid = sub[~sub["is_baseline"]].sort_values("grid_index")
        for channel in channels:
            ax.plot(grid["grid_index"], grid[channel], color=CHANNEL_COLORS.get(channel), linewidth=1.0, label=channel)
        if show_baseline:
            baseline = sub[sub["is_baseline"]].sort_values("baseline_id")
            x0 = grid["grid_index"].max() + 5
            for channel in channels:
                ax.scatter(x0 + baseline["baseline_id"], baseline[channel], color=CHANNEL_COLORS.get(channel), marker="x", s=20)
        ax.set_ylabel("mean raw counts")
        ax.set_title(str(group), fontsize=9, loc="left")
    axes[0].legend(fontsize=8, ncol=len(channels))
    axes[-1].set_xlabel("grid_index (trial order)" + (" -- baseline blocks past the gap" if show_baseline else ""))
    fig.tight_layout()
    return fig


def plot_prediction_trials(pred: pd.DataFrame, *, channels: list[str] = CORE_CHANNELS, title: str = "") -> plt.Figure:
    """One subplot per channel, from aggregate.additivity_prediction's
    output: the actual condition's value in that channel's own color
    (solid) against the predicted/combined value in black (dashed), both
    vs. grid_index (trial order). Per-trial counterpart to
    03_additivity_explore.ipynb's predicted-vs-actual scatter -- shows
    where along the grid a combination agrees or disagrees, not just the
    aggregate residual size."""
    pred = pred.sort_values("grid_index")
    fig, axes = plt.subplots(len(channels), 1, figsize=(12, 2.5 * len(channels)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, channel in zip(axes, channels):
        ax.plot(pred["grid_index"], pred[f"{channel}_actual"], color=CHANNEL_COLORS.get(channel), linewidth=1.2, label="actual")
        ax.plot(pred["grid_index"], pred[f"{channel}_predicted"], color="black", linewidth=1.0, linestyle="--", label="predicted")
        ax.set_ylabel(channel)
        ax.set_title(channel, fontsize=9, loc="left")
    axes[0].legend(fontsize=8)
    axes[-1].set_xlabel("grid_index (trial order)")
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_channel_grid(agg: pd.DataFrame, *, channels: list[str] = CORE_CHANNELS) -> plt.Figure:
    """One heatmap per channel, from agg (one row per grid cell: Red,
    Green, plus one already-aggregated column per channel) -- "plot the
    channel perception as a grid." Red on x, green on y, matching
    ssveps/scripts/plotting.py's own grid-heatmap convention -- but unlike
    ssveps/, this data carries its own actual (Red, Green) stimulus value
    per row already, so pivoting directly on those (ascending) replaces
    the separate grid.json index lookup ssveps/ needs. Each channel gets
    its own color scale -- raw sensor counts aren't comparable in
    magnitude across channels the way ssveps/'s normalized percent-change
    is comparable across subjects/groups, so a shared vmin/vmax would be
    misleading here."""
    fig, axes = plt.subplots(1, len(channels), figsize=(5 * len(channels), 4.5))
    axes = np.atleast_1d(axes)
    for ax, channel in zip(axes, channels):
        grid = agg.pivot(index="Green", columns="Red", values=channel)
        im = ax.imshow(grid.to_numpy(), origin="lower", cmap="viridis", aspect="auto", extent=[grid.columns.min(), grid.columns.max(), grid.index.min(), grid.index.max()])
        ax.set_xlabel("red")
        ax.set_ylabel("green")
        ax.set_title(channel)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="raw counts")
    fig.tight_layout()
    return fig
