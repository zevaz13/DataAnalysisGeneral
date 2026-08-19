"""Regression tests for the SSVEP pipeline.

Run: uv run pytest ssveps/tests -q

Deliberately small. Each test pins an invariant that was either got wrong once
already, or would be silent if it broke.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import analysis  # noqa: E402
import plotting  # noqa: E402
import permutation  # noqa: E402
from loader import load_ssvep, to_rows  # noqa: E402

RAW_DIR = Path("/home/sebas/data/ssveps")


@pytest.fixture(scope="module")
def data():
    return analysis.load_runmap(), analysis.load_baselines(), analysis.load_metadata()


@pytest.fixture(scope="module")
def axes():
    return analysis.load_grid_axes()


# --- axis orientation ------------------------------------------------------
# The one that was wrong. ssveps/CTRdata.png is an independently produced
# reference for this exact group; its minimum sits at red 2133 / green 889.


def test_ctr_trough_matches_reference_image(data, axes):
    runmap, baselines, meta = data
    red_vals, green_vals = axes
    grid = analysis.group_grid(runmap, baselines, meta, 1, group="CTR", normalize=analysis.DEFAULT_NORMALIZE)
    loc = analysis.trough_location(grid, red_vals, green_vals)
    assert loc["red"] == pytest.approx(2133.3, abs=1)
    assert loc["green"] == pytest.approx(888.9, abs=1)


def test_grid_is_indexed_red_then_green(data, axes):
    """Axis 0 is red, axis 1 is green -- the naming every docstring assumes."""
    runmap, baselines, meta = data
    red_vals, green_vals = axes
    grid = analysis.group_grid(runmap, baselines, meta, 1, group="CTR", normalize=analysis.DEFAULT_NORMALIZE)
    red_idx, green_idx = np.unravel_index(np.argmin(grid), grid.shape)
    assert red_vals[red_idx] == pytest.approx(2133.3, abs=1)
    assert green_vals[green_idx] == pytest.approx(888.9, abs=1)
    # SSVEP amplitude falls off with red: averaging over green, the red=0 edge
    # must be the brightest. This is direction-sensitive, unlike a correlation.
    raw = analysis.group_grid(runmap, baselines, meta, 1, group="CTR")
    assert raw.mean(axis=1)[0] == raw.mean(axis=1).max()


def test_heatmap_puts_red_on_x(data):
    """_plot_heatmap transposes for display, so the image's x axis is red."""
    runmap, baselines, meta = data
    grid = analysis.group_grid(runmap, baselines, meta, 1, group="CTR", normalize=analysis.DEFAULT_NORMALIZE)
    ax = plotting.plot_mean_across_subjects(runmap, baselines, meta, 1, group="CTR",
                                            normalize=analysis.DEFAULT_NORMALIZE)
    displayed = ax.images[0].get_array()
    assert displayed.shape == grid.T.shape
    np.testing.assert_allclose(displayed, grid.T)
    assert ax.get_xlabel() == "red" and ax.get_ylabel() == "green"


def test_loader_reads_runmap_green_first():
    """runMap's own axes are (green, red, run) despite mapDIM saying otherwise."""
    d = load_ssvep(str(RAW_DIR / "MET000.mat"))
    _, runmap_rows, _ = to_rows(d, "MET000.mat")
    row = next(r for r in runmap_rows if r["red_idx"] == 6 and r["green_idx"] == 4 and r["run"] == 1)
    assert row["value"] == d["runMap"][4, 6, 0]


# --- normalization ---------------------------------------------------------
# Must stay identical to templateCode/ICCs/computeICC_gridMaps.m lines 27-32.


def test_percent_normalization_matches_matlab_template(data):
    runmap, baselines, _ = data
    raw = analysis.raw_grid(runmap, "MET000", 1, 1)
    base = analysis.baseline_values(baselines, "MET000", 1, scope="run", run=1, trials="all")
    got = analysis.normalized_grid(runmap, baselines, "MET000", 1, 1, scope="run", trials="all", method="percent")
    np.testing.assert_allclose(got, (raw - base.mean()) / base.mean())


def test_mean_grid_normalizes_per_run_then_averages(data):
    """Order matters: normalize each run, then average -- not the reverse."""
    runmap, baselines, _ = data
    per_run = [
        analysis.normalized_grid(runmap, baselines, "MET000", 1, run, **analysis.DEFAULT_NORMALIZE)
        for run in (1, 2, 3, 4)
    ]
    got = analysis.mean_grid(runmap, baselines, "MET000", 1, normalize=analysis.DEFAULT_NORMALIZE)
    np.testing.assert_allclose(got, np.mean(per_run, axis=0))


# --- ragged 3-run subjects -------------------------------------------------


def test_ragged_three_run_subject(data):
    runmap, baselines, _ = data
    assert sorted(runmap.query("sub_id == 'MET037' and session == 1")["run"].unique()) == [1, 2, 3]
    assert analysis.flatten_runs(runmap, baselines, "MET037", 1).shape == (300,)
    assert analysis.flatten_runs(runmap, baselines, "MET000", 1).shape == (400,)
    assert analysis.mean_grid(runmap, baselines, "MET037", 1).shape == (10, 10)


# --- permutation testing ---------------------------------------------------


def test_clusters_use_8_connectivity():
    """MATLAB bwconncomp's 2D default is 8-connected; scipy's is 4."""
    zmap = np.zeros((10, 10))
    zmap[2, 2] = zmap[3, 3] = 5.0  # diagonal neighbours: one cluster, not two
    assert len(permutation._clusters(zmap, 1.96)) == 1


def test_permutation_keeps_every_subject(data):
    """n1/n2 default to the full group sizes -- no subject is discarded."""
    runmap, baselines, meta = data
    result = permutation.permutation_test_size(runmap, baselines, meta, 1, group1="PD", group2="CTR",
                                               n_perm=50, seed=0)
    assert result["n1"] == len(analysis.subjects_in_group(meta, 1, group="PD"))
    assert result["n2"] == len(analysis.subjects_in_group(meta, 1, group="CTR"))


def test_permutation_is_reproducible_under_a_seed(data):
    runmap, baselines, meta = data
    kw = dict(group1="PD", group2="CTR", n_perm=50, seed=7)
    a = permutation.permutation_test_size(runmap, baselines, meta, 1, **kw)
    b = permutation.permutation_test_size(runmap, baselines, meta, 1, **kw)
    np.testing.assert_array_equal(a["zdiff"], b["zdiff"])


# --- figure layout ---------------------------------------------------------


@pytest.mark.parametrize("n,expected_rows,expected_cols", [(3, 1, 3), (5, 1, 5), (6, 2, 5), (21, 5, 5)])
def test_panels_wrap_at_max_panel_cols(n, expected_rows, expected_cols):
    fig, axs = plotting._multi_panel_figure(n)
    rows, cols = axs[0].get_subplotspec().get_gridspec().get_geometry()
    assert (rows, cols) == (expected_rows, expected_cols)
    assert len(axs) == n
