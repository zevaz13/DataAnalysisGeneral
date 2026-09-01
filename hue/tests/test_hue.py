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
for _name in ("loader", "plotting", "aggregate"):
    sys.modules.pop(_name, None)

import aggregate  # noqa: E402
import loader  # noqa: E402
import pandas as pd  # noqa: E402
import plotting  # noqa: E402

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


def _synthetic_block(stim: int, n: int, start: float) -> pd.DataFrame:
    """One Stim block, HueR ramping start..start+n-1, for isolated trim-math tests."""
    return pd.DataFrame(
        {
            "Stim": stim,
            "sample_idx": range(n),
            "HueR": [start + i for i in range(n)],
            "is_baseline": False,
            "grid_index": stim,
            "baseline_id": pd.NA,
            "Red": 100,
            "Green": 200,
            "Yellow": 0,
        }
    )


def test_aggregate_trials_trims_both_edges_before_averaging():
    df = pd.concat([_synthetic_block(1, 10, start=0), _synthetic_block(2, 10, start=100)], ignore_index=True)
    agg = aggregate.aggregate_trials(df, group_cols=["Stim"], channels=["HueR"], trim=2)
    # block 1: values 0..9, trim 2 off each end -> 2..7, mean 4.5
    assert agg.set_index("Stim").loc[1, "HueR"] == pytest.approx(4.5)
    # block 2: values 100..109, trim 2 off each end -> 102..107, mean 104.5
    assert agg.set_index("Stim").loc[2, "HueR"] == pytest.approx(104.5)


def test_aggregate_trials_one_row_per_block_grid_and_baseline(filters_df):
    agg = aggregate.aggregate_trials(filters_df, group_cols=["flicker", "filter", "Stim"])
    assert len(agg) == filters_df.groupby(["flicker", "filter", "Stim"]).ngroups
    assert set(agg["is_baseline"].unique()) == {True, False}
    assert (agg.loc[~agg["is_baseline"], "grid_index"] >= 1).all()


def test_aggregate_trials_keeps_constant_columns(flashdiff_df):
    agg = aggregate.aggregate_trials(flashdiff_df, group_cols=["condition", "Stim"])
    for col in ("is_baseline", "grid_index", "baseline_id", "Red", "Green", "Yellow"):
        assert col in agg.columns


def test_additivity_prediction_matches_hand_computed_formula():
    agg = pd.DataFrame(
        {
            "condition": ["R", "R", "G", "G", "Y", "Y", "NN", "NN", "RGY", "RGY"],
            "grid_index": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
            "is_baseline": False,
            "HueR": [10, 20, 1, 2, 3, 4, 5, 6, 21, 32],
        }
    )
    out = aggregate.additivity_prediction(agg, components=["R", "G", "Y"], target="RGY", offset_multiplier=2, channels=["HueR"])
    row1 = out.set_index("grid_index").loc[1]
    # predicted = R + G + Y - 2*NN = 10 + 1 + 3 - 2*5 = 4
    assert row1["HueR_predicted"] == pytest.approx(4)
    assert row1["HueR_actual"] == pytest.approx(21)


def test_plot_channel_trials_one_panel_per_group(filters_df):
    agg = aggregate.aggregate_trials(filters_df, group_cols=["flicker", "filter", "Stim"])
    agg["condition"] = agg["flicker"] + "_" + agg["filter"]
    fig = plotting.plot_channel_trials(agg, group_col="condition")
    assert len(fig.axes) == agg["condition"].nunique()


def test_plot_channel_trials_show_baseline_adds_markers(filters_df):
    agg = aggregate.aggregate_trials(filters_df, group_cols=["flicker", "filter", "Stim"])
    agg["condition"] = agg["flicker"] + "_" + agg["filter"]
    fig = plotting.plot_channel_trials(agg, group_col="condition", groups=["solid_NF"], show_baseline=True)
    ax = fig.axes[0]
    assert len(ax.collections) == len(plotting.CORE_CHANNELS)  # one scatter series per channel


def test_plot_prediction_trials_one_panel_per_channel_actual_and_predicted_lines():
    pred = pd.DataFrame(
        {
            "grid_index": [1, 2, 3],
            "HueR_actual": [10, 20, 30],
            "HueR_predicted": [9, 21, 29],
            "HueG_actual": [1, 2, 3],
            "HueG_predicted": [1, 2, 3],
        }
    )
    fig = plotting.plot_prediction_trials(pred, channels=["HueR", "HueG"])
    assert len(fig.axes) == 2
    for ax in fig.axes:
        assert len(ax.lines) == 2  # actual + predicted
        assert "black" in {line.get_color() for line in ax.lines}
