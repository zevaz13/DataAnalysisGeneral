"""Regression tests for the ssvep_beh_fm100 pipeline (M1: FM100 reliability
and FM100-vs-behavioral).

Run: uv run pytest ssvep_beh_fm100/tests -q
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
    -- beh/, ssveps/, standardizedScores/FM100/, ssvepBeh/, and this project
    each have their own loader.py/plotting.py under the same bare names
    (see beh/README.md's Tests section)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


beh_loader = _load("beh_loader_for_ssvep_beh_fm100_tests", ROOT / "beh" / "scripts" / "loader.py")

# beh/scripts/features.py itself does `from loader import subjects_in_group`
# internally -- direct file-path loading (as above) doesn't put beh/scripts
# on sys.path, so that internal import needs it there explicitly first (same
# fix ssvepBeh/scripts/correlation.py already needed for the same reason).
_BEH_SCRIPTS = str(ROOT / "beh" / "scripts")
if _BEH_SCRIPTS in sys.path:
    sys.path.remove(_BEH_SCRIPTS)
sys.path.insert(0, _BEH_SCRIPTS)
sys.modules.pop("loader", None)
beh_features = _load("beh_features_for_ssvep_beh_fm100_tests", ROOT / "beh" / "scripts" / "features.py")

sys.path.insert(0, str(SCRIPTS))
for _name in ("loader", "plotting", "scores", "reliability"):
    sys.modules.pop(_name, None)
import fm100_features  # noqa: E402
import severity  # noqa: E402
import type_axis  # noqa: E402

# fm100_features's own import above inserted ssveps/scripts at sys.path[0]
# as a side effect (it needs ssveps' reliability.py) -- ssveps/scripts has
# its own plotting.py too, so re-assert this project's scripts/ first
# before resolving "plotting", or it would silently import ssveps' version
# instead (same gotcha ssvepBeh/ already documents for the same reason).
if str(SCRIPTS) in sys.path:
    sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))
sys.modules.pop("plotting", None)
import plotting  # noqa: E402


@pytest.fixture(scope="module")
def fm100_df():
    return fm100_features.fm100_loader.load_fm100_raw()


@pytest.fixture(scope="module")
def beh_df():
    return beh_loader.load_behavioral()


@pytest.fixture(scope="module")
def merged(fm100_df, beh_df):
    fm100_pooled = fm100_features.subject_pooled_features(fm100_df)
    rows = [{"sub_id": s, **beh_features.subject_shape_features(beh_df, s)} for s in beh_df["sub_id"].unique()]
    beh_table = pd.DataFrame(rows)
    return fm100_pooled.merge(beh_table, on="sub_id", suffixes=("_fm100", "_beh"))


# --- fm100_features ----------------------------------------------------


def test_subject_session_features_has_expected_columns(fm100_df):
    table = fm100_features.subject_session_features(fm100_df)
    assert list(table.columns) == ["sub_id", "session", "group", "subgroup", "TES", "VKS_Angle", "VKS_MajRad", "VKS_MinRad"]
    assert len(table) == 69


def test_subject_pooled_features_one_row_per_subject(fm100_df):
    table = fm100_features.subject_pooled_features(fm100_df)
    assert table["sub_id"].is_unique
    assert len(table) == fm100_df["sub_id"].nunique()
    assert (table["n_sessions"] >= 1).all()


def test_circ_mean_deg_axial_matches_manual_derivation():
    """Pins the derivation verified against pingouin directly before
    writing this module: mean of [179, 1] (2deg apart on the 180deg circle)
    should fold to ~0, not the naive linear mean of 90."""
    result = fm100_features._circ_mean_deg_axial(np.array([179.0, 1.0]))
    assert result == pytest.approx(0.0, abs=1e-6)


def test_circ_mean_deg_axial_stays_put_for_a_tight_cluster():
    result = fm100_features._circ_mean_deg_axial(np.array([88.0, 90.0, 92.0]))
    assert result == pytest.approx(90.0, abs=1e-6)


def test_paired_sessions_matches_known_count(fm100_df):
    paired = fm100_features.paired_sessions(fm100_df)
    assert len(paired) == 19
    assert {"TES_session1", "TES_session2", "VKS_Angle_session1", "VKS_Angle_session2"}.issubset(paired.columns)


def test_paired_sessions_raises_below_minimum(fm100_df):
    with pytest.raises(ValueError):
        fm100_features.paired_sessions(fm100_df, sessions=(1, 3))  # only 1 subject has session 3


def test_reliability_table_uses_icc_for_magnitude_features_and_circ_r_for_angle(fm100_df):
    result = fm100_features.reliability_table(fm100_df)
    assert set(result["feature"]) == {"TES", "VKS_MajRad", "VKS_MinRad", "VKS_Angle"}
    by_feature = result.set_index("feature")
    assert (by_feature.loc[["TES", "VKS_MajRad", "VKS_MinRad"], "statistic"] == "icc").all()
    assert by_feature.loc["VKS_Angle", "statistic"] == "circ_r"
    assert (by_feature["n"] == 19).all()


# --- severity (CCA) ------------------------------------------------------


def test_cca_test_detects_a_known_relationship():
    """X and Y share a common latent factor z -- the observed canonical
    correlation should sit far above the permutation null."""
    rng = np.random.default_rng(0)
    n = 40
    z = rng.normal(0, 1, n)
    X = np.column_stack([z + rng.normal(0, 0.2, n), rng.normal(0, 1, n)])
    Y = np.column_stack([z + rng.normal(0, 0.2, n), rng.normal(0, 1, n)])
    result = severity.cca_test(X, Y, n_perm=1000, seed=0)
    assert result["r"] > 0.8
    assert result["p_value"] < 0.01


def test_cca_test_independent_features_are_not_significant():
    rng = np.random.default_rng(1)
    n = 40
    X = rng.normal(0, 1, (n, 2))
    Y = rng.normal(0, 1, (n, 2))
    result = severity.cca_test(X, Y, n_perm=1000, seed=0)
    assert result["p_value"] > 0.05


def test_cca_test_r_is_never_negative():
    """Verified empirically before relying on it in the one-sided p-value
    formula -- sklearn's CCA always returns r >= 0."""
    rng = np.random.default_rng(2)
    for seed in range(5):
        rng_i = np.random.default_rng(seed)
        X = rng_i.normal(0, 1, (30, 3))
        Y = rng_i.normal(0, 1, (30, 2))
        result = severity.cca_test(X, Y, n_perm=50, seed=0)
        assert result["r"] >= 0


