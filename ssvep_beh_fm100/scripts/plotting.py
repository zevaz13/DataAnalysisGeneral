"""Plots for the severity (CCA) and type/axis (circular correlation) tests,
and the cross-session reliability table -- M1, PLANssvep_bh_fm100.md.
"""

import matplotlib.pyplot as plt
import numpy as np

POINT_COLOR = "#2a78d6"
NULL_COLOR = "#898781"  # muted ink, for a null distribution -- not a data series


def plot_canonical_variates(cca_result: dict, *, x_label: str = "X canonical variate", y_label: str = "Y canonical variate", ax: plt.Axes | None = None) -> plt.Axes:
    """Scatter of the observed CCA fit's canonical variates (one point per
    subject) -- the relationship severity.cca_test's r/p_value describe
    visually. cca_result is cca_test's return dict."""
    if ax is None:
        _, ax = plt.subplots()
    ax.scatter(cca_result["x_scores"], cca_result["y_scores"], color=POINT_COLOR, alpha=0.8, edgecolor="white", s=60)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(f"r={cca_result['r']:.3f}, p={cca_result['p_value']:.4f} (n={len(cca_result['x_scores'])})")
    return ax


def plot_null_distribution(cca_result: dict, *, ax: plt.Axes | None = None) -> plt.Axes:
    """Histogram of the permutation null (null_r) with the observed r drawn
    as a vertical line -- makes explicit how extreme (or not) the observed
    canonical correlation is relative to chance, given CCA's raw r is not
    interpretable on its own (see severity.py's module docstring)."""
    if ax is None:
        _, ax = plt.subplots()
    ax.hist(cca_result["null_r"], bins=40, color=NULL_COLOR, alpha=0.7)
    ax.axvline(cca_result["r"], color=POINT_COLOR, linewidth=2, label=f"observed r={cca_result['r']:.3f}")
    ax.set_xlabel("canonical correlation")
    ax.set_ylabel("count (permutations)")
    ax.legend(fontsize=8)
    return ax


def plot_circular_scatter(angles_deg_x: np.ndarray, angles_deg_y: np.ndarray, *, x_label: str = "X angle (deg)", y_label: str = "Y angle (deg)", ax: plt.Axes | None = None) -> plt.Axes:
    """Scatter of two 180deg-periodic angle arrays -- gridlines at 0/180
    mark the wrap point, since two points near opposite edges (e.g. 179deg
    and 1deg) are actually close together, not far apart."""
    if ax is None:
        _, ax = plt.subplots()
    ax.scatter(angles_deg_x, angles_deg_y, color=POINT_COLOR, alpha=0.8, edgecolor="white", s=60)
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 180)
    ax.set_xticks([0, 45, 90, 135, 180])
    ax.set_yticks([0, 45, 90, 135, 180])
    ax.axvline(0, color="#c3c2b7", linewidth=1)
    ax.axvline(180, color="#c3c2b7", linewidth=1)
    ax.axhline(0, color="#c3c2b7", linewidth=1)
    ax.axhline(180, color="#c3c2b7", linewidth=1)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    return ax


def plot_reliability_table(reliability_df, *, ax: plt.Axes | None = None) -> plt.Axes:
    """Bar chart of each feature's cross-session reliability statistic
    (ICC or circular r, from fm100_features.reliability_table), with the
    p-value annotated above each bar."""
    if ax is None:
        _, ax = plt.subplots()
    colors = [POINT_COLOR if p < 0.05 else NULL_COLOR for p in reliability_df["p_value"]]
    ax.bar(reliability_df["feature"], reliability_df["value"], color=colors)
    for i, (value, p_value) in enumerate(zip(reliability_df["value"], reliability_df["p_value"])):
        ax.text(i, value + 0.03, f"p={p_value:.3f}", ha="center", fontsize=8)
    ax.set_ylim(-1, 1.1)  # ICC and circular r can both dip negative, unlike a plain [0,1] correlation magnitude
    ax.set_ylabel("ICC / circular r")
    ax.axhline(0, color="#c3c2b7", linewidth=1)
    return ax
