"""Regression tests for the behavioral (manual point-matching) pipeline.

Run: uv run pytest beh/tests -q
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

# ssveps/scripts/ has its own loader.py/plotting.py -- if a combined run (e.g.
# bare `pytest` at the repo root) collected that test module first, sys.modules
# would already hold ssveps' versions under these bare names. Drop them so the
# imports below re-resolve against SCRIPTS, just inserted at sys.path[0],
# regardless of what ran before this module in the same pytest session.
for _name in ("loader", "plotting"):
    sys.modules.pop(_name, None)

import comparisons  # noqa: E402
import loader  # noqa: E402
import plotting  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return loader.load_behavioral()


# --- loader ------------------------------------------------------------


def test_load_behavioral_has_expected_shape_and_columns(df):
    assert list(df.columns) == ["sub_id", "session", "click", "red", "green", "group", "subgroup", "date", "folder"]
    assert len(df) == 1590
    assert df["sub_id"].nunique() == 47


def test_part_type_maps_to_group_matching_ssveps_metadata(df):
    """Confirmed empirically against ssveps/files/metadata.csv for every
    overlapping subject before choosing this mapping -- pin it."""
    ssvep_meta = pd.read_csv(SCRIPTS / ".." / ".." / "ssveps" / "files" / "metadata.csv", keep_default_na=False)
    overlap = ssvep_meta.drop_duplicates("sub_id").set_index("sub_id")["group"]
    checked = 0
    for sub_id, group in df[["sub_id", "group"]].drop_duplicates().itertuples(index=False):
        if sub_id in overlap.index:
            assert group == overlap[sub_id]
            checked += 1
    assert checked == 43  # every ssveps-known subject in this dataset


def test_subgroup_is_populated_for_every_cvd_subject(df):
    cvd = df[df["group"] == "CVD"]
    assert (cvd["subgroup"].isin(["protan", "deutan"])).all()


def test_subgroup_is_na_for_subjects_missing_from_ssvep_metadata(df):
    """MET013/MET014 (HC) and MET041/MET042 (PD) aren't in ssveps'
    metadata.csv -- they must not silently disappear or error, just get 'NA'."""
    extra = df[df["sub_id"].isin(["MET013", "MET014", "MET041", "MET042"])]
    assert len(extra) > 0
    assert (extra["subgroup"] == "NA").all()


def test_subjects_in_group_filters_correctly(df):
    protan = loader.subjects_in_group(df, subgroup="protan")
    assert set(protan) == set(df.loc[df["subgroup"] == "protan", "sub_id"].unique())
    assert len(loader.subjects_in_group(df)) == 47


# --- comparisons (Hotelling T^2) ----------------------------------------


def test_group_points_subject_unit_is_one_row_per_subject(df):
    sub_ids = loader.subjects_in_group(df, group="PD")
    points = comparisons.group_points(df, group="PD", unit="subject")
    assert points.shape == (len(sub_ids), 2)


def test_group_points_point_unit_is_one_row_per_click(df):
    n_clicks = len(df[df["group"] == "PD"])
    points = comparisons.group_points(df, group="PD", unit="point")
    assert points.shape == (n_clicks, 2)


def test_group_points_subject_mean_matches_manual_groupby(df):
    points = comparisons.group_points(df, group="PD", unit="subject")
    expected = df[df["group"] == "PD"].groupby("sub_id")[["red", "green"]].mean().sort_index().to_numpy()
    np.testing.assert_allclose(np.sort(points, axis=0), np.sort(expected, axis=0))


def test_group_points_rejects_unknown_unit(df):
    with pytest.raises(ValueError):
        comparisons.group_points(df, group="PD", unit="nonsense")


def test_compare_groups_detects_a_known_separation():
    """Two clearly separated synthetic clusters, one point per row (unit
    doesn't matter at n=1 click per subject) -- should reject the null hard."""
    rng = np.random.default_rng(0)
    n = 20
    synth = pd.DataFrame(
        {
            "sub_id": [f"A{i}" for i in range(n)] + [f"B{i}" for i in range(n)],
            "session": 1,
            "click": 1,
            "red": np.concatenate([rng.normal(500, 50, n), rng.normal(2500, 50, n)]),
            "green": np.concatenate([rng.normal(500, 50, n), rng.normal(1500, 50, n)]),
            "group": ["A"] * n + ["B"] * n,
            "subgroup": "NA",
        }
    )
    result = comparisons.compare_groups(synth, group1="A", group2="B", unit="subject")
    assert result["p_value"] < 1e-6
    assert result["n1"] == n and result["n2"] == n


def test_compare_groups_point_unit_pseudoreplicates_toward_significance(df):
    """Same two groups, both units -- pooling every click as if independent
    should push the p-value down relative to the subject-mean version (more
    'observations', same underlying separation), not the other way round."""
    subject_result = comparisons.compare_groups(df, group1="CTR", group2="PD", unit="subject")
    point_result = comparisons.compare_groups(df, group1="CTR", group2="PD", unit="point")
    assert point_result["n1"] > subject_result["n1"]
    assert point_result["p_value"] <= subject_result["p_value"]


# --- plotting ------------------------------------------------------------


def test_plot_subject_session_sets_default_axis_limits(df):
    ax = plotting.plot_subject_session(df, "MET001", 1)
    assert ax.get_xlim() == plotting.XLIM
    assert ax.get_ylim() == plotting.YLIM
    assert ax.get_xlabel() == "red" and ax.get_ylabel() == "green"


def test_plot_subject_sessions_draws_one_series_per_session(df):
    ax = plotting.plot_subject_sessions(df, "MET001")
    n_sessions = df.loc[df["sub_id"] == "MET001", "session"].nunique()
    assert len(ax.collections) == n_sessions


def test_plot_subjects_grid_wraps_at_max_panel_cols(df):
    sub_ids = loader.subjects_in_group(df, subgroup="protan")  # 8 subjects
    fig = plotting.plot_subjects_grid(df, sub_ids=sub_ids)
    rows, cols = fig.axes[0].get_subplotspec().get_gridspec().get_geometry()
    assert (rows, cols) == (2, plotting.MAX_PANEL_COLS)  # ceil(8/5) rows x 5 cols
    visible = [ax for ax in fig.axes if ax.axison]
    assert len(visible) == len(sub_ids)


def test_plot_groups_side_by_side_one_panel_per_category(df):
    categories = [{"label": "HC", "group": "CTR"}, {"label": "PD", "group": "PD"}]
    fig = plotting.plot_groups_side_by_side(df, categories)
    assert len(fig.axes) == len(categories)
