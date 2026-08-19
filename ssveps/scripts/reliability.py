"""Test-retest reliability (session 1 vs. session 2) via per-pixel ICC.

Replicates ssveps/templateCode/ICCs/computeICC_gridMaps.m: for a set of
subjects with both sessions, compute each subject's session 1 and session 2
mean grids, then for every one of the 100 grid cells, compute the
intraclass correlation coefficient between the two sessions across subjects
-- an "ICC map" showing which pixels are more or less reliable test-retest.

Uses pingouin's intraclass_corr, whose 'ICC(A,1)' row (two-way random,
absolute agreement, single measurement -- McGraw & Wong 1996 notation)
matches the template's MATLAB ICC(..., 'A-1') exactly.
"""

import numpy as np
import pandas as pd
import pingouin as pg

from analysis import DEFAULT_NORMALIZE, mean_grid, subjects_in_group


def paired_subjects(metadata_df: pd.DataFrame, *, group: str | None = None, subgroup: str | None = None) -> list[str]:
    """Subject IDs present at both session 1 and session 2, optionally
    filtered by group/subgroup (checked at session 1)."""
    session1 = set(subjects_in_group(metadata_df, 1, group=group, subgroup=subgroup))
    session2 = set(subjects_in_group(metadata_df, 2))
    return sorted(session1 & session2)


def icc_grid(
    runmap_df: pd.DataFrame, baselines_df: pd.DataFrame, sub_ids: list[str], *, normalize: dict | None = DEFAULT_NORMALIZE
) -> pd.DataFrame:
    """Per-pixel ICC(A,1) between session 1 and session 2 mean grids, across
    sub_ids (each must have both sessions -- see paired_subjects). Returns a
    tidy DataFrame (red_idx, green_idx, icc, ci_lower, ci_upper, f, df1, df2,
    pval), one row per grid cell -- pivot to a 10x10 array with icc_map()."""
    if len(sub_ids) < 3:
        raise ValueError(
            f"icc_grid needs at least 3 paired subjects, got {len(sub_ids)} -- pingouin's underlying "
            "ANOVA requires >=5 (subject x session) rows. protan/deutan alone don't have enough paired "
            "subjects in this project's data (see docs/api_reference.md's reliability.py section)."
        )
    grids1 = np.stack([mean_grid(runmap_df, baselines_df, sid, 1, normalize=normalize) for sid in sub_ids])
    grids2 = np.stack([mean_grid(runmap_df, baselines_df, sid, 2, normalize=normalize) for sid in sub_ids])
    n_red, n_green = grids1.shape[1:]
    n_sub = len(sub_ids)

    rows = []
    for red_idx in range(n_red):
        for green_idx in range(n_green):
            pixel_df = pd.DataFrame(
                {
                    "subject": np.tile(np.arange(n_sub), 2),
                    "session": np.repeat([1, 2], n_sub),
                    "value": np.concatenate([grids1[:, red_idx, green_idx], grids2[:, red_idx, green_idx]]),
                }
            )
            result = pg.intraclass_corr(data=pixel_df, targets="subject", raters="session", ratings="value")
            icc_a1 = result[result["Type"] == "ICC(A,1)"].iloc[0]
            ci_lower, ci_upper = icc_a1["CI95"]
            rows.append(
                {
                    "red_idx": red_idx,
                    "green_idx": green_idx,
                    "icc": icc_a1["ICC"],
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "f": icc_a1["F"],
                    "df1": icc_a1["df1"],
                    "df2": icc_a1["df2"],
                    "pval": icc_a1["pval"],
                }
            )
    return pd.DataFrame(rows)


def icc_map(icc_df: pd.DataFrame) -> np.ndarray:
    """Pivot icc_grid's tidy output into a [red_idx, green_idx] 10x10 array of ICC values."""
    return icc_df.pivot(index="red_idx", columns="green_idx", values="icc").sort_index().sort_index(axis=1).to_numpy()


def session_pair_values(
    runmap_df: pd.DataFrame, baselines_df: pd.DataFrame, sub_ids: list[str], red_idx: int, green_idx: int, *, normalize: dict | None = DEFAULT_NORMALIZE
) -> tuple[np.ndarray, np.ndarray]:
    """Session 1 and session 2 values at one grid cell, across sub_ids -- the
    raw paired data behind one icc_grid row, for e.g. a Bland-Altman plot."""
    values1 = np.array([mean_grid(runmap_df, baselines_df, sid, 1, normalize=normalize)[red_idx, green_idx] for sid in sub_ids])
    values2 = np.array([mean_grid(runmap_df, baselines_df, sid, 2, normalize=normalize)[red_idx, green_idx] for sid in sub_ids])
    return values1, values2


# The template's (ICC_grids_22oct25.m) own 5 example (red, green) targets --
# kept as literal values so results stay comparable to the original MATLAB
# analysis, snapped to whichever grid this project's data uses.
_TEMPLATE_EXAMPLE_TARGETS = [(0, 1111), (2488, 222), (3200, 1333), (711, 1777), (2133, 2000)]


def example_points_fixed(red_vals: list[float], green_vals: list[float]) -> list[dict]:
    """The template's 5 hardcoded example points, snapped to the nearest grid
    index. Fixed regardless of the data -- useful for comparing against the
    original MATLAB analysis, but not chosen for being informative here."""
    red_arr, green_arr = np.array(red_vals), np.array(green_vals)
    points = []
    for i, (red, green) in enumerate(_TEMPLATE_EXAMPLE_TARGETS, start=1):
        points.append(
            {
                "label": f"point {i}",
                "red_idx": int(np.argmin(np.abs(red_arr - red))),
                "green_idx": int(np.argmin(np.abs(green_arr - green))),
            }
        )
    return points


def example_points_informative(icc_df: pd.DataFrame, *, trough_red_idx: int | None = None, trough_green_idx: int | None = None) -> list[dict]:
    """Data-driven example points from an icc_grid result: the pixel with the
    lowest ICC (worst test-retest reliability) and the pixel with the highest
    ICC (best), plus -- if given -- the group's own trough location (compose
    with analysis.trough_location/group_troughs), the pixel this project
    actually cares about scientifically."""
    worst = icc_df.loc[icc_df["icc"].idxmin()]
    best = icc_df.loc[icc_df["icc"].idxmax()]
    points = [
        {"label": "lowest ICC", "red_idx": int(worst["red_idx"]), "green_idx": int(worst["green_idx"])},
        {"label": "highest ICC", "red_idx": int(best["red_idx"]), "green_idx": int(best["green_idx"])},
    ]
    if trough_red_idx is not None and trough_green_idx is not None:
        points.append({"label": "trough", "red_idx": trough_red_idx, "green_idx": trough_green_idx})
    return points
