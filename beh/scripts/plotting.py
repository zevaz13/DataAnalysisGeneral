"""Scatter plots of the manual/behavioral (red, green) match-point data.

Axes: red is always x, green is always y, matching ssveps' convention and
the physical stimulus this task shares with it. Default axis limits are
x=[0, 3200], y=[0, 2000] (the SSVEP stimulus grid's own range) for visual
comparability across plots -- some subjects' green values run past 2000
(the raw data does, see loader.load_behavioral), and are not clipped, just
plotted against a fixed default window; pass ylim= to see the full range for
a specific subject/group.

Color follows the dataviz skill's categorical rule: the first three
palette slots are the only ones validated for an all-pairs (scatter)
comparison, so per-session coloring (at most 3 sessions in this dataset)
uses them directly. Multi-subject/multi-group figures instead use one panel
per subject/group (faceting, the skill's own prescribed alternative past
three categories) with a single uniform point color -- identity comes from
the panel title, not hue, the same convention ssveps/scripts/plotting.py
uses for its boxplots.
"""

import matplotlib.pyplot as plt
import pandas as pd

from loader import subjects_in_group

POINT_COLOR = "#2a78d6"
SESSION_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]  # validated all-pairs for scatter, up to 3 categories
XLIM = (0, 3200)
YLIM = (0, 2000)

# Every multi-panel figure here wraps to at most this many panels per row.
MAX_PANEL_COLS = 5


def _style_axes(ax: plt.Axes, *, xlim: tuple[float, float], ylim: tuple[float, float], title: str | None = None) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("red")
    ax.set_ylabel("green")
    if title:
        ax.set_title(title)


def _multi_panel_figure(n: int, *, max_cols: int = MAX_PANEL_COLS, panel_size: float = 3.5) -> tuple[plt.Figure, list[plt.Axes]]:
    n_cols = min(n, max_cols)
    n_rows = -(-n // max_cols)  # ceil division
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(panel_size * n_cols, panel_size * n_rows), squeeze=False)
    flat_axes = axes.ravel()
    for ax in flat_axes[n:]:
        ax.axis("off")
    return fig, list(flat_axes[:n])


def plot_subject_session(
    df: pd.DataFrame, sub_id: str, session: int, *, xlim: tuple[float, float] = XLIM, ylim: tuple[float, float] = YLIM, ax: plt.Axes | None = None
) -> plt.Axes:
    """Scatter of one subject's clicks in one session."""
    sub = df[(df["sub_id"] == sub_id) & (df["session"] == session)]
    if ax is None:
        _, ax = plt.subplots()
    ax.scatter(sub["red"], sub["green"], color=POINT_COLOR, alpha=0.7, edgecolor="white")
    _style_axes(ax, xlim=xlim, ylim=ylim, title=f"{sub_id} session {session} (n={len(sub)})")
    return ax


