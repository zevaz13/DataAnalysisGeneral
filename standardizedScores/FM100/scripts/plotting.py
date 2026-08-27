"""Linear and radial (polar) plots of FM100 per-cap error profiles
(scores.err_vals).

Linear: cap position (1-85) on x, circular hue error on y -- the standard
FM100 error-score profile. Radial: the same profile wrapped onto a circle
(angle = cap position, radius = error) -- the "trademark" FM100 diagram.

Color follows the same dataviz-skill rules beh/scripts/plotting.py uses:
SESSION_COLORS (first 3 categorical slots, all-pairs validated) for
per-session overlays on a single participant (at most 3 sessions here too).
Group plots are *line* charts (a mean +-1 SD band per category), which the
dataviz skill validates on the *adjacent*-pair rule rather than the stricter
all-pairs scatter rule -- so FULL_PALETTE's full 8 slots are safe in fixed
order without a category cap or faceting.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comparisons import FEATURES, group_pooled_scores, tukey_outlier_mask
from loader import subjects_in_group
from scores import N_CAPS, err_vals

SESSION_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]  # validated all-pairs for scatter, up to 3 categories
SUBJECT_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]  # validated all-pairs for scatter, up to 4 subjects --
# #4a3aa7 replaces FULL_PALETTE's natural 4th slot, #eda100, which fails the
# dataviz skill's normal-vision floor against #eb6834 (deltaE 13.7 < 15)
FULL_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]  # adjacent-pair validated, for lines
BAND_ALPHA = 0.2

CAP_POSITIONS = np.arange(1, N_CAPS + 1)
CAP_ANGLES = np.linspace(0, 2 * np.pi, N_CAPS, endpoint=False)


def _smooth_circular(values: np.ndarray, window: int) -> np.ndarray:
    """Circular moving average -- caps wrap around the hue circle, so the
    window wraps too (window=1 is a no-op, the raw values)."""
    if window <= 1:
        return values
    padded = np.concatenate([values[-(window // 2) :], values, values[: window - window // 2 - 1]])
    kernel = np.ones(window) / window
    return np.convolve(padded, kernel, mode="valid")


def _subject_profile(df: pd.DataFrame, sub_id: str, session: int, *, window: int) -> np.ndarray:
    row = df[(df["sub_id"] == sub_id) & (df["session"] == session)]
    if len(row) != 1:
        raise ValueError(f"expected exactly one row for {sub_id} session {session}, got {len(row)}")
    return _smooth_circular(err_vals(row["caps"].iloc[0]), window)


def group_profiles(df: pd.DataFrame, *, group: str | None = None, subgroup: str | None = None, sub_ids: list[str] | None = None, window: int = 1) -> np.ndarray:
    """One smoothed error profile per *subject* matching the filter (that
    subject's own sessions averaged together first), stacked into an
    (n_subjects, 85) array -- 19/48 subjects here have 2-3 FM100 sessions,
    so pooling by row instead would let them outweigh single-session
    subjects and pseudoreplicate the group SD, the same concern beh's
    unit='subject' default addresses. Public (not just plot_group_fm100's
    internal helper) so comparisons.py's estimate_offset (M2) can bootstrap
    over the same per-subject profiles without recomputing them."""
    if sub_ids is None:
        sub_ids = subjects_in_group(df, group=group, subgroup=subgroup)
    sub = df[df["sub_id"].isin(sub_ids)]
    profiles_by_subject = sub.groupby("sub_id")["caps"].apply(lambda caps_list: np.mean([_smooth_circular(err_vals(c), window) for c in caps_list], axis=0))
    return np.stack(profiles_by_subject.to_list())


def _radial_xy(x: np.ndarray, y: np.ndarray, *, kind: str) -> tuple[np.ndarray, np.ndarray]:
    """For kind='radial', append the first point again at the end so the
    plotted circle actually closes -- CAP_ANGLES uses endpoint=False (no
    angle repeats 0/2*pi), so without this cap 85 and cap 1 wouldn't
    connect, leaving a visible gap at the seam. No-op for kind='linear'."""
    if kind != "radial":
        return x, y
    return np.append(x, x[0] + 2 * np.pi), np.append(y, y[0])


def _new_axes(kind: str) -> plt.Axes:
    """New linear or polar axes, as plot_subject_fm100/plot_group_fm100/
    plot_subjects_fm100 each need when the caller doesn't pass their own
    ax= (none currently do for kind='radial' -- dashboard/pages/1_FM100.py
    always lets these functions create their own). Polar axes get
    theta_direction=-1 (M3): fm100radialTemplate.png's cap numbers grow
    clockwise, but matplotlib's own polar default is counterclockwise --
    set once here so every radial plot (data line, cap-wheel ring, angle
    ticks) shares the same rotational handedness, in the one place all
    three creation sites share."""
    _, ax = plt.subplots(subplot_kw={"projection": "polar"} if kind == "radial" else None)
    if kind == "radial":
        ax.set_theta_direction(-1)
    return ax


def _style_linear_axes(ax: plt.Axes, *, title: str | None = None) -> None:
    ax.set_xlim(1, N_CAPS)
    ax.set_xlabel("cap position")
    ax.set_ylabel("error")
    if title:
        ax.set_title(title)


RADIAL_TICK_STEP = 5  # every 5th cap gets a printed label on the radial diagram, in 'cap' label_mode


def _cap_label(position_index: int) -> int:
    """The FM100 test's own printed-diagram convention: the label sequence
    starts at 85 (not 1) at angle 0, then continues 1, 2, ... 84 -- the
    ordinary 1..85 label at each angular position, rotated back by one
    step (position_index 0 -> 85, 1 -> 1, 2 -> 2, ..., 84 -> 84)."""
    return ((position_index - 1) % N_CAPS) + 1


def _apply_cap_labels(ax: plt.Axes, *, step: int = RADIAL_TICK_STEP) -> None:
    """Replaces a radial plot's default angle-in-degrees tick labels with
    the FM100 test's own cap-number convention (_cap_label), one printed
    label every `step` cap positions (17 labels at the default step=5,
    legible without crowding the circle)."""
    indices = np.arange(0, N_CAPS, step)
    ax.set_xticks(CAP_ANGLES[indices])
    ax.set_xticklabels([str(_cap_label(i)) for i in indices])


CAP_WHEEL_CMAP = plt.cm.hsv  # cyclic colormap sampled at each cap's own angular position -- the caps sit on one continuous hue circle, so angular position doubles as an approximate hue (fm100radialTemplate.png)


def _draw_cap_wheel(ax: plt.Axes) -> None:
    """Draws a ring of N_CAPS colored dots just outside the plotted data
    (fm100radialTemplate.png's outer ring), one per cap position, colored
    by CAP_WHEEL_CMAP. Every cap gets a printed number (_cap_label
    convention) -- unlike _apply_cap_labels' every-Nth-cap default, the
    ring itself is the legend, so there's no crowding tradeoff to make.
    Rescales ax's r-limit (from its current auto-scaled data max) to leave
    room for the ring and its labels, and blanks the radial tick labels,
    which would otherwise collide with the ring."""
    r_data_max = ax.get_ylim()[1]
    r_ring = r_data_max * 1.15
    r_label = r_data_max * 1.3
    colors = CAP_WHEEL_CMAP(np.linspace(0, 1, N_CAPS, endpoint=False))
    ax.scatter(CAP_ANGLES, np.full(N_CAPS, r_ring), c=colors, s=40, zorder=5, edgecolor="white", linewidth=0.5)
    for i, angle in enumerate(CAP_ANGLES):
        ax.text(angle, r_label, str(_cap_label(i)), fontsize=5, ha="center", va="center")
    ax.set_ylim(0, r_label * 1.15)
    ax.set_yticklabels([])


def plot_subject_fm100(
    df: pd.DataFrame,
    sub_id: str,
    *,
    kind: str = "linear",
    sessions: list[int] | None = None,
    window: int = 1,
    label_mode: str = "angle",
    show_cap_wheel: bool = False,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """One participant's error profile, one line per session overlaid
    (at most 3 sessions in this dataset, colored like beh's
    plot_subject_sessions). kind='linear' or 'radial'. window is the
    circular moving-average size (1 = no smoothing). label_mode (radial
    only): 'angle' (default, matplotlib's own angle-in-degrees ticks) or
    'cap' (the FM100 test's own cap-number convention, _apply_cap_labels).
    show_cap_wheel (radial only): draws fm100radialTemplate.png's colored
    cap-number ring around the data (_draw_cap_wheel) instead of tick
    labels -- takes priority over label_mode when both are set, since the
    ring already carries every cap's number."""
    if kind not in ("linear", "radial"):
        raise ValueError(f"kind must be 'linear' or 'radial', got {kind!r}")
    if label_mode not in ("angle", "cap"):
        raise ValueError(f"label_mode must be 'angle' or 'cap', got {label_mode!r}")
    if sessions is None:
        sessions = sorted(df.loc[df["sub_id"] == sub_id, "session"].unique())
    if ax is None:
        ax = _new_axes(kind)

    x = CAP_ANGLES if kind == "radial" else CAP_POSITIONS
    for session, color in zip(sessions, SESSION_COLORS):
        profile = _subject_profile(df, sub_id, session, window=window)
        plot_x, plot_y = _radial_xy(x, profile, kind=kind)
        ax.plot(plot_x, plot_y, color=color, linewidth=2, label=f"session {session}")

    if kind == "linear":
        _style_linear_axes(ax, title=sub_id)
    else:
        ax.set_title(sub_id)
        if show_cap_wheel:
            _draw_cap_wheel(ax)
        elif label_mode == "cap":
            _apply_cap_labels(ax)
    ax.legend(fontsize=8)
    return ax


def plot_group_fm100(
    df: pd.DataFrame,
    categories: list[dict],
    *,
    kind: str = "linear",
    window: int = 1,
    label_mode: str = "angle",
    show_cap_wheel: bool = False,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """One line + shaded +-1 SD band per category -- categories is the same
    {"label", "group", "subgroup"} (or "sub_ids") shape used throughout this
    project. Each subject contributes one profile (their own sessions
    averaged first, see group_profiles) to that category's mean/SD, so the
    ±1 SD band reflects subject-to-subject spread, not session count.
    kind='linear' or 'radial'. label_mode (radial only): 'angle' (default)
    or 'cap' (see plot_subject_fm100). show_cap_wheel (radial only): see
    plot_subject_fm100 -- takes priority over label_mode when both are set.
    Up to len(FULL_PALETTE) (8) categories -- a line chart, so the dataviz
    skill's adjacent-pair color rule applies, not the stricter all-pairs
    scatter cap."""
    if kind not in ("linear", "radial"):
        raise ValueError(f"kind must be 'linear' or 'radial', got {kind!r}")
    if label_mode not in ("angle", "cap"):
        raise ValueError(f"label_mode must be 'angle' or 'cap', got {label_mode!r}")
    if len(categories) > len(FULL_PALETTE):
        raise ValueError(f"plot_group_fm100 supports at most {len(FULL_PALETTE)} categories, got {len(categories)}")
    if ax is None:
        ax = _new_axes(kind)

    x = CAP_ANGLES if kind == "radial" else CAP_POSITIONS
    for cat, color in zip(categories, FULL_PALETTE):
        profiles = group_profiles(df, group=cat.get("group"), subgroup=cat.get("subgroup"), sub_ids=cat.get("sub_ids"), window=window)
        mean, sd = profiles.mean(axis=0), profiles.std(axis=0, ddof=1)
        plot_x, plot_mean = _radial_xy(x, mean, kind=kind)
        _, plot_lower = _radial_xy(x, mean - sd, kind=kind)
        _, plot_upper = _radial_xy(x, mean + sd, kind=kind)
        ax.plot(plot_x, plot_mean, color=color, linewidth=2, label=f"{cat['label']} (n={len(profiles)})")
        ax.fill_between(plot_x, plot_lower, plot_upper, color=color, alpha=BAND_ALPHA, linewidth=0)

    if kind == "linear":
        _style_linear_axes(ax, title="Group FM100 error profile (mean ± 1 SD)")
    else:
        ax.set_title("Group FM100 error profile (mean ± 1 SD)")
        if show_cap_wheel:
            _draw_cap_wheel(ax)
        elif label_mode == "cap":
            _apply_cap_labels(ax)
    ax.legend(fontsize=8)
    return ax


def plot_subjects_fm100(
    df: pd.DataFrame,
    sub_ids: list[str],
    *,
    kind: str = "linear",
    window: int = 1,
    label_mode: str = "angle",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Multiple participants overlaid, one color each (dashboard M2). Unlike
    plot_subject_fm100 (one subject, one line per session), this always
    plots session 1 only per subject -- with several subjects already
    competing for color, adding a second line style per subject for session
    would overload the legend. Up to len(SUBJECT_COLORS) (4) subjects."""
    if len(sub_ids) > len(SUBJECT_COLORS):
        raise ValueError(f"plot_subjects_fm100 supports at most {len(SUBJECT_COLORS)} subjects, got {len(sub_ids)}")
    if kind not in ("linear", "radial"):
        raise ValueError(f"kind must be 'linear' or 'radial', got {kind!r}")
    if label_mode not in ("angle", "cap"):
        raise ValueError(f"label_mode must be 'angle' or 'cap', got {label_mode!r}")
    if ax is None:
        ax = _new_axes(kind)

    x = CAP_ANGLES if kind == "radial" else CAP_POSITIONS
    for sub_id, color in zip(sub_ids, SUBJECT_COLORS):
        profile = _subject_profile(df, sub_id, 1, window=window)
        plot_x, plot_y = _radial_xy(x, profile, kind=kind)
        ax.plot(plot_x, plot_y, color=color, linewidth=2, label=sub_id)

    if kind == "linear":
        _style_linear_axes(ax, title="Participants (session 1)")
    else:
        ax.set_title("Participants (session 1)")
        if label_mode == "cap":
            _apply_cap_labels(ax)
    ax.legend(fontsize=8)
    return ax


BOX_JITTER_WIDTH = 0.15
OUTLIER_LABEL_COLOR = "black"
INLIER_LABEL_COLOR = "#555555"


def plot_feature_boxplot(
    df: pd.DataFrame,
    feature: str,
    categories: list[dict],
    *,
    seed: int | None = 0,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """One box (Tukey 1.5xIQR whiskers, showfliers=False -- outliers are
    drawn as labeled scatter points instead of matplotlib's own flier
    markers) per category, with every subject's own value scattered on top
    (small horizontal jitter) and labeled with their id minus the 'MET'
    prefix (M3: spot which CTR/PD participants land inside another group's
    range, and which subjects look unlike their own group). Points
    comparisons.tukey_outlier_mask flags against their own category (the
    same 1.5xIQR rule the box itself is drawn with) get a black edge and a
    bold label instead of the default white edge/plain gray label -- an
    outlier stands out without a second legend. Label text always uses a
    fixed color (OUTLIER_LABEL_COLOR/INLIER_LABEL_COLOR), never the
    category color, so identity stays on the point, not the text (dataviz
    skill: text wears text tokens). Up to len(FULL_PALETTE) (8) categories,
    same {"label", "group"/"subgroup", or "sub_ids"} shape used throughout
    this project."""
    if len(categories) > len(FULL_PALETTE):
        raise ValueError(f"plot_feature_boxplot supports at most {len(FULL_PALETTE)} categories, got {len(categories)}")
    if ax is None:
        _, ax = plt.subplots()
    rng = np.random.default_rng(seed)

    tick_labels = []
    for i, (cat, color) in enumerate(zip(categories, FULL_PALETTE), start=1):
        pooled = group_pooled_scores(df, group=cat.get("group"), subgroup=cat.get("subgroup"))
        values = pooled[feature].to_numpy()
        outlier = tukey_outlier_mask(values)
        ax.boxplot(
            values,
            positions=[i],
            widths=0.5,
            showfliers=False,
            boxprops={"color": color, "linewidth": 1.5},
            medianprops={"color": color, "linewidth": 1.5},
            whiskerprops={"color": color, "linewidth": 1.5},
            capprops={"color": color, "linewidth": 1.5},
        )
        x = i + rng.uniform(-BOX_JITTER_WIDTH, BOX_JITTER_WIDTH, len(values))
        ax.scatter(x[~outlier], values[~outlier], color=color, alpha=0.8, edgecolor="white", linewidth=0.5, s=30, zorder=3)
        ax.scatter(x[outlier], values[outlier], color=color, alpha=0.9, edgecolor="black", linewidth=1.0, s=40, zorder=4)
        for xi, yi, sub_id, is_out in zip(x, values, pooled["sub_id"], outlier):
            ax.annotate(
                sub_id.removeprefix("MET"),
                (xi, yi),
                fontsize=6,
                xytext=(4, 2),
                textcoords="offset points",
                color=OUTLIER_LABEL_COLOR if is_out else INLIER_LABEL_COLOR,
                fontweight="bold" if is_out else "normal",
            )
        tick_labels.append(f"{cat['label']} (n={len(values)})")

    ax.set_xticks(range(1, len(categories) + 1))
    ax.set_xticklabels(tick_labels)
    ax.set_ylabel(feature)
    ax.set_title(feature)
    return ax


def plot_feature_boxplots_grid(
    df: pd.DataFrame,
    categories: list[dict],
    *,
    features: list[str] = FEATURES,
    seed: int | None = 0,
) -> plt.Figure:
    """plot_feature_boxplot, one panel per feature in a 2-column grid (M3:
    "flag outlier participants for each group", all six features at a
    glance)."""
    ncols = 2
    nrows = -(-len(features) // ncols)  # ceil
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 4 * nrows))
    axes = np.atleast_1d(axes).flatten()
    for ax, feature in zip(axes, features):
        plot_feature_boxplot(df, feature, categories, seed=seed, ax=ax)
    for ax in axes[len(features) :]:
        ax.axis("off")
    fig.tight_layout()
    return fig


def plot_group_vs_subjects_fm100(
    df: pd.DataFrame,
    categories: list[dict],
    sub_ids: list[str],
    *,
    kind: str = "linear",
    window: int = 1,
    label_mode: str = "angle",
    show_cap_wheel: bool = False,
) -> plt.Axes:
    """plot_group_fm100's category bands (solid line + shaded SD, same
    FULL_PALETTE colors) with individual participants' session-1 profiles
    (dashed, SUBJECT_COLORS) overlaid on the same axes (dashboard M2, "compare
    a group to one or more participants"). Dashed vs. solid is the
    distinguishing encoding, not color alone, since a subject's color can
    coincide with an unrelated category's -- consistent with the dataviz
    skill's "identity is never color-alone" rule. show_cap_wheel (radial
    only): see plot_subject_fm100 -- drawn last, after the subject overlays
    below, not inside the plot_group_fm100 call: _draw_cap_wheel calls
    ax.set_ylim, which disables further autoscaling, so drawing it before
    the overlays would silently clip any subject line reaching past the
    group bands' own range. Up to len(SUBJECT_COLORS) (4) subjects;
    categories follows plot_group_fm100's own cap."""
    if len(sub_ids) > len(SUBJECT_COLORS):
        raise ValueError(f"plot_group_vs_subjects_fm100 supports at most {len(SUBJECT_COLORS)} subjects, got {len(sub_ids)}")
    inner_label_mode = "angle" if show_cap_wheel else label_mode  # avoid an _apply_cap_labels call show_cap_wheel is about to override anyway
    ax = plot_group_fm100(df, categories, kind=kind, window=window, label_mode=inner_label_mode, show_cap_wheel=False)

    x = CAP_ANGLES if kind == "radial" else CAP_POSITIONS
    for sub_id, color in zip(sub_ids, SUBJECT_COLORS):
        profile = _subject_profile(df, sub_id, 1, window=window)
        plot_x, plot_y = _radial_xy(x, profile, kind=kind)
        ax.plot(plot_x, plot_y, color=color, linewidth=2, linestyle="--", label=f"{sub_id} (individual)")

    if kind == "radial" and show_cap_wheel:
        _draw_cap_wheel(ax)
    ax.legend(fontsize=8)
    return ax
