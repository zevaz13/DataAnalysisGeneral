"""Regression tests for the FM100 pipeline.

Run: uv run pytest standardizedScores/FM100/tests -q
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

# beh/scripts/ and ssveps/scripts/ each have their own loader.py/plotting.py
# under the same bare names -- if a combined pytest session collected one of
# those test modules first, sys.modules would hold their versions. Drop them
# so the imports below re-resolve against SCRIPTS (see beh/README.md's Tests
# section for the same issue there).
for _name in ("loader", "plotting", "scores"):
    sys.modules.pop(_name, None)

import loader  # noqa: E402
import plotting  # noqa: E402
import scores  # noqa: E402

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templateCode" / "FM100.py"


def _load_template():
    spec = importlib.util.spec_from_file_location("template_fm100", TEMPLATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def df():
    return loader.load_fm100_raw()


@pytest.fixture(scope="module")
def template():
    return _load_template()


# --- loader ----------------------------------------------------------------


def test_load_fm100_raw_has_expected_shape_and_columns(df):
    assert list(df.columns) == ["sub_id", "session", "group", "subgroup", "sex", "date", "caps"]
    assert len(df) == 69  # 70 raw rows minus the byte-identical duplicate MET000 row


def test_duplicate_first_row_is_dropped(df):
    """The raw file's first line is a byte-identical duplicate of the
    second (MET000) row -- pin that only one MET000/session-1 row survives."""
    assert len(df[(df["sub_id"] == "MET000") & (df["session"] == 1)]) == 1


def test_session_suffix_parsing(df):
    met000_sessions = sorted(df.loc[df["sub_id"] == "MET000", "session"])
    assert met000_sessions == [1, 2, 3]  # MET000, MET000b, MET000c


def test_caps_are_a_permutation_of_1_to_85(df):
    for caps in df["caps"]:
        assert caps.shape == (85,)
        np.testing.assert_array_equal(np.sort(caps), np.arange(1, 86))


def test_group_matches_ssveps_metadata_for_every_overlapping_subject(df):
    ssvep_meta = pd.read_csv(SCRIPTS / ".." / ".." / ".." / "ssveps" / "files" / "metadata.csv", keep_default_na=False)
    overlap = ssvep_meta.drop_duplicates("sub_id").set_index("sub_id")["group"]
    checked = 0
    for sub_id, group in df[["sub_id", "group"]].drop_duplicates().itertuples(index=False):
        if sub_id in overlap.index:
            assert group == overlap[sub_id]
            checked += 1
    assert checked > 0


def test_met047_is_unknown_and_met021_keeps_its_ssvep_label(df):
    """MET047 has no SSVEP/behavioral data at all (new, unallocated).
    MET021 is labeled CTR in ssveps/files/metadata.csv -- trusted as-is
    here, per project decision, despite being flagged as a possibly
    different (non-red-green) deficiency type."""
    met047 = df[df["sub_id"] == "MET047"]
    assert len(met047) == 1
    assert (met047["group"] == "UNKNOWN").all() and (met047["subgroup"] == "NA").all()

    met021 = df[df["sub_id"] == "MET021"]
    assert len(met021) > 0
    assert (met021["group"] == "CTR").all()


def test_subjects_in_group_filters_correctly(df):
    protan = loader.subjects_in_group(df, subgroup="protan")
    assert set(protan) == set(df.loc[df["subgroup"] == "protan", "sub_id"].unique())
    assert len(loader.subjects_in_group(df)) == df["sub_id"].nunique()


# --- scores: pinned against templateCode/FM100.py on every real row --------


def test_err_vals_matches_template_on_every_subject(df, template):
    for caps in df["caps"]:
        _, _, expected = template.FM100_TESwhole(caps)
        np.testing.assert_allclose(scores.err_vals(caps), expected)


def test_tes_matches_template_on_every_subject(df, template):
    for caps in df["caps"]:
        expected_tes, expected_sqrt, _ = template.FM100_TESwhole(caps)
        result = scores.tes(caps)
        assert result["TES"] == pytest.approx(expected_tes)
        assert result["SqrtTES"] == pytest.approx(expected_sqrt)


def test_pes_matches_template_on_every_subject(df, template):
    for caps in df["caps"]:
        expected = template.compute_PES(caps)
        result = scores.pes(caps)
        for key in ["PES_RG", "PES_BY", "PES_RG_sqrt", "PES_BY_sqrt"]:
            assert result[key] == pytest.approx(expected[key])


def test_tes_trays_matches_template_on_every_subject(df, template):
    for caps in df["caps"]:
        expected = template.compute_TES_trays(caps)
        result = scores.tes_trays(caps)
        np.testing.assert_allclose(result["TES_tray"], expected["TES_tray"])
        assert result["TES_whole"] == pytest.approx(expected["TES_whole"])


def test_vks_matches_template_on_every_subject(df, template):
    for caps in df["caps"]:
        expected = template.compute_VKS_metrics(caps, silent=True)
        result = scores.vks(caps)
        assert result["VKS_Angle"] == pytest.approx(expected["Angle"])
        assert result["VKS_MajRad"] == pytest.approx(expected["MajRad"])
        assert result["VKS_MinRad"] == pytest.approx(expected["MinRad"])
        assert result["VKS_Sindex"] == pytest.approx(expected["Sindex"])
        assert result["VKS_Cindex"] == pytest.approx(expected["Cindex"])


def test_err_vals_rejects_wrong_length():
    with pytest.raises(ValueError):
        scores.err_vals(np.arange(1, 84))


def test_vks_rejects_non_permutation():
    bad_caps = np.arange(1, 86)
    bad_caps[0] = 2  # cap 2 repeated, cap 1 missing
    with pytest.raises(ValueError):
        scores.vks(bad_caps)


def test_build_scores_one_row_per_subject_session(df):
    result = scores.build_scores(df)
    assert len(result) == len(df)
    assert {"sub_id", "session", "group", "subgroup", "TES", "PES_RG", "PES_BY", "VKS_Angle"}.issubset(result.columns)


# --- plotting ----------------------------------------------------------------


def test_plot_subject_fm100_linear_draws_one_line_per_session(df):
    ax = plotting.plot_subject_fm100(df, "MET001", kind="linear")
    n_sessions = df.loc[df["sub_id"] == "MET001", "session"].nunique()
    assert len(ax.lines) == n_sessions
    assert ax.get_xlim() == (1.0, 85.0)


def test_plot_subject_fm100_radial_uses_a_polar_axes(df):
    ax = plotting.plot_subject_fm100(df, "MET001", kind="radial")
    assert ax.name == "polar"


def test_plot_subject_fm100_radial_closes_the_circle(df):
    """CAP_ANGLES uses endpoint=False -- without closing, cap 85 and cap 1
    wouldn't connect, leaving a visible gap at the seam."""
    ax = plotting.plot_subject_fm100(df, "MET001", kind="radial", sessions=[1])
    theta, r = ax.lines[0].get_xydata().T
    assert theta[-1] == pytest.approx(theta[0] + 2 * np.pi)
    assert r[-1] == pytest.approx(r[0])


