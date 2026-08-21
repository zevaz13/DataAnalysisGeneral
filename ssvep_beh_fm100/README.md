# ssvep_beh_fm100 (FM100 vs. behavioral, and vs. EEG)

Tests the hypothesis that FM100 encodes a continuous "severity of color
perception deficiency" spectrum, masked by the categorical protan/deutan/
HC/PD labels -- and that this spectrum correlates with behavioral and EEG
features. `PLANssvep_bh_fm100.md`'s scope; M1 covers FM100 vs. behavioral,
M2 extends the same structure to EEG, M3 asks whether all three agree
*jointly*, not just pairwise.

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
- `scripts/eeg_features.py` (M2) -- EEG severity/type features derived
  from `ssveps/files/subject_troughs.csv`'s ramp fit: `ramp_magnitude`
  (severity, direction-independent) and the ramp-vector's angle
  (type/axis) -- see its module docstring for why the angle's genuine
  directionality is deliberately folded to axial only where it's actually
  compared against `VKS_Angle`/`orientation_deg`. Reuses
  `fm100_features.reliability` rather than re-resolving `ssveps/`'s
  reliability module a second time.
- `scripts/severity.py` -- `cca_test`: CCA + seeded permutation
  significance test. **Feature-set-agnostic** (any two per-subject feature
  matrices) -- used unchanged by both M1 (vs. behavioral) and M2 (vs. EEG).
- `scripts/type_axis.py` -- `circular_correlation_test`: `circ_axial` +
  `circ_corrcc` between two angle arrays, reused unchanged in M2.
  `joint_concordance_test` (M3): the same tool generalized to `>= 2` angle
  arrays at once -- `mean(|pairwise r|)`, permutation-tested. See "Circular
  correlation sign isn't comparable across pairs" below for why it's an
  absolute-value mean, not signed.
- `scripts/plotting.py` -- canonical-variate scatter, permutation null
  histogram, circular scatter, reliability bar chart, and (M3) a pairwise-
  `|r|` bar chart + joint-statistic null histogram.

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

## Circular correlation sign isn't comparable across pairs -- confirmed, not just suspected

M2's `VKS_Angle`-vs-EEG-ramp-angle pooled r was **negative** (-0.40),
opposite in sign to M1's `VKS_Angle`-vs-`orientation_deg` result
(**+0.37**) -- each pair of angle spaces has its own arbitrary coordinate
convention, so sign carries no meaning across different pairs.
`type_axis.joint_concordance_test`'s statistic is therefore
`mean(|pairwise r|)`, not a signed mean: a signed combination would let
pairs partially cancel for no principled reason, exactly the failure mode
these two real results already demonstrate.

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
check that `sklearn`'s CCA never returns a negative r, a pin of the real
paired-EEG-subject count (19) behind M2's reliability gap, a check that
`joint_concordance_test`'s `|r|` statistic exceeds what a naive signed mean
would give on a constructed equal-and-opposite-correlation example, and
pins of the real M1/M2/M3 findings (both severity CCAs, all three
pairwise type/axis correlations, and the joint concordance test) as
regression tests.

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
- `03_eeg_reliability.ipynb` -- M2a: the two derived EEG features'
  reliability. Both moderate, not strong: `ramp_magnitude` ICC=0.65 (lower
  than `ramp_slope_red`'s own established 0.85 -- combining it with
  `ramp_slope_green` diluted it), ramp-angle circular r=0.69. As expected
  going in, CVD/protan/deutan can't be checked at all (2/2/0 paired
  subjects).
- `04_fm100_vs_eeg.ipynb` -- M2b: the same two tests against EEG, reusing
  `severity.py`/`type_axis.py` unchanged. **Severity**: significant pooled
  (r=0.50, p=0.047) but weaker than the behavioral version, and doesn't
  hold up per-group. **Type/axis**: significant pooled (r=-0.40, p=0.014);
  per-group, only `deutan` (n=7, r=0.66, p=0.034) reaches significance --
  a lead, not a confirmed finding at that n, weaker than M1's within-CVD
  result. Both EEG results are weaker than their behavioral counterparts,
  consistent with EEG being the noisier measure throughout this project.
- `05_three_way_type_axis.ipynb` -- M3: completes the triangle
  (`orientation_deg` vs. EEG ramp-angle -- **not significant pooled**,
  r=-0.23, p=0.13, the one edge that doesn't hold up alone), then runs
  `joint_concordance_test` on all three angles -- **significant pooled**
  (mean|r|=0.33, p=0.0012) *despite* that missing edge. The strongest
  whole-project argument yet for the "masked continuous spectrum"
  hypothesis: a pattern spread across a triangle, robust to any one weak
  edge, not concentrated in a single measurement. No group confirms the
  joint result on its own at current n; `protan` alone is significant on
  the triangle-completion edge specifically (r=-0.57, p=0.023, n=8) -- a
  new lead, not yet a finding.
