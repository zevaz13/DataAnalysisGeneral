# ssvep_beh_fm100 scripts and notebooks: reference

Everything lives in `ssvep_beh_fm100/scripts/`. Notebooks
(`ssvep_beh_fm100/notebooks/`) call these directly. See
`ssvep_beh_fm100/README.md` for the two-pre-specified-tests rationale, the
FM100-reliability-first decision, and the cross-project import gotcha
(three source projects deep here -- read before adding a new import).

## `fm100_features.py` -- FM100 severity/type features and reliability

`SEVERITY_FEATURES = ["TES", "VKS_MajRad", "VKS_MinRad"]`,
`TYPE_FEATURE = "VKS_Angle"`.

- **`subject_session_features(fm100_df) -> DataFrame`**
  One row per (subject, session): `sub_id, session, group, subgroup, TES,
  VKS_Angle, VKS_MajRad, VKS_MinRad`. Reuses
  `standardizedScores/FM100/scripts/scores.py`'s `build_scores`.
- **`subject_pooled_features(fm100_df) -> DataFrame`**
  One row per subject: the three severity features averaged (linear mean)
  across that subject's available sessions; `VKS_Angle` averaged
  *circularly* (`circ_axial` + `circ_mean`, then folded back into
  `[0, 180)`) since it's periodic -- a naive linear mean of e.g. 179deg and
  1deg would wrongly give 90deg instead of ~0deg (verified numerically
  against `pingouin` before trusting the derivation). Adds `n_sessions`.
- **`paired_sessions(fm100_df, *, sessions=(1, 2)) -> DataFrame`**
  Features for subjects present at both `sessions`, one row per subject,
  each feature suffixed `_session{n}`. Raises `ValueError` below 3
  qualifying subjects.
- **`reliability_table(fm100_df, *, sessions=(1, 2)) -> DataFrame`**
  Cross-session reliability for all four features: ICC(A,1)
  (`ssveps/scripts/reliability.py`'s `feature_icc`) for the three magnitude
  features, `circ_corrcc` (after `circ_axial` folding) for `VKS_Angle`.
  Returns `feature, n, statistic ('icc'|'circ_r'), value, p_value`.

## `severity.py` -- multivariate severity test (feature-set-agnostic)

- **`cca_test(X, Y, *, n_perm=5000, seed=None) -> dict`**
  1-component CCA (`sklearn.cross_decomposition.CCA`) between `X`
  `(n_subjects, p)` and `Y` `(n_subjects, q)` -- rows must already be
  aligned to the same subjects in the same order. Seeded permutation test
  (shuffle `Y`'s row order, refit, repeat `n_perm` times) for whether the
  observed canonical correlation exceeds chance. Returns `{r, p_value,
  null_r, x_scores, y_scores}`. `r` is always `>= 0` (verified empirically:
  `sklearn`'s CCA finds the positively-correlated axis by construction, so
  even independent noise gives `r` up to ~0.5 at small n/feature-count) --
  the test is one-sided, `p_value = P(null_r >= r)`, with the `(1 + count)
  / (1 + n_perm)` correction (a permutation p-value can never legitimately
  be exactly 0). `x_scores`/`y_scores` are the observed fit's canonical
  variates, for `plotting.plot_canonical_variates`. Raises `ValueError` if
  `X`/`Y` have mismatched subject counts or fewer than 3 subjects.

## `type_axis.py` -- circular correlation test (feature-set-agnostic)

- **`circular_correlation_test(angles_deg_x, angles_deg_y) -> dict`**
  Circular-circular correlation (`pingouin.circ_corrcc`, after
  `circ_axial`-folding both inputs) between two same-subject-order,
  180deg-periodic angle arrays in degrees. Returns `{r, p_value, n}`.
  Raises `ValueError` on mismatched lengths.

## `plotting.py`

- **`plot_canonical_variates(cca_result, *, x_label=..., y_label=..., ax=None) -> Axes`**
  Scatter of `cca_test`'s observed `x_scores`/`y_scores`, titled with `r`/
  `p_value`/`n`.
- **`plot_null_distribution(cca_result, *, ax=None) -> Axes`**
  Histogram of `cca_test`'s `null_r` with the observed `r` marked -- makes
  explicit how extreme the observed canonical correlation is relative to
  chance (see `severity.py`'s note on why the raw `r` alone is misleading).
- **`plot_circular_scatter(angles_deg_x, angles_deg_y, *, x_label=..., y_label=..., ax=None) -> Axes`**
  Scatter of two periodic angle arrays, with gridlines at 0/180 marking the
  wrap point.
- **`plot_reliability_table(reliability_df, *, ax=None) -> Axes`**
  Bar chart of `fm100_features.reliability_table`'s per-feature statistic,
  colored by significance, p-value annotated per bar. y-axis spans
  `[-1, 1.1]` since both ICC and circular `r` can be negative.

## Notebooks

- **`01_fm100_reliability.ipynb`** -- M1a: `reliability_table` +
  `plot_reliability_table`; session 1 vs. session 2 scatter per feature.
  Verdict: three magnitude features reliable, `VKS_Angle` is not -- carried
  forward as a caveat into `02_fm100_vs_behavioral.ipynb`.
- **`02_fm100_vs_behavioral.ipynb`** -- M1b: merges `subject_pooled_features`
  with `beh/scripts/features.py`'s `subject_shape_features` (+ inline
  centroid). Runs `severity.cca_test` and `type_axis.circular_correlation_test`,
  pooled and per-group (`categories` list, top cell -- edit to check
  different group sets), plus a context-only univariate feature table
  (`pingouin.corr`, explicitly not used to claim significance). Ends with a
  summary of both results.
