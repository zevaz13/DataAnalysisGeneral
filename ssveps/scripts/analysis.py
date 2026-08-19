"""Load tidy SSVEP files and compute baseline-normalized grids.

Baseline trial order (confirmed): trials 1-2 are pre-grid, 3-4 are post-grid.
"""

import json
import os

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "files")

TRIAL_SUBSETS = {"all": (1, 2, 3, 4), "first2": (1, 2), "last2": (3, 4)}

# Depth is normalized by default (percent change from baseline) since raw SSVEP
# amplitude varies a lot subject-to-subject, so only normalized depth is
# comparable across subjects/groups.
DEFAULT_TROUGH_NORMALIZE = {"scope": "run", "trials": "all", "method": "percent"}


def load_runmap() -> pd.DataFrame:
    return pd.read_csv(os.path.join(FILES_DIR, "runmap.csv"))


def load_baselines() -> pd.DataFrame:
    return pd.read_csv(os.path.join(FILES_DIR, "baselines.csv"))


def load_metadata() -> pd.DataFrame:
    # keep_default_na=False: subgroup's literal "NA" value must not become NaN
    return pd.read_csv(os.path.join(FILES_DIR, "metadata.csv"), keep_default_na=False)


def load_grid_axes() -> tuple[list[float], list[float]]:
    with open(os.path.join(FILES_DIR, "grid.json")) as f:
        grid = json.load(f)
    return grid["redArray"], grid["greenArray"]


def raw_grid(runmap_df: pd.DataFrame, sub_id: str, session: int, run: int) -> np.ndarray:
    """10x10 (red_idx, green_idx) grid of raw runMap values for one run."""
    sub = runmap_df.query("sub_id == @sub_id and session == @session and run == @run")
    return sub.pivot(index="red_idx", columns="green_idx", values="value").sort_index().sort_index(axis=1).to_numpy()


def mean_raw_grid(runmap_df: pd.DataFrame, sub_id: str, session: int) -> np.ndarray:
    """Mean raw grid across all runs of a session."""
    sub = runmap_df.query("sub_id == @sub_id and session == @session")
    pivoted = sub.groupby(["red_idx", "green_idx"])["value"].mean().unstack()
    return pivoted.sort_index().sort_index(axis=1).to_numpy()


def baseline_values(
    baselines_df: pd.DataFrame, sub_id: str, session: int, *, scope: str = "run", run: int | None = None, trials: str = "all"
) -> np.ndarray:
    """Selected baseline trial values: one run's own trials (scope='run'), or
    pooled across every run of the session (scope='session')."""
    trial_nums = TRIAL_SUBSETS[trials]
    sub = baselines_df.query("sub_id == @sub_id and session == @session and trial in @trial_nums")
    if scope == "run":
        if run is None:
            raise ValueError("scope='run' requires a run")
        sub = sub.query("run == @run")
    elif scope != "session":
        raise ValueError(f"unknown scope: {scope}")
    return sub["value"].to_numpy()


def normalize_grid(raw: np.ndarray, baseline_vals: np.ndarray, *, method: str = "percent") -> np.ndarray:
    """Normalize a raw grid against a scalar baseline derived from baseline_vals."""
    base_mean = baseline_vals.mean()
    if method == "percent":
        return (raw - base_mean) / base_mean
    if method == "db":
        return 10 * np.log10(raw / base_mean)
    if method == "zscore":
        return (raw - base_mean) / baseline_vals.std()
    raise ValueError(f"unknown method: {method}")


def normalized_grid(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_id: str,
    session: int,
    run: int,
    *,
    scope: str = "run",
    trials: str = "all",
    method: str = "percent",
) -> np.ndarray:
    raw = raw_grid(runmap_df, sub_id, session, run)
    bvals = baseline_values(baselines_df, sub_id, session, scope=scope, run=run, trials=trials)
    return normalize_grid(raw, bvals, method=method)


def _run_grids(
    runmap_df: pd.DataFrame, baselines_df: pd.DataFrame, sub_id: str, session: int, normalize: dict | None
) -> list[np.ndarray]:
    """Each run's grid (raw or normalized) for one subject/session, in run order."""
    runs = sorted(runmap_df.query("sub_id == @sub_id and session == @session")["run"].unique())
    if normalize is None:
        return [raw_grid(runmap_df, sub_id, session, run) for run in runs]
    return [normalized_grid(runmap_df, baselines_df, sub_id, session, run, **normalize) for run in runs]


def mean_grid(
    runmap_df: pd.DataFrame, baselines_df: pd.DataFrame, sub_id: str, session: int, *, normalize: dict | None = None
) -> np.ndarray:
    """Mean grid across all runs of one subject/session, raw or normalized
    (normalize, if given, is a scope/trials/method dict for normalized_grid;
    each run is normalized individually, then the runs are averaged)."""
    if normalize is None:
        return mean_raw_grid(runmap_df, sub_id, session)
    return np.mean(_run_grids(runmap_df, baselines_df, sub_id, session, normalize), axis=0)


def flatten_runs(
    runmap_df: pd.DataFrame, baselines_df: pd.DataFrame, sub_id: str, session: int, *, normalize: dict | None = None
) -> np.ndarray:
    """Every pixel of every run of one subject/session, concatenated into one
    1D array (400 values for 4-run subjects, 300 for the ragged 3-run ones)."""
    grids = _run_grids(runmap_df, baselines_df, sub_id, session, normalize)
    return np.concatenate([g.ravel() for g in grids])


