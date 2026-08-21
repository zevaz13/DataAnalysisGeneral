"""Type/axis test: circular-circular correlation between per-subject angle
features -- M1/M2/M3, PLANssvep_bh_fm100.md.

Feature-set-agnostic by design (any angle arrays, in degrees, each folded
to [0, 180) the way beh's orientation_deg and FM100's VKS_Angle already
are) so M2 reuses circular_correlation_test unchanged against the EEG
ramp-angle, and M3 extends to a genuine >=2-array joint test
(joint_concordance_test) instead of duplicating the circular-correlation
machinery.

Uses pingouin's circ_axial (doubles the angle so a 180deg-periodic
"axial" quantity -- a line has no direction -- behaves like a proper
360deg circular one) and circ_corrcc (circular-circular correlation,
Berens 2009 / CircStats) rather than naive Pearson/Spearman on raw
degrees, which would be wrong near the 0/180 wrap point (a subject at
179deg and one at 1deg are 2deg apart, not 178deg apart).
"""

import numpy as np
import pingouin as pg


def circular_correlation_test(angles_deg_x: np.ndarray, angles_deg_y: np.ndarray) -> dict:
    """Circular-circular correlation between two same-subject-order,
    180deg-periodic angle arrays (degrees). Returns {r, p_value, n}."""
    angles_deg_x = np.asarray(angles_deg_x, dtype=float)
    angles_deg_y = np.asarray(angles_deg_y, dtype=float)
    if angles_deg_x.shape[0] != angles_deg_y.shape[0]:
        raise ValueError(f"both angle arrays must have the same length, got {angles_deg_x.shape[0]} and {angles_deg_y.shape[0]}")

    x_axial = pg.circ_axial(np.deg2rad(angles_deg_x), 2)
    y_axial = pg.circ_axial(np.deg2rad(angles_deg_y), 2)
    r, p_value = pg.circ_corrcc(x_axial, y_axial)
    return {"r": float(r), "p_value": float(p_value), "n": len(angles_deg_x)}


def _pairwise_r(axial_arrays: list[np.ndarray]) -> dict[tuple[int, int], float]:
    pairwise = {}
    for i in range(len(axial_arrays)):
        for j in range(i + 1, len(axial_arrays)):
            r, _ = pg.circ_corrcc(axial_arrays[i], axial_arrays[j])
            pairwise[(i, j)] = float(r)
    return pairwise


def joint_concordance_test(angle_arrays: list[np.ndarray], *, n_perm: int = 5000, seed: int | None = None) -> dict:
    """Joint test for whether >= 2 axial angle arrays (same subject order,
    degrees) agree with each other more than chance, as one statistic
    rather than one p-value per pair: mean(|pairwise circ_corrcc r|)
    across every pair.

    Absolute value because circular-correlation sign is an artifact of
    each pair's own coordinate convention, not comparable across different
    pairs -- confirmed empirically, not just suspected: M2's
    VKS_Angle-vs-EEG-ramp-angle r was negative, opposite in sign to M1's
    VKS_Angle-vs-orientation_deg result. A signed mean would let pairs
    partially cancel for no principled reason, understating real
    three-way structure whenever pairs don't happen to share a sign
    convention.

    Permutation null generalizes severity.cca_test's "shuffle Y relative
    to X" scheme to more than two arrays: angle_arrays[0] stays fixed,
    every other array's subject order is independently permuted (its own
    separate random permutation, not one shared shift -- otherwise the
    relationship *between* the non-anchor arrays would survive into the
    "null"), the statistic is recomputed, repeated n_perm times. Same
    (1 + count) / (1 + n_perm) p-value correction used everywhere else in
    this project.

    Returns {statistic, p_value, null_stat, pairwise_r}. pairwise_r is a
    dict {(i, j): r} of the observed (unpermuted) pairwise correlations
    (i < j, indices into angle_arrays), so the joint result can still be
    decomposed back into its components."""
    if len(angle_arrays) < 2:
        raise ValueError(f"need at least 2 angle arrays, got {len(angle_arrays)}")
    arrays = [np.asarray(a, dtype=float) for a in angle_arrays]
    n = arrays[0].shape[0]
    if any(a.shape[0] != n for a in arrays):
        raise ValueError(f"all angle arrays must have the same length, got {[a.shape[0] for a in arrays]}")

    axial = [pg.circ_axial(np.deg2rad(a), 2) for a in arrays]

    obs_pairwise = _pairwise_r(axial)
    obs_stat = float(np.mean([abs(r) for r in obs_pairwise.values()]))

    rng = np.random.default_rng(seed)
    null_stat = np.empty(n_perm)
    for k in range(n_perm):
        permuted = [axial[0]] + [a[rng.permutation(n)] for a in axial[1:]]
        pairwise = _pairwise_r(permuted)
        null_stat[k] = np.mean([abs(r) for r in pairwise.values()])

    p_value = float((1 + np.sum(null_stat >= obs_stat)) / (1 + n_perm))
    return {"statistic": obs_stat, "p_value": p_value, "null_stat": null_stat, "pairwise_r": obs_pairwise}
