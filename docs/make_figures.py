"""Regenerates the figures embedded in docs/experiment_summary.md and
docs/findings.md, straight from the raw data via each project's own
loader/plotting functions (no numbers re-derived here).

Run: uv run python docs/make_figures.py

Each block below is a direct port of an existing, working notebook cell
(cited per block) -- only the relative sys.path inserts became absolute
paths, and the standard cross-project loader/plotting name-collision reset
(see beh/README.md's Tests section) is applied before every block that
imports those two bare names from a different project than the block
before it.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIGURES = Path(__file__).resolve().parent / "figures"
FIGURES.mkdir(exist_ok=True)

BEH_SCRIPTS = str(ROOT / "beh/scripts")
SSVEPS_SCRIPTS = str(ROOT / "ssveps/scripts")
FM100_SCRIPTS = str(ROOT / "standardizedScores/FM100/scripts")
SSVEPBEH_SCRIPTS = str(ROOT / "ssvepBeh/scripts")
FM100BEH_SCRIPTS = str(ROOT / "ssvep_beh_fm100/scripts")


def use(scripts_dir: str, *names: str) -> None:
    """Force `names` (bare module names shared by more than one project's
    scripts/ dir) to re-resolve against scripts_dir on the next import."""
    for name in names:
        sys.modules.pop(name, None)
    while scripts_dir in sys.path:
        sys.path.remove(scripts_dir)
    sys.path.insert(0, scripts_dir)


def save(obj, name: str) -> None:
    fig = obj.figure if hasattr(obj, "figure") else obj
    fig.savefig(FIGURES / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {name}")


# ---------------------------------------------------------------------------
# 1. Shared stimulus, HC group: EEG response grid vs. behavioral click
#    density -- docs/experiment_summary.md.
#    Port of ssvepBeh/notebooks/01_explore.ipynb's group-overlap loop, HC.
# ---------------------------------------------------------------------------
use(BEH_SCRIPTS, "loader")
import loader as beh_loader

use(SSVEPBEH_SCRIPTS, "overlap")
import overlap

use(SSVEPBEH_SCRIPTS, "plotting")
import plotting as ssvepbeh_plotting

analysis = overlap.analysis  # ssveps/scripts/analysis.py, resolved by overlap.py
beh_df = beh_loader.load_behavioral()
runmap_df = analysis.load_runmap()
baselines_df = analysis.load_baselines()
metadata_df = analysis.load_metadata()
session = 1

hc_sub_ids = analysis.subjects_in_group(metadata_df, session, group="CTR")
E_hc = analysis.mean_grid_across_subjects(runmap_df, baselines_df, hc_sub_ids, session, normalize=analysis.DEFAULT_NORMALIZE)
fig = ssvepbeh_plotting.plot_overlap(beh_df, E_hc, hc_sub_ids, title=f"HC group: EEG response vs. behavioral clicks (n={len(hc_sub_ids)})")
save(fig, "shared_stimulus_hc_overlap.png")

# ---------------------------------------------------------------------------
# 2. FM100 radial error profile, one subject -- docs/experiment_summary.md.
#    Port of standardizedScores/FM100/notebooks/01_explore.ipynb.
# ---------------------------------------------------------------------------
use(FM100_SCRIPTS, "loader", "plotting")
import loader as fm100_loader
import plotting as fm100_plotting

fm100_df = fm100_loader.load_fm100_raw()
ax = fm100_plotting.plot_subject_fm100(fm100_df, "MET020", kind="radial", window=10)
save(ax, "shared_stimulus_fm100_radial.png")

# ---------------------------------------------------------------------------
# 3. FM100 group profiles, incl. MET047/MET021 -- docs/findings.md section 1.
#    Same notebook, group-plot cell. Reuses fm100_df/fm100_plotting above.
# ---------------------------------------------------------------------------
fm100_categories = [
    {"label": "HC", "group": "CTR"},
    {"label": "protan", "subgroup": "protan"},
    {"label": "deutan", "subgroup": "deutan"},
    {"label": "flagged (MET047, MET021)", "sub_ids": ["MET047", "MET021"]},
]
ax = fm100_plotting.plot_group_fm100(fm100_df, fm100_categories, kind="radial", window=10)
save(ax, "findings_fm100_groups_radial.png")

# ---------------------------------------------------------------------------
# 4. Behavioral shape feature space, protan vs. deutan -- findings section 2.
#    Port of beh/notebooks/02_shape_features.ipynb.
# ---------------------------------------------------------------------------
use(BEH_SCRIPTS, "loader", "plotting")
import loader as beh_loader2
import plotting as beh_plotting

beh_df2 = beh_loader2.load_behavioral()
pd_categories = [
    {"label": "protan", "subgroup": "protan"},
    {"label": "deutan", "subgroup": "deutan"},
]
ax = beh_plotting.plot_feature_space(beh_df2, pd_categories, x_feature="orientation_deg", y_feature="perp_var")
save(ax, "findings_beh_orientation_separation.png")

# ---------------------------------------------------------------------------
# 5. SSVEP response grid, HC/protan/deutan side by side -- findings section 3.
#    Port of ssveps/notebooks/03_group_comparisons.ipynb.
# ---------------------------------------------------------------------------
use(SSVEPS_SCRIPTS, "loader", "plotting", "analysis")
from analysis import load_baselines, load_metadata, load_runmap
from plotting import plot_groups_side_by_side

runmap_df2 = load_runmap()
baselines_df2 = load_baselines()
metadata_df2 = load_metadata()
gamut_categories = [
    {"label": "HC", "group": "CTR"},
    {"label": "protan", "subgroup": "protan"},
    {"label": "deutan", "subgroup": "deutan"},
]
fig = plot_groups_side_by_side(runmap_df2, baselines_df2, metadata_df2, session, gamut_categories, normalize=analysis.DEFAULT_NORMALIZE)
save(fig, "findings_ssveps_gamut_groups.png")

# ---------------------------------------------------------------------------
# 6. Behavioral-vs-EEG spatial overlap, CVD group -- findings section 4.
#    Same overlap/analysis objects as block 1; only "plotting" needs
#    re-resolving to ssvepBeh's version (block 5 pointed it at ssveps').
# ---------------------------------------------------------------------------
use(SSVEPBEH_SCRIPTS, "plotting")
import plotting as ssvepbeh_plotting2

cvd_sub_ids = analysis.subjects_in_group(metadata_df, session, group="CVD")
E_cvd = analysis.mean_grid_across_subjects(runmap_df, baselines_df, cvd_sub_ids, session, normalize=analysis.DEFAULT_NORMALIZE)
fig = ssvepbeh_plotting2.plot_overlap(beh_df, E_cvd, cvd_sub_ids, title=f"CVD group: EEG response vs. behavioral clicks (n={len(cvd_sub_ids)})")
save(fig, "findings_beh_eeg_overlap_cvd.png")

# ---------------------------------------------------------------------------
# 7. Three-way type/axis concordance (FM100, behavioral, EEG) -- section 5.
#    Port of ssvep_beh_fm100/notebooks/05_three_way_type_axis.ipynb.
# ---------------------------------------------------------------------------
use(FM100BEH_SCRIPTS, "loader", "plotting", "features", "fm100_features", "eeg_features", "type_axis")
import eeg_features
import fm100_features

use(FM100BEH_SCRIPTS, "plotting")
import plotting as fm100beh_plotting
import type_axis

use(BEH_SCRIPTS, "loader", "features")
import features as beh_features3
import loader as beh_loader3

fm100_df3 = fm100_features.fm100_loader.load_fm100_raw()
beh_df3 = beh_loader3.load_behavioral()
troughs = eeg_features.load_subject_troughs()

fm100_pooled = fm100_features.subject_pooled_features(fm100_df3)
beh_rows = [{"sub_id": s, **beh_features3.subject_shape_features(beh_df3, s)} for s in beh_df3["sub_id"].unique()]
beh_table = pd.DataFrame(beh_rows)
eeg_session1 = eeg_features.subject_session_features(troughs)
eeg_session1 = eeg_session1[eeg_session1["session"] == 1]

merged = fm100_pooled.merge(beh_table, on="sub_id").merge(eeg_session1, on="sub_id", suffixes=("_fm100", "_eeg"))

angle_arrays = [merged["VKS_Angle"].to_numpy(), merged["orientation_deg"].to_numpy(), merged["ramp_angle_deg"].to_numpy()]
labels = ["FM100", "Behavioral", "EEG"]
joint_result = type_axis.joint_concordance_test(angle_arrays, n_perm=5000, seed=0)

fig, ax = plt.subplots(figsize=(5, 4))
fm100beh_plotting.plot_pairwise_bars(joint_result, labels, ax=ax)
save(fig, "findings_three_way_concordance.png")

print("done")
