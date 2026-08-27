"""Plotting for the hue-sensor grid experiment
(hue/hue_sensor_experiment_notes.md). Two views, matching PLANhue.md M1's
two exploration goals:

plot_channel_overview -- every raw sample of a condition's core channels,
in original recording order, to see the onset-transient-then-plateau
shape within each Stim block before deciding how to aggregate it.

plot_channel_grid -- a 10x10 heatmap per channel, from an
already-aggregated one-row-per-grid-cell table. The aggregation itself is
prototyped per notebook for now (PLANhue.md), not fixed here.
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
