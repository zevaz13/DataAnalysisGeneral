"""Per-subject shape features from PCA on each subject's pooled (red, green)
clicks -- orientation, along-line spread, and perpendicular tightness, as a
complement to comparisons.py's group-mean Hotelling T^2 (M2, PLANbeh.md).

M1's subject-mean Hotelling T^2 already separated every group pair on
centroid location alone, including protan vs deutan. These features instead
describe each subject's line *shape*: where it points (orientation), how far
clicks spread along it (along_var), and how tightly they cluster off of it
(perp_var) -- protan and deutan clouds were noted as differing in shape as
much as position.

orientation_deg is folded into [0, 180) -- a fitted line has no direction, so
0deg and 180deg are the same orientation. This means group comparisons on
orientation_deg (compare_shape_feature) assume a group's angles don't
straddle the 0/180 wrap point; true for this dataset's isoluminance lines
(consistently positive slope, well clear of the wrap), but not a fully
circular-safe statistic in general.
"""

import numpy as np
import pandas as pd
import pingouin as pg

from loader import subjects_in_group


def _subject_pca(df: pd.DataFrame, sub_id: str) -> dict:
    points = df.loc[df["sub_id"] == sub_id, ["red", "green"]].to_numpy()
    if len(points) < 2:
        raise ValueError(f"{sub_id} has fewer than 2 points ({len(points)}), can't fit a PCA line")
    mean = points.mean(axis=0)
    centered = points - mean
    eigvals, eigvecs = np.linalg.eigh(np.cov(centered, rowvar=False))  # ascending
    return {"mean": mean, "centered": centered, "pc1": eigvecs[:, 1], "along_var": eigvals[1], "perp_var": eigvals[0], "n": len(points)}


def subject_shape_features(df: pd.DataFrame, sub_id: str) -> dict:
    """PCA on one subject's pooled (red, green) clicks (every session).

    Returns {orientation_deg, along_var, perp_var, n}:
    - orientation_deg: angle of the first principal component, folded into
      [0, 180).
    - along_var: variance along that first component (spread along the
      fitted line).
    - perp_var: variance along the second component (scatter off the line --
      how tight/consistent the match is).

    Needs at least 2 points; raises ValueError otherwise."""
    fit = _subject_pca(df, sub_id)
    orientation_deg = float(np.degrees(np.arctan2(fit["pc1"][1], fit["pc1"][0])) % 180)
    return {"orientation_deg": orientation_deg, "along_var": float(fit["along_var"]), "perp_var": float(fit["perp_var"]), "n": fit["n"]}


def subject_pca_line(df: pd.DataFrame, sub_id: str) -> tuple[np.ndarray, np.ndarray]:
    """Endpoints of the fitted PCA line, spanning the subject's actual data
    extent along the first principal component -- for overlaying on a cloud
    plot (plotting.plot_subject_cloud's show_fit)."""
    fit = _subject_pca(df, sub_id)
    proj = fit["centered"] @ fit["pc1"]
    return fit["mean"] + proj.min() * fit["pc1"], fit["mean"] + proj.max() * fit["pc1"]


def group_features(df: pd.DataFrame, *, group: str | None = None, subgroup: str | None = None) -> pd.DataFrame:
    """subject_shape_features for every subject in a group/subgroup, one row
    per subject, indexed by sub_id."""
    sub_ids = subjects_in_group(df, group=group, subgroup=subgroup)
    rows = {sub_id: subject_shape_features(df, sub_id) for sub_id in sub_ids}
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("sub_id")


def compare_shape_feature(
    df: pd.DataFrame,
    feature: str,
    *,
    group1: str | None = None,
    subgroup1: str | None = None,
    group2: str | None = None,
    subgroup2: str | None = None,
) -> dict:
    """Mann-Whitney U test + effect size (pingouin.mwu) on one shape feature
    between two groups/subgroups. feature is one of subject_shape_features's
    keys ('orientation_deg', 'along_var', 'perp_var').

    Returns {feature, u_val, p_value, rbc, cles, n1, n2}. rbc (rank-biserial
    correlation) and cles (common language effect size) come straight from
    pingouin -- unlike Hotelling T^2's single omnibus stat, this is
    per-feature, so run it once per feature to see which shape property (if
    any) drives a given group difference."""
    x = group_features(df, group=group1, subgroup=subgroup1)[feature]
    y = group_features(df, group=group2, subgroup=subgroup2)[feature]
    result = pg.mwu(x, y)
    return {
        "feature": feature,
        "u_val": float(result["U_val"].iloc[0]),
        "p_value": float(result["p_val"].iloc[0]),
        "rbc": float(result["RBC"].iloc[0]),
        "cles": float(result["CLES"].iloc[0]),
        "n1": len(x),
        "n2": len(y),
    }
