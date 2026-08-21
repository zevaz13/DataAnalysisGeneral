"""Overlap between behavioral click density and the EEG (SSVEP grid)
response -- does a participant's/group's behavioral metamer estimate
spatially agree with where the EEG response is weakest?

Refactored from ssvepBeh/templateCode/grid_mapping.py's
closest_grid_indices/permWeighted2Dshifts.

**Orientation bug found and fixed.** The template's closest_grid_indices
returns a second value, outMat = subs.T, described as matching "MATLAB
orientation" -- that is [green_idx, red_idx], the same axis-swap bug
ssveps/ already found and fixed once (docs/ssvep_summary.md finding 2.1,
where ssveps/scripts/loader.py's own runMap unpacking had red and green
swapped). Verified empirically on real data (MET001): the behavioral
centroid's nearest grid cell is (red_idx=5, green_idx=4); the untransposed
idx/subs peaks there correctly, outMat peaks at (4, 5) -- swapped. This
module therefore builds its density map directly from idx (never outMat),
so it is genuinely [red_idx, green_idx] like every ssveps/ grid -- pinned by
tests/test_ssvepbeh.py's own version of ssveps' own
test_loader_reads_runmap_green_first regression test.

Every function here takes beh_df/runmap_df/baselines_df/metadata_df as
already-loaded DataFrames (the caller's job, e.g. beh's load_behavioral and
ssveps' analysis.load_* in a notebook) -- so the only cross-project
dependency this module itself needs is ssveps/scripts/analysis.py, for grid
access, normalization, and trough location.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_SSVEPS_SCRIPTS = str(Path(__file__).resolve().parents[2] / "ssveps" / "scripts")
if _SSVEPS_SCRIPTS not in sys.path:
    sys.path.insert(0, _SSVEPS_SCRIPTS)

import analysis  # noqa: E402 -- ssveps/scripts/analysis.py; "analysis" is a unique name repo-wide, no loader.py/plotting.py collision risk

DEFAULT_RED = np.array([0, 355.6, 711.1, 1066.7, 1422.2, 1777.8, 2133.3, 2488.9, 2844.4, 3200.0])
DEFAULT_GREEN = np.array([0, 222.2, 444.4, 666.7, 888.9, 1111.1, 1333.3, 1555.6, 1777.8, 2000.0])


def closest_grid_indices(points: np.ndarray, *, red: np.ndarray = DEFAULT_RED, green: np.ndarray = DEFAULT_GREEN) -> np.ndarray:
    """Nearest (red_idx, green_idx) grid cell for each (red, green) point,
    shape (N, 2) -- genuinely [red_idx, green_idx] (see module docstring)."""
    points = np.asarray(points)
    red_idx = np.argmin(np.abs(red.reshape(1, -1) - points[:, 0].reshape(-1, 1)), axis=1)
    green_idx = np.argmin(np.abs(green.reshape(1, -1) - points[:, 1].reshape(-1, 1)), axis=1)
    return np.column_stack([red_idx, green_idx])


def behavioral_density_map(beh_df: pd.DataFrame, sub_ids: list[str], *, red: np.ndarray = DEFAULT_RED, green: np.ndarray = DEFAULT_GREEN) -> np.ndarray:
    """Count of clicks per grid cell, pooled across every session/click of
    every subject in sub_ids -- shape (len(red), len(green)),
    [red_idx, green_idx]. Pass a single-element list for one participant, or
    a whole group's sub_ids to pool (see group_overlap)."""
    sub = beh_df[beh_df["sub_id"].isin(sub_ids)]
    idx = closest_grid_indices(sub[["red", "green"]].to_numpy(), red=red, green=green)
    counts = np.zeros((len(red), len(green)), dtype=int)
    for red_idx, green_idx in idx:
        counts[red_idx, green_idx] += 1
    return counts


