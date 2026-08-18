"""Heatmap plots for SSVEP grid data, raw or baseline-normalized.

Axes: red is always x, green is always y. Color follows the dataviz skill: raw
values are a magnitude job (sequential, one hue) while normalized values are
signed/polarity (diverging, centered on zero) -- both ramps are the skill's
validated default palette. Every function accepts optional clim=(vmin, vmax)
and cmap overrides; multi-panel functions use one shared clim/cmap across all
their panels by default.
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Colormap, LinearSegmentedColormap

from analysis import mean_grid, mean_grid_across_subjects, normalized_grid, raw_grid, subjects_in_group

FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "files")

SEQUENTIAL_BLUE = LinearSegmentedColormap.from_list("sequential_blue", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
DIVERGING_BLUE_RED = LinearSegmentedColormap.from_list("diverging_blue_red", ["#2a78d6", "#f0efec", "#e34948"])

METHOD_LABELS = {"percent": "% change from baseline", "db": "dB change from baseline", "zscore": "baseline z-score"}


def _grid_axes() -> tuple[list[float], list[float]]:
    with open(os.path.join(FILES_DIR, "grid.json")) as f:
        grid = json.load(f)
    return grid["redArray"], grid["greenArray"]


def _default_cmap(diverging: bool) -> Colormap:
    return DIVERGING_BLUE_RED if diverging else SEQUENTIAL_BLUE


def _auto_clim(grids: list[np.ndarray], *, diverging: bool) -> tuple[float, float]:
    values = np.concatenate([g.ravel() for g in grids])
    if diverging:
        vmax = float(np.abs(values).max())
        return -vmax, vmax
    return float(values.min()), float(values.max())


def _label_for(normalize: dict | None) -> str:
    return "raw value" if normalize is None else METHOD_LABELS[normalize["method"]]


def _plot_heatmap(ax: plt.Axes, grid: np.ndarray, *, cmap: Colormap, vmin: float, vmax: float, label: str) -> None:
    """grid is indexed [red_idx, green_idx]; plotted with red on x, green on y."""
    im = ax.imshow(grid.T, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    red_vals, green_vals = _grid_axes()
    ax.set_xticks(range(len(red_vals)))
    ax.set_xticklabels([f"{v:.0f}" for v in red_vals], rotation=45, ha="right")
    ax.set_xlabel("red")
    ax.set_yticks(range(len(green_vals)))
    ax.set_yticklabels([f"{v:.0f}" for v in green_vals])
    ax.set_ylabel("green")
    plt.colorbar(im, ax=ax, label=label)


def plot_run(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_id: str,
    session: int,
    run: int,
    *,
    normalize: dict | None = None,
    clim: tuple[float, float] | None = None,
    cmap: Colormap | str | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Heatmap for one participant/session/run. normalize, if given, is a dict
    of scope/trials/method kwargs for analysis.normalized_grid."""
    grid = raw_grid(runmap_df, sub_id, session, run) if normalize is None else normalized_grid(
        runmap_df, baselines_df, sub_id, session, run, **normalize
    )
    vmin, vmax = clim if clim is not None else _auto_clim([grid], diverging=normalize is not None)
    if ax is None:
        _, ax = plt.subplots()
    _plot_heatmap(ax, grid, cmap=cmap or _default_cmap(normalize is not None), vmin=vmin, vmax=vmax, label=_label_for(normalize))
    ax.set_title(f"{sub_id} session {session} run {run}")
    return ax


def plot_all_runs(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_id: str,
    session: int,
    *,
    normalize: dict | None = None,
    clim: tuple[float, float] | None = None,
    cmap: Colormap | str | None = None,
) -> plt.Figure:
    """One heatmap per run of a participant/session (handles 3- or 4-run
    sessions), sharing one color scale across all panels by default."""
    runs = sorted(runmap_df.query("sub_id == @sub_id and session == @session")["run"].unique())
    grids = [
        raw_grid(runmap_df, sub_id, session, run)
        if normalize is None
        else normalized_grid(runmap_df, baselines_df, sub_id, session, run, **normalize)
        for run in runs
    ]
    vmin, vmax = clim if clim is not None else _auto_clim(grids, diverging=normalize is not None)
    resolved_cmap = cmap or _default_cmap(normalize is not None)
    label = _label_for(normalize)

    fig, axes = plt.subplots(1, len(runs), figsize=(4.5 * len(runs), 4))
    for ax, run, grid in zip(np.atleast_1d(axes), runs, grids):
        _plot_heatmap(ax, grid, cmap=resolved_cmap, vmin=vmin, vmax=vmax, label=label)
        ax.set_title(f"{sub_id} session {session} run {run}")
    fig.suptitle(f"{sub_id} session {session} -- all runs")
    fig.tight_layout()
    return fig


