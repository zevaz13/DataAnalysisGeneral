# ssvep_beh_fm100 (FM100 vs. behavioral, later vs. EEG)

Tests the hypothesis that FM100 encodes a continuous "severity of color
perception deficiency" spectrum, masked by the categorical protan/deutan/
HC/PD labels -- and that this spectrum correlates with behavioral (and
later EEG) features. `PLANssvep_bh_fm100.md`'s scope; M1 covers FM100 vs.
behavioral, M2 (not yet started) extends the same structure to EEG.

No raw data of its own -- reuses `standardizedScores/FM100/scripts/scores.py`
and `beh/scripts/features.py` directly. Function-by-function reference:
`docs/ssvep_beh_fm100_api_reference.md`. Plan and milestone status:
`../PLANssvep_bh_fm100.md`.

## Two pre-specified tests, not a matrix of many

`ssvepBeh/`'s correlation work (`docs/ssvepbeh_reliability_gaps.md`) tested
25 univariate feature pairs and found nothing survived multiple-comparisons
correction. This project avoids that structurally: FM100's features split
naturally into severity (`TES`, `VKS_MajRad`, `VKS_MinRad` -- error
magnitude) and type/axis (`VKS_Angle` -- confusion-ellipse direction),
mirroring `beh/`'s own M2 split (`along_var`/`perp_var` vs.
`orientation_deg`). One multivariate test (CCA) for severity, one circular
correlation for type/axis -- two pre-specified hypotheses, not 25 fished
from a matrix. A univariate feature table is still shown in
`02_fm100_vs_behavioral.ipynb` for context, but explicitly never used to
claim significance.

## FM100 reliability, checked first

`ssvepBeh/` found a promising-looking correlation that didn't survive
correction or a cross-session reliability check -- discovered only after
building on it. This project checks FM100's own cross-session reliability
*first* (`01_fm100_reliability.ipynb`): the three magnitude features are
highly reliable (ICC 0.84-0.93), but `VKS_Angle` is not (circular r=0.44,
p=0.15) -- carried forward explicitly as a caveat on the type/axis result,
not discovered after the fact.

## Scripts

- `scripts/fm100_features.py` -- per-subject/session and pooled-across-
  sessions FM100 severity/type features; cross-session reliability
  (`reliability_table`, ICC for magnitude features via
  `ssveps/scripts/reliability.py`'s `feature_icc`, circular correlation for
  `VKS_Angle` since it's periodic).
- `scripts/severity.py` -- `cca_test`: CCA + seeded permutation
  significance test. **Feature-set-agnostic** (any two per-subject feature
  matrices) so M2 reuses it against EEG features unchanged.
- `scripts/type_axis.py` -- `circular_correlation_test`: `circ_axial` +
  `circ_corrcc` between two angle arrays. Also feature-set-agnostic.
- `scripts/plotting.py` -- canonical-variate scatter, permutation null
  histogram, circular scatter, reliability bar chart.

## A permutation p-value can't legitimately be exactly 0

Same fix `ssvepBeh/scripts/overlap.py` applies (`docs/ssvep_summary.md`
finding 2.7): `severity.cca_test` uses `p = (1 + count) / (1 + n_perm)`,
not `(null > obs).mean()`.

## sklearn's CCA always returns r >= 0

Verified empirically before trusting it: even pure independent Gaussian
noise (n=30, 3 vs. 2 features) produces a raw canonical correlation up to
~0.48 by chance. The permutation test in `severity.cca_test` is not
optional decoration -- a raw canonical correlation is meaningless without
it.

## Cross-project imports: the same gotcha as `ssvepBeh/`, now three deep

`fm100_features.py` needs both `standardizedScores/FM100/scripts/` (for
`loader`/`scores`) and `ssveps/scripts/` (for `reliability`), and the
notebooks additionally need `beh/scripts/` (for `loader`/`features`).
`beh/`, `ssveps/`, `standardizedScores/FM100/`, `ssvepBeh/`, and this
project all have `loader.py`; several have `plotting.py` too. Every
cross-project import in this project's scripts and notebooks explicitly
moves the target directory to `sys.path[0]` (not just inserts if absent --
a path already present further back in `sys.path` from an earlier import
elsewhere in the process is not "resolved first") and drops any stale
cached module before importing. See `fm100_features.py`'s own import block
for the pattern, and re-apply it (don't just `sys.path.append`) any time a
new cross-project import is added here.

## Tests

`uv run pytest ssvep_beh_fm100/tests -q`. Includes a pin of the circular-
mean-folding derivation verified against `pingouin` directly (mean of
[179deg, 1deg] must fold to ~0deg, not the naive linear mean of 90deg), a
check that `sklearn`'s CCA never returns a negative r, and pins of the real
M1 findings (severity CCA pooled significant, type/axis pooled and
within-CVD significant) as regression tests.

## Notebooks

- `01_fm100_reliability.ipynb` -- M1a: FM100's own cross-session
  reliability. Three magnitude features reliable (ICC 0.84-0.93);
  `VKS_Angle` is not (circular r=0.44, p=0.15) -- carried forward as a
  caveat, not a blocker.
- `02_fm100_vs_behavioral.ipynb` -- M1b: the two primary tests, pooled and
  per-group. **Severity**: strong pooled (r=0.73, p<0.001), but doesn't
  hold up within any single group at this n -- likely partly a
  between-group effect, not yet confirmed as a within-group continuum.
  **Type/axis**: significant pooled (r=0.37, p=0.009) *and* within CVD
  alone (r=0.56, p=0.031, n=15) -- the more solid of the two results,
  though riding on `VKS_Angle`'s weaker reliability. A context-only
  univariate feature table, and a summary of both results.
