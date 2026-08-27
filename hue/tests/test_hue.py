"""Regression tests for the hue-sensor loader.

Run: uv run pytest hue/tests -q
"""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

# beh/scripts/, ssveps/scripts/, etc. each have their own loader.py/plotting.py
# under the same bare names -- if a combined pytest session collected one of
# those test modules first, sys.modules would hold their versions. Drop them
# so the imports below re-resolve against SCRIPTS (see beh/README.md's Tests
# section for the same issue there).
for _name in ("loader", "plotting"):
    sys.modules.pop(_name, None)

import loader  # noqa: E402

EXPECTED_COLUMNS = {"Stim", "HueR", "HueG", "HueB", "HueC", "HueCT", "HueLux", "Yellow", "Red", "Green", "Trig", "sample_idx", "is_baseline", "grid_index", "baseline_id"}
GRID_RED_VALUES = {0, 355, 711, 1066, 1422, 1777, 2133, 2488, 2844, 3200}
GRID_GREEN_VALUES = {0, 222, 444, 666, 888, 1111, 1333, 1555, 1777, 2000}


@pytest.fixture(scope="module")
def filters_df():
    return loader.load_filters()


@pytest.fixture(scope="module")
def flashdiff_df():
    return loader.load_flashdiff()


def test_load_filters_has_expected_columns(filters_df):
    assert EXPECTED_COLUMNS <= set(filters_df.columns)
    assert set(filters_df["flicker"].unique()) == {"solid", "flash"}
    assert set(filters_df["filter"].unique()) == {"F", "NF", "Or"}


def test_load_filters_covers_all_six_files(filters_df):
    assert filters_df.groupby(["flicker", "filter"]).ngroups == 6


def test_load_flashdiff_has_expected_columns(flashdiff_df):
    assert EXPECTED_COLUMNS <= set(flashdiff_df.columns)
    assert set(flashdiff_df["condition"].unique()) == {"NN", "R", "G", "Y", "RG", "RY", "GY", "RGY", "RGY_1"}


def test_yellow_is_the_fixed_reference_value(filters_df, flashdiff_df):
    """docs/experiment_summary.md: the fixed yellow LED reference is 2400
    D/A units, the same beh/'s manual-match task and ssveps/'s stimulus
    use."""
    assert (filters_df["Yellow"].isin([0, 2400])).all()
    assert (flashdiff_df["Yellow"].isin([0, 2400])).all()


def test_grid_red_green_values_match_ssveps_grid(filters_df, flashdiff_df):
    """Red/Green on grid rows are the same 10x10 grid ssveps/files/grid.json
    defines (redArray/greenArray, int-truncated)."""
    for df in (filters_df, flashdiff_df):
        grid = df[~df["is_baseline"]]
        assert set(grid["Red"].unique()) == GRID_RED_VALUES
        assert set(grid["Green"].unique()) == GRID_GREEN_VALUES


def test_grid_index_spans_1_to_100_for_every_condition(flashdiff_df):
    for condition, sub in flashdiff_df.groupby("condition"):
        grid_index = sub.loc[~sub["is_baseline"], "grid_index"]
        assert set(grid_index.unique()) == set(range(1, 101)), condition


def test_grid_index_maps_to_one_consistent_red_green_pair(filters_df, flashdiff_df):
    """Every grid_index must correspond to exactly one (Red, Green) pair,
    consistently across every condition and both filters/ and flashDiff/ --
    otherwise a grid heatmap built from grid_index wouldn't be meaningful."""
    for df in (filters_df, flashdiff_df):
        grid = df[~df["is_baseline"]]
        nunique = grid.groupby("grid_index")[["Red", "Green"]].nunique()
        assert (nunique == 1).all().all()

    filters_map = filters_df[~filters_df["is_baseline"]].groupby("grid_index")[["Red", "Green"]].first()
    flashdiff_map = flashdiff_df[~flashdiff_df["is_baseline"]].groupby("grid_index")[["Red", "Green"]].first()
    assert filters_map.equals(flashdiff_map)


def test_rgy_1_baseline_and_grid_normalized_from_its_own_raw_scheme(flashdiff_df):
    """RGY_1's raw Stim range is 999-1099 (not 1-100 plus 1000-1005 like
    every other condition) -- confirms the loader's remapping (999 ->
    baseline, 1000-1099 -> grid_index 1-100) actually ran, not just that
    the columns exist."""
    rgy1 = flashdiff_df[flashdiff_df["condition"] == "RGY_1"]
    assert set(rgy1.loc[rgy1["is_baseline"], "baseline_id"].unique()) == {0}
    assert set(rgy1.loc[~rgy1["is_baseline"], "grid_index"].unique()) == set(range(1, 101))


def test_most_conditions_have_six_baseline_blocks_rgy_1_has_one(flashdiff_df):
    for condition, sub in flashdiff_df.groupby("condition"):
        baseline_ids = set(sub.loc[sub["is_baseline"], "baseline_id"].unique())
        expected = {0} if condition == "RGY_1" else {0, 1, 2, 3, 4, 5}
        assert baseline_ids == expected, condition


def test_sample_idx_restarts_at_zero_per_stim_block(filters_df):
    one_block = filters_df[(filters_df["flicker"] == "solid") & (filters_df["filter"] == "NF") & (filters_df["Stim"] == 1)]
    assert one_block["sample_idx"].tolist() == list(range(len(one_block)))
