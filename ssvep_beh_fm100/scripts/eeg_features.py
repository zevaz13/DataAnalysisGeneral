"""EEG severity/type features and cross-session reliability -- M2,
PLANssvep_bh_fm100.md.

Severity: ramp_magnitude (sqrt(ramp_slope_red^2 + ramp_slope_green^2),
overall steepness, direction-independent), ramp_intercept (baseline gain).
Type/axis: ramp_angle_deg, the direction of (ramp_slope_red,
ramp_slope_green), stored as the full arctan2 angle in [0, 360).

**Design note, worth being explicit about.** Unlike VKS_Angle/orientation_deg
(a PCA/ellipse-fit axis, whose sign is arbitrary by construction -- an
eigenvector points equally validly either way), the raw gradient direction
here is genuinely meaningful: a response that falls off toward higher red
is physically different from one that rises toward higher red. This module
stores the full directional angle; the axial (180deg-periodic) fold is
applied only downstream, at this module's own reliability check and at
type_axis.circular_correlation_test's cross-modality use -- the same
storage-vs-usage split fm100_features.py uses for VKS_Angle. Folding is a
deliberate simplification specific to comparing against two features that
cannot carry a sign at all, turning the question into "does the axis of
steepest change agree" -- not a general claim that the sign doesn't matter.

Reuses ssveps/files/subject_troughs.csv directly, not recomputed, and
fm100_features.reliability (already resolved there via the cross-project
sys.path dance) rather than repeating that a third time in this module.
"""

import os

import numpy as np
import pandas as pd
import pingouin as pg

import fm100_features

SUBJECT_TROUGHS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ssveps", "files", "subject_troughs.csv")

SEVERITY_FEATURES = ["ramp_magnitude", "ramp_intercept"]
TYPE_FEATURE = "ramp_angle_deg"


def load_subject_troughs(path: str = SUBJECT_TROUGHS_PATH) -> pd.DataFrame:
    """ssveps/files/subject_troughs.csv, read directly."""
    return pd.read_csv(path)


def subject_session_features(troughs_df: pd.DataFrame) -> pd.DataFrame:
    """EEG severity/type features for every (subject, session) row:
    sub_id, session, group, subgroup, ramp_magnitude, ramp_angle_deg (full
    [0, 360) direction -- see module docstring for the axial-fold caveat),
    ramp_intercept, plus the raw ramp_slope_red/green/r_squared passed
    through for reference."""
    df = troughs_df.copy()
    df["ramp_magnitude"] = np.hypot(df["ramp_slope_red"], df["ramp_slope_green"])
    df["ramp_angle_deg"] = np.degrees(np.arctan2(df["ramp_slope_green"], df["ramp_slope_red"])) % 360
    return df[["sub_id", "session", "group", "subgroup", "ramp_magnitude", "ramp_angle_deg", "ramp_intercept", "ramp_slope_red", "ramp_slope_green", "ramp_r_squared"]]


def paired_sessions(troughs_df: pd.DataFrame, *, sessions: tuple[int, int] = (1, 2)) -> pd.DataFrame:
    """EEG severity/type features for subjects present at both of
    `sessions`, one row per subject, each feature suffixed `_session{n}`.
    Raises ValueError if fewer than 3 subjects qualify."""
    per_session = subject_session_features(troughs_df)
    s1 = per_session[per_session["session"] == sessions[0]].set_index("sub_id")
    s2 = per_session[per_session["session"] == sessions[1]].set_index("sub_id")
    sub_ids = sorted(set(s1.index) & set(s2.index))
    if len(sub_ids) < 3:
        raise ValueError(f"only {len(sub_ids)} subjects have EEG data at both session {sessions[0]} and {sessions[1]} (need >= 3)")

    features = [TYPE_FEATURE] + SEVERITY_FEATURES
    table = pd.DataFrame({"sub_id": sub_ids})
    for feat in features:
        table[f"{feat}_session{sessions[0]}"] = s1.loc[sub_ids, feat].to_numpy()
        table[f"{feat}_session{sessions[1]}"] = s2.loc[sub_ids, feat].to_numpy()
    return table


def reliability_table(troughs_df: pd.DataFrame, *, group: str | None = None, subgroup: str | None = None, sessions: tuple[int, int] = (1, 2)) -> pd.DataFrame:
    """Cross-session reliability for the two *derived* features only:
    ICC(A,1) (fm100_features.reliability.feature_icc) for ramp_magnitude,
    circ_corrcc (after circ_axial folding, matching how it's actually used
    downstream) for ramp_angle_deg. ramp_slope_red/ramp_intercept's own
    reliability is already established (ssveps' M9, ICC 0.85/0.90) and
    isn't re-checked here.

    Optionally filtered by group/subgroup first -- protan/deutan/CVD
    (combined) are expected to raise (2/0/2 paired subjects, per
    docs/ssvepbeh_reliability_gaps.md's numbers, unchanged here since both
    projects draw from the same ssveps/files/subject_troughs.csv).

    Returns one row per feature: feature, n, statistic ('icc'|'circ_r'),
    value, p_value."""
    df = troughs_df
    if group is not None:
        df = df[df["group"] == group]
    if subgroup is not None:
        df = df[df["subgroup"] == subgroup]
    paired = paired_sessions(df, sessions=sessions)
    n = len(paired)

    result = fm100_features.reliability.feature_icc(paired[f"ramp_magnitude_session{sessions[0]}"].to_numpy(), paired[f"ramp_magnitude_session{sessions[1]}"].to_numpy())
    rows = [{"feature": "ramp_magnitude", "n": n, "statistic": "icc", "value": result["icc"], "p_value": result["pval"]}]

    angle1 = pg.circ_axial(np.deg2rad(paired[f"{TYPE_FEATURE}_session{sessions[0]}"].to_numpy()), 2)
    angle2 = pg.circ_axial(np.deg2rad(paired[f"{TYPE_FEATURE}_session{sessions[1]}"].to_numpy()), 2)
    r, p_value = pg.circ_corrcc(angle1, angle2)
    rows.append({"feature": TYPE_FEATURE, "n": n, "statistic": "circ_r", "value": r, "p_value": p_value})

    return pd.DataFrame(rows)