def weighted_overlap_test(B: np.ndarray, E: np.ndarray, *, n_perm: int = 5000, seed: int | None = None) -> dict:
    """Toroidal-shift permutation test for whether clicks (B) concentrate
    where the EEG response (E) is low, more than chance predicts.

    B: a behavioral click-density grid (behavioral_density_map). E: an EEG
    response grid, same shape and [red_idx, green_idx] orientation (e.g.
    analysis.mean_grid/mean_grid_across_subjects).

    Seeded (np.random.default_rng), unlike the template's unseeded
    np.random.randint -- same reproducibility convention as
    ssveps/scripts/permutation.py.

    Returns {p_value, obs_stat, null_stats}. obs_stat = sum(E * B/B.sum());
    p_value is one-sided, P(null_stat <= obs_stat) -- the probability a
    random click layout would concentrate on E's low values at least as much
    as the real one does."""
    B = np.asarray(B, dtype=float)
    E = np.asarray(E, dtype=float)
    if B.shape != E.shape:
        raise ValueError(f"B and E must have the same shape, got {B.shape} and {E.shape}")
    total_b = B.sum()
    if total_b == 0:
        raise ValueError("B contains no clicks")

    b_norm = B / total_b
    obs_stat = float(np.sum(E * b_norm))

    rng = np.random.default_rng(seed)
    n_rows, n_cols = B.shape
    null_stats = np.array([np.sum(E * np.roll(b_norm, shift=(rng.integers(n_rows), rng.integers(n_cols)), axis=(0, 1))) for _ in range(n_perm)])

    p_value = float(np.mean(null_stats <= obs_stat))
    return {"p_value": p_value, "obs_stat": obs_stat, "null_stats": null_stats}


def subject_overlap(
    beh_df: pd.DataFrame,
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_id: str,
    session: int,
    *,
    normalize: dict | None = analysis.DEFAULT_NORMALIZE,
    n_perm: int = 5000,
    seed: int | None = None,
) -> dict:
    """weighted_overlap_test for one participant: B from their own clicks
    (behavioral_density_map), E from their mean EEG grid (analysis.mean_grid).
    normalize is analysis.mean_grid's own parameter (a scope/trials/method
    dict, or None for raw) -- exposed here rather than fixed, since which
    normalization is most appropriate for this comparison is still an open
    question."""
    B = behavioral_density_map(beh_df, [sub_id])
    E = analysis.mean_grid(runmap_df, baselines_df, sub_id, session, normalize=normalize)
    return weighted_overlap_test(B, E, n_perm=n_perm, seed=seed)


def group_overlap(
    beh_df: pd.DataFrame,
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    session: int,
    *,
    group: str | None = None,
    subgroup: str | None = None,
    sub_ids: list[str] | None = None,
    normalize: dict | None = analysis.DEFAULT_NORMALIZE,
    n_perm: int = 5000,
    seed: int | None = None,
) -> dict:
    """weighted_overlap_test for a group: every matching subject's clicks
    pooled into one B (behavioral_density_map), their EEG grids averaged
    into one E (analysis.mean_grid_across_subjects) -- one test per group,
    not one test per subject. Pass sub_ids for an arbitrary hand-picked set
    instead of a group/subgroup filter (same convention as beh/ssveps)."""
    if sub_ids is None:
        sub_ids = analysis.subjects_in_group(metadata_df, session, group=group, subgroup=subgroup)
    B = behavioral_density_map(beh_df, sub_ids)
    E = analysis.mean_grid_across_subjects(runmap_df, baselines_df, sub_ids, session, normalize=normalize)
    result = weighted_overlap_test(B, E, n_perm=n_perm, seed=seed)
    result["n_subjects"] = len(sub_ids)
    return result


def centroid_distance(
    beh_df: pd.DataFrame,
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_id: str,
    session: int,
    *,
    normalize: dict | None = analysis.DEFAULT_NORMALIZE,
) -> dict:
    """A second, simpler overlap metric: Euclidean distance between a
    participant's behavioral centroid (mean red/green across every click)
    and their EEG trough location (analysis.trough_location's argmin,
    native grid resolution). Complements weighted_overlap_test's spatial
    density comparison with a single interpretable number per subject.

    Returns {beh_red, beh_green, eeg_red, eeg_green, distance}."""
    clicks = beh_df.loc[beh_df["sub_id"] == sub_id, ["red", "green"]]
    beh_red, beh_green = clicks["red"].mean(), clicks["green"].mean()

    red_vals, green_vals = analysis.load_grid_axes()
    grid = analysis.mean_grid(runmap_df, baselines_df, sub_id, session, normalize=normalize)
    trough = analysis.trough_location(grid, red_vals, green_vals)

    distance = float(np.hypot(beh_red - trough["red"], beh_green - trough["green"]))
    return {"beh_red": float(beh_red), "beh_green": float(beh_green), "eeg_red": trough["red"], "eeg_green": trough["green"], "distance": distance}
