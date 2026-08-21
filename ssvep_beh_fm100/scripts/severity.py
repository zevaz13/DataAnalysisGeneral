"""Multivariate severity test: Canonical Correlation Analysis (CCA)
between two per-subject feature bundles, with a seeded permutation test for
the top canonical correlation's significance -- M1, PLANssvep_bh_fm100.md.

Feature-set-agnostic by design (any two same-subject-order feature
matrices) so M2 reuses this unchanged against EEG features instead of
duplicating the CCA/permutation machinery -- see PLANssvep_bh_fm100.md's
"Decisions" section.

**The permutation test is essential, not optional.** sklearn's CCA always
returns a non-negative canonical correlation (verified: even pure
independent Gaussian noise at n=30 subjects with 3 and 2 features per side
produces raw r up to ~0.48 by chance -- CCA has enough degrees of freedom
with only a handful of features to find a spurious axis of alignment). A
raw canonical correlation is not interpretable on its own; only its
position relative to the permutation null is.
"""

import numpy as np
from sklearn.cross_decomposition import CCA


def _canonical_correlation(X: np.ndarray, Y: np.ndarray) -> float:
    _, x_c, y_c = _fit_cca(X, Y)
    return float(np.corrcoef(x_c[:, 0], y_c[:, 0])[0, 1])


def _fit_cca(X: np.ndarray, Y: np.ndarray) -> tuple[CCA, np.ndarray, np.ndarray]:
    cca = CCA(n_components=1)
    x_c, y_c = cca.fit_transform(X, Y)
    return cca, x_c, y_c


def cca_test(X: np.ndarray, Y: np.ndarray, *, n_perm: int = 5000, seed: int | None = None) -> dict:
    """Fits a 1-component CCA between X (n_subjects, p) and Y (n_subjects,
    q) -- rows must already be aligned to the same subjects in the same
    order -- then a permutation test for whether the resulting canonical
    correlation is bigger than chance: shuffle Y's row order (breaking the
    subject correspondence while keeping each side's own covariance
    structure intact), refit, repeat n_perm times.

    Returns {r, p_value, null_r, x_scores, y_scores}. r is always >= 0 (see
    module docstring), so the test is one-sided: p_value = P(null_r >= r),
    with the (1 + count) / (1 + n_perm) correction (a permutation p-value
    can never legitimately be exactly 0 -- see ssvepBeh/scripts/overlap.py's
    docstring for the same reasoning applied there). x_scores/y_scores are
    the observed (unpermuted) fit's canonical variates, length n_subjects
    each -- what plotting.plot_canonical_variates scatters."""
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    if X.shape[0] != Y.shape[0]:
        raise ValueError(f"X and Y must have the same number of subjects, got {X.shape[0]} and {Y.shape[0]}")
    if X.shape[0] < 3:
        raise ValueError(f"need at least 3 subjects, got {X.shape[0]}")

    _, x_scores, y_scores = _fit_cca(X, Y)
    obs_r = float(np.corrcoef(x_scores[:, 0], y_scores[:, 0])[0, 1])

    rng = np.random.default_rng(seed)
    null_r = np.empty(n_perm)
    for i in range(n_perm):
        perm = rng.permutation(Y.shape[0])
        null_r[i] = _canonical_correlation(X, Y[perm])

    p_value = float((1 + np.sum(null_r >= obs_r)) / (1 + n_perm))
    return {"r": obs_r, "p_value": p_value, "null_r": null_r, "x_scores": x_scores[:, 0], "y_scores": y_scores[:, 0]}
