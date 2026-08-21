"""FM100 severity/type features and cross-session reliability -- M1,
PLANssvep_bh_fm100.md.

Severity: TES, VKS_MajRad, VKS_MinRad (overall error magnitude, all
non-negative and non-periodic). Type/axis: VKS_Angle (confusion ellipse
direction). Reuses standardizedScores/FM100/scripts/scores.py's
build_scores, not recomputed.

VKS_Angle is periodic (a fitted ellipse axis has no direction, same
fold-to-axial treatment as beh's orientation_deg) -- both its
cross-session pooling (subject_pooled_features) and its reliability check
(vks_angle_reliability) use pingouin's circ_axial (doubles the angle so a
180deg-periodic quantity behaves like a proper 360deg circular one) rather
than a naive linear mean/ICC, which would silently give wrong answers near
the 0/180 wrap point -- verified with a synthetic example (mean of
[179deg, 1deg]: linear mean gives 90deg, the actual answer is ~0deg).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pingouin as pg

_FM100_SCRIPTS = str(Path(__file__).resolve().parents[2] / "standardizedScores" / "FM100" / "scripts")
if _FM100_SCRIPTS in sys.path:
    sys.path.remove(_FM100_SCRIPTS)
sys.path.insert(0, _FM100_SCRIPTS)
# standardizedScores/FM100/, beh/, ssveps/, and ssvepBeh/ each have their own
# loader.py/plotting.py under the same bare names -- drop any stale cache
# before importing FM100's, then import it first (before anything below
# touches sys.path again), so the module object this file binds to is
# correct regardless of what else has run in this process (see
# beh/README.md's Tests section for the same issue elsewhere).
for _name in ("loader", "plotting", "scores"):
    sys.modules.pop(_name, None)
import loader as fm100_loader  # noqa: E402
import scores as fm100_scores  # noqa: E402

_SSVEPS_SCRIPTS = str(Path(__file__).resolve().parents[2] / "ssveps" / "scripts")
if _SSVEPS_SCRIPTS in sys.path:
    sys.path.remove(_SSVEPS_SCRIPTS)
sys.path.insert(0, _SSVEPS_SCRIPTS)
import reliability  # noqa: E402 -- imports from "analysis" internally (unique name), no further defense needed

SEVERITY_FEATURES = ["TES", "VKS_MajRad", "VKS_MinRad"]
TYPE_FEATURE = "VKS_Angle"


def _circ_mean_deg_axial(angles_deg: np.ndarray) -> float:
    """Circular mean of 180deg-periodic ('axial') angles in degrees,
    folded back into [0, 180)."""
    doubled = pg.circ_axial(np.deg2rad(angles_deg), 2)
    return float(np.degrees(pg.circ_mean(doubled)) / 2 % 180)


def subject_session_features(fm100_df: pd.DataFrame) -> pd.DataFrame:
    """FM100 severity/type features for every (subject, session) row:
    sub_id, session, group, subgroup, TES, VKS_Angle, VKS_MajRad,
    VKS_MinRad -- reuses standardizedScores/FM100/scripts/scores.py's
    build_scores directly."""
    scores = fm100_scores.build_scores(fm100_df)
    return scores[["sub_id", "session", "group", "subgroup", "TES", "VKS_Angle", "VKS_MajRad", "VKS_MinRad"]]


def subject_pooled_features(fm100_df: pd.DataFrame) -> pd.DataFrame:
    """One row per subject: TES/VKS_MajRad/VKS_MinRad averaged (linear
    mean) across that subject's available FM100 sessions; VKS_Angle
    averaged circularly (see module docstring). group/subgroup taken from
    the first row (constant per subject). Adds n_sessions."""
    per_session = subject_session_features(fm100_df)
    rows = []
    for sub_id, sub in per_session.groupby("sub_id"):
        rows.append(
            {
                "sub_id": sub_id,
                "group": sub["group"].iloc[0],
                "subgroup": sub["subgroup"].iloc[0],
                "TES": sub["TES"].mean(),
                "VKS_Angle": _circ_mean_deg_axial(sub["VKS_Angle"].to_numpy()),
                "VKS_MajRad": sub["VKS_MajRad"].mean(),
                "VKS_MinRad": sub["VKS_MinRad"].mean(),
                "n_sessions": len(sub),
            }
        )
    return pd.DataFrame(rows)


def paired_sessions(fm100_df: pd.DataFrame, *, sessions: tuple[int, int] = (1, 2)) -> pd.DataFrame:
    """FM100 severity/type features for subjects present at both of
    `sessions`, one row per subject with each feature suffixed
    `_session{n}` (e.g. TES_session1, TES_session2) -- the input
    reliability_table needs. Raises ValueError if fewer than 3 subjects
    qualify (feature_icc's own minimum)."""
    per_session = subject_session_features(fm100_df)
    s1 = per_session[per_session["session"] == sessions[0]].set_index("sub_id")
    s2 = per_session[per_session["session"] == sessions[1]].set_index("sub_id")
    sub_ids = sorted(set(s1.index) & set(s2.index))
    if len(sub_ids) < 3:
        raise ValueError(f"only {len(sub_ids)} subjects have FM100 data at both session {sessions[0]} and {sessions[1]} (need >= 3)")

    features = [TYPE_FEATURE] + SEVERITY_FEATURES
    table = pd.DataFrame({"sub_id": sub_ids})
    for feat in features:
        table[f"{feat}_session{sessions[0]}"] = s1.loc[sub_ids, feat].to_numpy()
        table[f"{feat}_session{sessions[1]}"] = s2.loc[sub_ids, feat].to_numpy()
    return table


def reliability_table(fm100_df: pd.DataFrame, *, sessions: tuple[int, int] = (1, 2)) -> pd.DataFrame:
    """Cross-session reliability for all four severity/type features:
    ICC(A,1) (reliability.feature_icc) for the three magnitude features
    (SEVERITY_FEATURES), circ_corrcc (after circ_axial folding) for
    VKS_Angle, since it's periodic and a linear ICC would be wrong for it.
    Returns one row per feature: feature, n, statistic ('icc' or 'circ_r'),
    value, p_value."""
    paired = paired_sessions(fm100_df, sessions=sessions)
    n = len(paired)

    rows = []
    for feat in SEVERITY_FEATURES:
        result = reliability.feature_icc(paired[f"{feat}_session{sessions[0]}"].to_numpy(), paired[f"{feat}_session{sessions[1]}"].to_numpy())
        rows.append({"feature": feat, "n": n, "statistic": "icc", "value": result["icc"], "p_value": result["pval"]})

    angle1 = pg.circ_axial(np.deg2rad(paired[f"{TYPE_FEATURE}_session{sessions[0]}"].to_numpy()), 2)
    angle2 = pg.circ_axial(np.deg2rad(paired[f"{TYPE_FEATURE}_session{sessions[1]}"].to_numpy()), 2)
    r, p_value = pg.circ_corrcc(angle1, angle2)
    rows.append({"feature": TYPE_FEATURE, "n": n, "statistic": "circ_r", "value": r, "p_value": p_value})

    return pd.DataFrame(rows)
