"""Spectra plots: one panel per group, curves overlaid within a panel."""

import matplotlib.pyplot as plt
import pandas as pd

FILTER_ORDER = ["NF", "YF", "RF"]
STIMULUS_COLORS = {"blue2000": "tab:blue", "blue2000_red2000": "red", "blue2000_yellow2000": "gold"}


def _panels(
    df: pd.DataFrame, panel_by: str, line_by: str, panels: list[str], lines: list[str], colors: dict[str, str] | None = None
) -> plt.Figure:
    fig, axes = plt.subplots(1, len(panels), figsize=(5 * len(panels), 4), sharey=True, squeeze=False)
    for ax, panel in zip(axes[0], panels):
        for line in lines:
            sub = df[(df[panel_by] == panel) & (df[line_by] == line)]
            ax.plot(sub["wavelength"], sub["irradiance"], label=line, color=(colors or {}).get(line))
        ax.set_title(panel)
        ax.set_xlabel("wavelength (nm)")
        ax.legend()
    axes[0][0].set_ylabel("spectral irradiance (W/(m$^2$ nm))")
    fig.tight_layout()
    return fig


def plot_by_filter(df: pd.DataFrame) -> plt.Figure:
    """One panel per filter, all stimuli overlaid."""
    stimuli = sorted(df["stimulus"].unique())
    return _panels(df, "filter", "stimulus", FILTER_ORDER, stimuli, STIMULUS_COLORS)


def plot_by_stimulus(df: pd.DataFrame) -> plt.Figure:
    """One panel per stimulus, the three filters overlaid."""
    stimuli = sorted(df["stimulus"].unique())
    return _panels(df, "stimulus", "filter", stimuli, FILTER_ORDER)


def plot_traces(df: pd.DataFrame, ncols: int = 4) -> plt.Figure:
    """One panel per trace, shared axes."""
    traces = sorted(df["trace"].unique())
    nrows = -(-len(traces) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows), sharex=True, sharey=True, squeeze=False)
    for ax, trace in zip(axes.flat, traces):
        sub = df[df["trace"] == trace]
        ax.plot(sub["wavelength"], sub["irradiance"])
        ax.set_title(trace)
    for ax in axes[-1]:
        ax.set_xlabel("wavelength (nm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("spectral irradiance (W/(m$^2$ nm))")
    fig.tight_layout()
    return fig


def plot_overlay(df: pd.DataFrame, traces: list[str]) -> plt.Figure:
    """Selected traces on one axis."""
    fig, ax = plt.subplots(figsize=(8, 4))
    for trace in traces:
        sub = df[df["trace"] == trace]
        ax.plot(sub["wavelength"], sub["irradiance"], label=trace)
    ax.set_xlabel("wavelength (nm)")
    ax.set_ylabel("spectral irradiance (W/(m$^2$ nm))")
    ax.legend()
    fig.tight_layout()
    return fig