def pooled_pixels(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_ids: list[str],
    session: int,
    *,
    normalize: dict | None = None,
) -> np.ndarray:
    """flatten_runs for every subject in sub_ids, concatenated into one pooled
    1D array (a group's entire raw pixel distribution, not averaged)."""
    return np.concatenate([flatten_runs(runmap_df, baselines_df, sub_id, session, normalize=normalize) for sub_id in sub_ids])


def subjects_in_group(
    metadata_df: pd.DataFrame, session: int, *, group: str | None = None, subgroup: str | None = None
) -> list[str]:
    """Subject IDs at a given session, optionally filtered by group and/or subgroup."""
    sub = metadata_df.query("session == @session")
    if group is not None:
        sub = sub.query("group == @group")
    if subgroup is not None:
        sub = sub.query("subgroup == @subgroup")
    return sorted(sub["sub_id"].unique())


def mean_grid_across_subjects(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    sub_ids: list[str],
    session: int,
    *,
    normalize: dict | None = None,
) -> np.ndarray:
    """Mean of each subject's own mean-across-runs grid (each subject weighted equally)."""
    grids = [mean_grid(runmap_df, baselines_df, sub_id, session, normalize=normalize) for sub_id in sub_ids]
    return np.mean(grids, axis=0)


def group_grid(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    session: int,
    *,
    group: str | None = None,
    subgroup: str | None = None,
    normalize: dict | None = None,
) -> np.ndarray:
    """Aggregated mean grid across every subject at this session matching
    group/subgroup (every subject at that session if neither is given).
    Convenience wrapper composing subjects_in_group + mean_grid_across_subjects
    for reuse outside of plotting (e.g. further stats, group difference maps)."""
    sub_ids = subjects_in_group(metadata_df, session, group=group, subgroup=subgroup)
    return mean_grid_across_subjects(runmap_df, baselines_df, sub_ids, session, normalize=normalize)


def interpolate_grid(grid: np.ndarray, shape: tuple[int, int], *, method: str = "linear") -> np.ndarray:
    """Resize a (red_idx, green_idx) grid to a new (n_red, n_green) resolution."""
    n_red, n_green = grid.shape
    interpolator = RegularGridInterpolator((np.arange(n_red), np.arange(n_green)), grid, method=method)
    new_red_n, new_green_n = shape
    red_q, green_q = np.linspace(0, n_red - 1, new_red_n), np.linspace(0, n_green - 1, new_green_n)
    query_red, query_green = np.meshgrid(red_q, green_q, indexing="ij")
    return interpolator(np.stack([query_red.ravel(), query_green.ravel()], axis=-1)).reshape(new_red_n, new_green_n)


def trough_location(grid: np.ndarray, red_vals: list[float], green_vals: list[float]) -> dict:
    """Location and depth of a grid's minimum: physical red/green values, their
    red_idx/green_idx grid positions, and the depth (the minimum value itself).
    Native grid resolution only -- no interpolation (a finer, noise-resistant
    localization via a parametric surface fit is planned separately for M4)."""
    red_idx, green_idx = np.unravel_index(np.argmin(grid), grid.shape)
    return {
        "red": red_vals[red_idx],
        "green": green_vals[green_idx],
        "depth": grid[red_idx, green_idx],
        "red_idx": red_idx,
        "green_idx": green_idx,
    }


def subject_troughs(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    *,
    normalize: dict | None = DEFAULT_TROUGH_NORMALIZE,
) -> pd.DataFrame:
    """One row per (sub_id, session) in metadata_df: the minimum location and
    depth of that subject's mean-across-runs grid. normalize=None for raw
    depth, otherwise a scope/trials/method dict as elsewhere."""
    red_vals, green_vals = load_grid_axes()
    rows = []
    for meta in metadata_df.to_dict("records"):
        grid = mean_grid(runmap_df, baselines_df, meta["sub_id"], meta["session"], normalize=normalize)
        loc = trough_location(grid, red_vals, green_vals)
        rows.append({"sub_id": meta["sub_id"], "session": meta["session"], "group": meta["group"], "subgroup": meta["subgroup"], **loc})
    return pd.DataFrame(rows)


def group_troughs(
    runmap_df: pd.DataFrame,
    baselines_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    sessions: list[int],
    categories: list[dict],
    *,
    normalize: dict | None = DEFAULT_TROUGH_NORMALIZE,
) -> pd.DataFrame:
    """One row per (session, category) with at least one subject: the minimum
    location and depth of that category's mean-of-subject-means grid.
    categories as in plotting.plot_groups_side_by_side -- categories with no
    subjects at a given session (e.g. deutan at session 2) are skipped."""
    red_vals, green_vals = load_grid_axes()
    rows = []
    for session in sessions:
        for cat in categories:
            sub_ids = subjects_in_group(metadata_df, session, group=cat.get("group"), subgroup=cat.get("subgroup"))
            if not sub_ids:
                continue
            grid = mean_grid_across_subjects(runmap_df, baselines_df, sub_ids, session, normalize=normalize)
            loc = trough_location(grid, red_vals, green_vals)
            rows.append({"label": cat["label"], "session": session, "n": len(sub_ids), **loc})
    return pd.DataFrame(rows)
