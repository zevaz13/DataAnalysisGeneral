"""Regression tests for the ssvepBeh (behavioral-vs-EEG overlap) pipeline.

Run: uv run pytest ssvepBeh/tests -q
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str, path: Path):
    """Load a module directly by file path, bypassing sys.modules entirely
    -- beh/, ssveps/, standardizedScores/FM100/, and this project each have
    their own loader.py/plotting.py under the same bare names, so a bare
    `import loader` here would be ambiguous (see beh/README.md's Tests
    section). Used only for beh's loader.py, the one cross-project import
    ssvepBeh/scripts/overlap.py itself doesn't need (see its docstring)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


beh_loader = _load("beh_loader_for_ssvepbeh_tests", ROOT / "beh" / "scripts" / "loader.py")
template = _load("template_grid_mapping", ROOT / "ssvepBeh" / "templateCode" / "grid_mapping.py")

# overlap.py/plotting.py are this project's own modules -- import normally,
# dropping any stale loader/plotting cache first (overlap.py inserts
# ssveps/scripts onto sys.path itself and imports "analysis", a unique name,
# so it doesn't need the same defense).
sys.path.insert(0, str(SCRIPTS))
for _name in ("loader", "plotting"):
    sys.modules.pop(_name, None)
import overlap  # noqa: E402

# overlap's own import above inserted ssveps/scripts at sys.path[0] as a
# side effect (see its docstring) -- ssveps/scripts has its own plotting.py
# too, so re-assert this project's scripts/ first before resolving
# "plotting", or it would silently import ssveps' version instead.
sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))
sys.modules.pop("plotting", None)
import plotting  # noqa: E402

analysis = overlap.analysis  # ssveps/scripts/analysis.py, already imported by overlap


@pytest.fixture(scope="module")
def beh_df():
    return beh_loader.load_behavioral()


@pytest.fixture(scope="module")
def runmap_df():
    return analysis.load_runmap()


@pytest.fixture(scope="module")
def baselines_df():
    return analysis.load_baselines()


@pytest.fixture(scope="module")
def metadata_df():
    return analysis.load_metadata()


# --- orientation (the bug this project found and fixed) --------------------


def test_behavioral_density_map_orientation_matches_template_subs_not_outmat(beh_df):
    """The template's outMat = subs.T is [green_idx, red_idx] -- the same
    axis-swap bug ssveps/ already fixed once (docs/ssvep_summary.md finding
    2.1). Pin that this module's density map matches the template's
    untransposed subs (correct) and NOT outMat (swapped)."""
    sub_id = "MET001"
    clicks = beh_df.loc[beh_df["sub_id"] == sub_id, ["red", "green"]].to_numpy()
    idx, out_mat = template.closest_grid_indices(clicks)
    subs = np.zeros((10, 10), dtype=int)
    for red_idx, green_idx in idx:
        subs[red_idx, green_idx] += 1

    B = overlap.behavioral_density_map(beh_df, [sub_id])
    np.testing.assert_array_equal(B, subs)
    assert not np.array_equal(B, out_mat)  # outMat is the swapped orientation -- must NOT match


def test_behavioral_centroid_peaks_at_the_expected_grid_cell(beh_df):
    """A subject's mean click should land near the density map's peak cell
    -- an independent sanity check on orientation beyond the template
    comparison above."""
    sub_id = "MET001"
    clicks = beh_df.loc[beh_df["sub_id"] == sub_id, ["red", "green"]]
    expected_red_idx = int(np.argmin(np.abs(overlap.DEFAULT_RED - clicks["red"].mean())))
    expected_green_idx = int(np.argmin(np.abs(overlap.DEFAULT_GREEN - clicks["green"].mean())))

    B = overlap.behavioral_density_map(beh_df, [sub_id])
    peak_red_idx, peak_green_idx = np.unravel_index(np.argmax(B), B.shape)
    assert (peak_red_idx, peak_green_idx) == (expected_red_idx, expected_green_idx)


# --- behavioral_density_map --------------------------------------------------


def test_behavioral_density_map_sums_to_click_count(beh_df):
    sub_id = "MET001"
    n_clicks = len(beh_df[beh_df["sub_id"] == sub_id])
    B = overlap.behavioral_density_map(beh_df, [sub_id])
    assert B.shape == (10, 10)
    assert B.sum() == n_clicks


def test_behavioral_density_map_pools_multiple_subjects(beh_df):
    sub_ids = ["MET001", "MET002"]
    n_clicks = len(beh_df[beh_df["sub_id"].isin(sub_ids)])
    B = overlap.behavioral_density_map(beh_df, sub_ids)
    assert B.sum() == n_clicks