def plot_mean_run(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_id: str,
    session: int,
    *,
    normalize: dict | None = None,
    clim: tuple[float, float] | None = None,
    cmap: Colormap | str | None = None,
) -> plt.Axes:
    """Heatmap of the mean grid across all runs of a participant/session."""
    grid = mean_grid(runmap_df, baselines_df, sub_id, session, normalize=normalize)
    vmin, vmax = clim if clim is not None else _auto_clim([grid], diverging=normalize is not None)
    _, ax = plt.subplots()
    _plot_heatmap(ax, grid, cmap=cmap or _default_cmap(normalize is not None), vmin=vmin, vmax=vmax, label=_label_for(normalize))
    ax.set_title(f"{sub_id} session {session} -- mean across runs")
    return ax


def plot_mean_across_subjects(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    session: int,
    *,
    sub_ids: list[str] | None = None,
    group: str | None = None,
    subgroup: str | None = None,
    normalize: dict | None = None,
    clim: tuple[float, float] | None = None,
    cmap: Colormap | str | None = None,
) -> plt.Axes:
    """Grand-mean heatmap: each subject's own mean-across-runs grid, then
    averaged across subjects. Pass sub_ids explicitly, or filter by group/
    subgroup (metadata_df); with none given, uses every subject at this
    session."""
    if sub_ids is None:
        sub_ids = subjects_in_group(metadata_df, session, group=group, subgroup=subgroup)
    grid = mean_grid_across_subjects(runmap_df, baselines_df, sub_ids, session, normalize=normalize)
    vmin, vmax = clim if clim is not None else _auto_clim([grid], diverging=normalize is not None)
    _, ax = plt.subplots()
    _plot_heatmap(ax, grid, cmap=cmap or _default_cmap(normalize is not None), vmin=vmin, vmax=vmax, label=_label_for(normalize))
    label = ", ".join(filter(None, [group, subgroup])) or f"{len(sub_ids)} subjects"
    ax.set_title(f"session {session} -- mean across {label}")
    return ax


def plot_subjects_side_by_side(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    session: int,
    *,
    sub_ids: list[str] | None = None,
    group: str | None = None,
    subgroup: str | None = None,
    normalize: dict | None = None,
    clim: tuple[float, float] | None = None,
    cmap: Colormap | str | None = None,
) -> plt.Figure:
    """One heatmap per subject (each subject's own mean-across-runs grid), side
    by side, sharing one color scale by default. Pass sub_ids explicitly, or
    filter by group/subgroup (metadata_df)."""
    if sub_ids is None:
        sub_ids = subjects_in_group(metadata_df, session, group=group, subgroup=subgroup)
    grids = [mean_grid(runmap_df, baselines_df, sub_id, session, normalize=normalize) for sub_id in sub_ids]
    vmin, vmax = clim if clim is not None else _auto_clim(grids, diverging=normalize is not None)
    resolved_cmap = cmap or _default_cmap(normalize is not None)
    label = _label_for(normalize)

    fig, axes = plt.subplots(1, len(sub_ids), figsize=(4.5 * len(sub_ids), 4))
    for ax, sub_id, grid in zip(np.atleast_1d(axes), sub_ids, grids):
        _plot_heatmap(ax, grid, cmap=resolved_cmap, vmin=vmin, vmax=vmax, label=label)
        ax.set_title(sub_id)
    subtitle = ", ".join(filter(None, [group, subgroup])) or f"{len(sub_ids)} subjects"
    fig.suptitle(f"session {session} -- {subtitle} side by side")
    fig.tight_layout()
    return fig