def plot_subject_sessions(
    df: pd.DataFrame,
    sub_id: str,
    *,
    sessions: list[int] | None = None,
    xlim: tuple[float, float] = XLIM,
    ylim: tuple[float, float] = YLIM,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Scatter of one subject's clicks, every session overlaid, one color
    per session (at most 3 sessions in this dataset -- see module docstring
    for why color, not shape, is safe here)."""
    sub = df[df["sub_id"] == sub_id]
    if sessions is None:
        sessions = sorted(sub["session"].unique())
    if ax is None:
        _, ax = plt.subplots()
    for session, color in zip(sessions, SESSION_COLORS):
        points = sub[sub["session"] == session]
        ax.scatter(points["red"], points["green"], color=color, alpha=0.7, edgecolor="white", label=f"session {session} (n={len(points)})")
    _style_axes(ax, xlim=xlim, ylim=ylim, title=sub_id)
    ax.legend(fontsize=8)
    return ax


def plot_subject_cloud(
    df: pd.DataFrame, sub_id: str, *, xlim: tuple[float, float] = XLIM, ylim: tuple[float, float] = YLIM, ax: plt.Axes | None = None
) -> plt.Axes:
    """Scatter of every click from every session of one subject, pooled into
    a single color -- the whole-subject point cloud, session distinctions
    dropped."""
    sub = df[df["sub_id"] == sub_id]
    if ax is None:
        _, ax = plt.subplots()
    ax.scatter(sub["red"], sub["green"], color=POINT_COLOR, alpha=0.7, edgecolor="white")
    _style_axes(ax, xlim=xlim, ylim=ylim, title=f"{sub_id} (n={len(sub)}, all sessions)")
    return ax


def plot_subjects_pooled(
    df: pd.DataFrame,
    *,
    sub_ids: list[str] | None = None,
    group: str | None = None,
    subgroup: str | None = None,
    xlim: tuple[float, float] = XLIM,
    ylim: tuple[float, float] = YLIM,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Scatter of every click from every subject/session matching
    sub_ids (explicit) or group/subgroup, pooled into one panel and one
    color -- "all the data from one group on one plot" (PLANbeh.md M1).
    Pass sub_ids to plot an arbitrary hand-picked set of subjects together
    instead of a group/subgroup filter."""
    if sub_ids is None:
        sub_ids = subjects_in_group(df, group=group, subgroup=subgroup)
    sub = df[df["sub_id"].isin(sub_ids)]
    label = ", ".join(filter(None, [group, subgroup])) or f"{len(sub_ids)} subjects"
    if ax is None:
        _, ax = plt.subplots()
    ax.scatter(sub["red"], sub["green"], color=POINT_COLOR, alpha=0.5, edgecolor="white")
    _style_axes(ax, xlim=xlim, ylim=ylim, title=f"{label} (n={len(sub_ids)} subjects, {len(sub)} clicks)")
    return ax


def plot_subjects_grid(
    df: pd.DataFrame,
    *,
    sub_ids: list[str] | None = None,
    group: str | None = None,
    subgroup: str | None = None,
    xlim: tuple[float, float] = XLIM,
    ylim: tuple[float, float] = YLIM,
) -> plt.Figure:
    """One panel per subject (that subject's whole point cloud, every
    session pooled), wrapped to at most MAX_PANEL_COLS per row -- "all on a
    grid (max 5 participants per row)" (PLANbeh.md M1). Pass sub_ids for an
    arbitrary hand-picked set of subjects side by side instead of a
    group/subgroup filter."""
    if sub_ids is None:
        sub_ids = subjects_in_group(df, group=group, subgroup=subgroup)
    fig, axes = _multi_panel_figure(len(sub_ids))
    for ax, sub_id in zip(axes, sub_ids):
        plot_subject_cloud(df, sub_id, xlim=xlim, ylim=ylim, ax=ax)
    subtitle = ", ".join(filter(None, [group, subgroup])) or f"{len(sub_ids)} subjects"
    fig.suptitle(subtitle)
    fig.tight_layout()
    return fig


def plot_groups_side_by_side(
    df: pd.DataFrame, categories: list[dict], *, xlim: tuple[float, float] = XLIM, ylim: tuple[float, float] = YLIM
) -> plt.Figure:
    """One panel per category, each showing that category's pooled point
    cloud -- "plot HC group, next to PD next to CVD, next to protan, next
    to deutan" (PLANbeh.md M1). categories is a list of {"label", "group",
    "subgroup"} dicts, same shape as ssveps' plotting.plot_groups_side_by_side."""
    fig, axes = _multi_panel_figure(len(categories))
    for ax, cat in zip(axes, categories):
        plot_subjects_pooled(df, group=cat.get("group"), subgroup=cat.get("subgroup"), xlim=xlim, ylim=ylim, ax=ax)
        ax.set_title(cat["label"] + "\n" + ax.get_title())
    fig.tight_layout()
    return fig