def test_plot_group_fm100_radial_closes_the_circle(df):
    categories = [{"label": "HC", "group": "CTR"}]
    ax = plotting.plot_group_fm100(df, categories, kind="radial")
    theta, r = ax.lines[0].get_xydata().T
    assert theta[-1] == pytest.approx(theta[0] + 2 * np.pi)
    assert r[-1] == pytest.approx(r[0])


def test_plot_subject_fm100_rejects_unknown_kind(df):
    with pytest.raises(ValueError):
        plotting.plot_subject_fm100(df, "MET001", kind="nonsense")


def test_plot_group_fm100_draws_one_line_and_band_per_category(df):
    categories = [{"label": "HC", "group": "CTR"}, {"label": "PD", "group": "PD"}]
    ax = plotting.plot_group_fm100(df, categories)
    assert len(ax.lines) == len(categories)
    assert len(ax.collections) == len(categories)  # fill_between bands


def test_plot_group_fm100_rejects_more_categories_than_full_palette(df):
    categories = [{"label": str(i), "group": "CTR"} for i in range(len(plotting.FULL_PALETTE) + 1)]
    with pytest.raises(ValueError):
        plotting.plot_group_fm100(df, categories)


def test_plot_group_fm100_averages_multi_session_subjects_before_group_stats(df):
    """A subject with 2 sessions must count once toward the group mean/SD,
    not twice -- pin against a hand-picked pair (one 1-session, one
    2-session subject)."""
    session_counts = df.groupby("sub_id")["session"].nunique()
    pair = [session_counts[session_counts == 1].index[0], session_counts[session_counts == 2].index[0]]
    profiles = plotting._group_profiles(df, group=None, subgroup=None, sub_ids=pair, window=1)
    assert profiles.shape == (2, 85)


def test_smooth_circular_is_a_noop_for_window_1():
    values = np.arange(85, dtype=float)
    np.testing.assert_array_equal(plotting._smooth_circular(values, 1), values)


def test_smooth_circular_preserves_length():
    values = np.arange(85, dtype=float)
    for window in [2, 3, 5, 8]:
        assert plotting._smooth_circular(values, window).shape == (85,)
