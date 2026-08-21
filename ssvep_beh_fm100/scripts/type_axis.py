"""Type/axis test: circular-circular correlation between two per-subject
angle features -- M1, PLANssvep_bh_fm100.md.

Feature-set-agnostic by design (any two angle arrays, in degrees, each
folded to [0, 180) the way beh's orientation_deg and FM100's VKS_Angle
already are) so M2 reuses this unchanged against the EEG ramp-angle
instead of duplicating the circular-correlation machinery.

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