def test_cca_test_is_reproducible_under_a_seed():
    rng = np.random.default_rng(3)
    X = rng.normal(0, 1, (20, 2))
    Y = rng.normal(0, 1, (20, 2))
    r1 = severity.cca_test(X, Y, n_perm=200, seed=42)
    r2 = severity.cca_test(X, Y, n_perm=200, seed=42)
    np.testing.assert_array_equal(r1["null_r"], r2["null_r"])


def test_cca_test_rejects_mismatched_subject_counts():
    with pytest.raises(ValueError):
        severity.cca_test(np.ones((10, 2)), np.ones((8, 2)))


def test_cca_test_rejects_too_few_subjects():
    with pytest.raises(ValueError):
        severity.cca_test(np.ones((2, 2)), np.ones((2, 2)))


def test_severity_cca_on_real_data_is_significant_pooled(merged):
    """Pins the real M1 finding: pooled across all 47 subjects, the
    severity CCA between FM100 (TES, VKS_MajRad, VKS_MinRad) and behavioral
    (along_var, perp_var) is strong and significant."""
    X = merged[["TES", "VKS_MajRad", "VKS_MinRad"]].to_numpy()
    Y = merged[["along_var", "perp_var"]].to_numpy()
    result = severity.cca_test(X, Y, n_perm=2000, seed=0)
    assert result["r"] > 0.5
    assert result["p_value"] < 0.01


# --- type_axis (circular correlation) -------------------------------------


def test_circular_correlation_test_detects_a_known_relationship():
    rng = np.random.default_rng(0)
    n = 40
    base = rng.uniform(0, 180, n)
    noisy = (base + rng.normal(0, 5, n)) % 180
    result = type_axis.circular_correlation_test(base, noisy)
    assert result["r"] > 0.8
    assert result["p_value"] < 0.001


def test_circular_correlation_test_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        type_axis.circular_correlation_test(np.array([1.0, 2.0]), np.array([1.0]))


def test_circular_correlation_wraps_correctly_near_the_boundary():
    """179 and 1 are 2deg apart on the 180deg circle -- a set of points
    hugging that boundary should still show a strong circular correlation
    with a copy of itself, unlike a naive linear correlation would."""
    x = np.array([179.0, 178.0, 1.0, 2.0, 3.0])
    y = x.copy()
    result = type_axis.circular_correlation_test(x, y)
    assert result["r"] > 0.9


def test_type_axis_on_real_data_is_significant_pooled(merged):
    """Pins the real M1 finding: pooled, VKS_Angle vs. orientation_deg is
    significantly circularly correlated."""
    result = type_axis.circular_correlation_test(merged["VKS_Angle"].to_numpy(), merged["orientation_deg"].to_numpy())
    assert result["p_value"] < 0.05


# --- plotting -----------------------------------------------------------


def test_plot_canonical_variates_returns_axes():
    result = {"r": 0.5, "p_value": 0.01, "x_scores": np.array([1.0, 2.0, 3.0]), "y_scores": np.array([1.0, 2.0, 3.0])}
    ax = plotting.plot_canonical_variates(result)
    assert len(ax.collections) == 1


def test_plot_null_distribution_draws_the_observed_line():
    result = {"r": 0.5, "null_r": np.random.default_rng(0).uniform(0, 1, 100)}
    ax = plotting.plot_null_distribution(result)
    assert len(ax.lines) == 1


def test_plot_circular_scatter_returns_axes():
    ax = plotting.plot_circular_scatter(np.array([10.0, 20.0]), np.array([15.0, 25.0]))
    assert ax.get_xlim() == (0.0, 180.0)


def test_plot_reliability_table_handles_negative_values():
    df = pd.DataFrame({"feature": ["A", "B"], "value": [-0.3, 0.8], "p_value": [0.5, 0.01]})
    ax = plotting.plot_reliability_table(df)
    assert ax.get_ylim() == (-1.0, 1.1)