# --- weighted_overlap_test --------------------------------------------------


def test_weighted_overlap_test_obs_stat_matches_template_formula(beh_df, runmap_df, baselines_df):
    """obs_stat = sum(E * B/B.sum()) -- same formula as the template's
    permWeighted2Dshifts, applied to the same (correctly oriented) B/E."""
    sub_id, session = "MET001", 1
    B = overlap.behavioral_density_map(beh_df, [sub_id])
    E = analysis.mean_grid(runmap_df, baselines_df, sub_id, session, normalize=analysis.DEFAULT_NORMALIZE)

    result = overlap.weighted_overlap_test(B, E, n_perm=100, seed=0)
    expected_obs_stat = float(np.sum(E * (B / B.sum())))
    assert result["obs_stat"] == pytest.approx(expected_obs_stat)


def test_weighted_overlap_test_is_reproducible_under_a_seed(beh_df, runmap_df, baselines_df):
    sub_id, session = "MET001", 1
    B = overlap.behavioral_density_map(beh_df, [sub_id])
    E = analysis.mean_grid(runmap_df, baselines_df, sub_id, session, normalize=analysis.DEFAULT_NORMALIZE)
    r1 = overlap.weighted_overlap_test(B, E, n_perm=200, seed=42)
    r2 = overlap.weighted_overlap_test(B, E, n_perm=200, seed=42)
    np.testing.assert_array_equal(r1["null_stats"], r2["null_stats"])
    assert r1["p_value"] == r2["p_value"]


def test_weighted_overlap_test_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        overlap.weighted_overlap_test(np.ones((10, 10)), np.ones((5, 5)))


def test_weighted_overlap_test_rejects_empty_behavioral_map():
    with pytest.raises(ValueError):
        overlap.weighted_overlap_test(np.zeros((10, 10)), np.ones((10, 10)))


def test_weighted_overlap_test_detects_a_known_overlap():
    """B and E both concentrated in the same corner -- obs_stat should sit
    at the low tail of the null (p small), since a real toroidal shift would
    almost always move E's low corner away from B's peak."""
    B = np.zeros((10, 10))
    B[0, 0] = 100  # every click in one cell
    E = np.ones((10, 10)) * 10
    E[0, 0] = 0  # EEG response is minimal exactly where clicks concentrate
    result = overlap.weighted_overlap_test(B, E, n_perm=2000, seed=0)
    assert result["obs_stat"] == 0
    assert result["p_value"] < 0.05


# --- subject_overlap / group_overlap / centroid_distance --------------------


def test_subject_overlap_runs_end_to_end(beh_df, runmap_df, baselines_df):
    result = overlap.subject_overlap(beh_df, runmap_df, baselines_df, "MET001", 1, n_perm=200, seed=0)
    assert {"p_value", "obs_stat", "null_stats"}.issubset(result)
    assert 0 <= result["p_value"] <= 1


def test_group_overlap_pools_subjects_and_reports_n(beh_df, runmap_df, baselines_df, metadata_df):
    result = overlap.group_overlap(beh_df, runmap_df, baselines_df, metadata_df, 1, group="CTR", n_perm=200, seed=0)
    expected_n = len(analysis.subjects_in_group(metadata_df, 1, group="CTR"))
    assert result["n_subjects"] == expected_n
    assert expected_n > 1


def test_group_overlap_sub_ids_overrides_group_filter(beh_df, runmap_df, baselines_df, metadata_df):
    sub_ids = ["MET001", "MET002"]
    result = overlap.group_overlap(beh_df, runmap_df, baselines_df, metadata_df, 1, sub_ids=sub_ids, n_perm=100, seed=0)
    assert result["n_subjects"] == len(sub_ids)


def test_centroid_distance_returns_expected_keys(beh_df, runmap_df, baselines_df):
    result = overlap.centroid_distance(beh_df, runmap_df, baselines_df, "MET001", 1)
    assert set(result) == {"beh_red", "beh_green", "eeg_red", "eeg_green", "distance"}
    assert result["distance"] >= 0


# --- plotting -----------------------------------------------------------


def test_plot_overlap_returns_two_panels(beh_df, runmap_df, baselines_df):
    E = analysis.mean_grid(runmap_df, baselines_df, "MET001", 1, normalize=analysis.DEFAULT_NORMALIZE)
    fig = plotting.plot_overlap(beh_df, E, ["MET001"])
    titles = [ax.get_title() for ax in fig.axes if ax.get_title()]
    assert titles == ["EEG response", "Behavioral clicks (n=30)"]
