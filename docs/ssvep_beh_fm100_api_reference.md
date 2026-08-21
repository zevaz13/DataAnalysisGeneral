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

## `eeg_features.py` -- EEG severity/type features and reliability (M2)

`SEVERITY_FEATURES = ["ramp_magnitude", "ramp_intercept"]`,
`TYPE_FEATURE = "ramp_angle_deg"`. Reuses
`fm100_features.reliability` (already resolved there) rather than
re-running the cross-project `sys.path` dance a third time.

- **`load_subject_troughs(path=SUBJECT_TROUGHS_PATH) -> DataFrame`**
  `ssveps/files/subject_troughs.csv`, read directly.
- **`subject_session_features(troughs_df) -> DataFrame`**
  One row per (subject, session): `sub_id, session, group, subgroup,
  ramp_magnitude, ramp_angle_deg, ramp_intercept, ramp_slope_red,
  ramp_slope_green, ramp_r_squared`. `ramp_magnitude = hypot(ramp_slope_red,
  ramp_slope_green)`. `ramp_angle_deg = degrees(atan2(ramp_slope_green,
  ramp_slope_red)) % 360` -- the **full** directional angle, not folded to
  axial. Unlike `VKS_Angle`/`orientation_deg` (a PCA/ellipse axis, sign
  arbitrary by construction), this gradient direction is genuinely
  meaningful; folding to axial `[0, 180)` is applied only downstream
  (`reliability_table` below, and `type_axis.circular_correlation_test`'s
  cross-modality use), not at storage time -- see the module docstring for
  the full reasoning.
- **`paired_sessions(troughs_df, *, sessions=(1, 2)) -> DataFrame`**
  Same shape/contract as `fm100_features.paired_sessions`.
- **`reliability_table(troughs_df, *, group=None, subgroup=None, sessions=(1, 2)) -> DataFrame`**
  ICC(A,1) for `ramp_magnitude`, `circ_corrcc` (after `circ_axial` folding)
  for `ramp_angle_deg` -- **only the two derived features**; `ramp_slope_red`/
  `ramp_intercept`'s own reliability is already established (`ssveps/`'s M9)
  and isn't re-checked. Optional `group`/`subgroup` filter. Raises
  `ValueError` below 3 paired subjects -- expected for `group='CVD',
  subgroup='deutan'` (0 paired), `subgroup='protan'` (2), and `group='CVD'`
  combined (2), per `docs/ssvepbeh_reliability_gaps.md`'s numbers (same
  underlying `ssveps/files/subject_troughs.csv`).

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

## `type_axis.py` -- circular correlation tests (feature-set-agnostic)

- **`circular_correlation_test(angles_deg_x, angles_deg_y) -> dict`**
  Circular-circular correlation (`pingouin.circ_corrcc`, after
  `circ_axial`-folding both inputs) between two same-subject-order,
  180deg-periodic angle arrays in degrees. Returns `{r, p_value, n}`.
  Raises `ValueError` on mismatched lengths.
- **`joint_concordance_test(angle_arrays, *, n_perm=5000, seed=None) -> dict`** (M3)
  Joint test for whether `>= 2` axial angle arrays (same subject order,
  degrees) agree with each other more than chance, as **one** statistic
  rather than one p-value per pair: `mean(|pairwise circ_corrcc r|)` across
  every pair. Uses **absolute value**, not a signed mean -- circular-
  correlation sign is an artifact of each pair's own coordinate convention,
  confirmed not comparable across pairs (M2's `VKS_Angle`-vs-EEG-ramp-angle
  r was negative, opposite in sign to M1's `VKS_Angle`-vs-`orientation_deg`
  result); a signed mean would let pairs partially cancel for no principled
  reason. Permutation null generalizes `severity.cca_test`'s "shuffle `Y`
  relative to `X`" scheme to more than two arrays: `angle_arrays[0]` stays
  fixed, every other array gets its own independent random permutation
  (not one shared shift -- that would let the relationship *between* the
  non-anchor arrays survive into the "null"), the statistic is recomputed,
  repeated `n_perm` times. Same `(1 + count) / (1 + n_perm)` p-value
  correction as `cca_test`. Returns `{statistic, p_value, null_stat,
  pairwise_r}` -- `pairwise_r` is `{(i, j): r}` for the observed
  (unpermuted) pairwise correlations, so the joint result decomposes back
  into its components. Raises `ValueError` for fewer than 2 arrays or
  mismatched lengths.

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
- **`plot_pairwise_bars(joint_result, labels, *, ax=None) -> Axes`** (M3)
  Bar chart of `joint_concordance_test`'s three (or more) observed
  `|pairwise r|` values, with a dashed line at the joint statistic --
  shows which edge(s) of the triangle actually carry the joint result.
  `labels` names each angle array in the same order passed to
  `joint_concordance_test` (e.g. `['FM100', 'Behavioral', 'EEG']`).
- **`plot_joint_null_distribution(joint_result, *, ax=None) -> Axes`** (M3)
  Histogram of `joint_concordance_test`'s `null_stat` with the observed
  statistic marked -- same pattern as `plot_null_distribution`, for the
  joint concordance statistic instead of a CCA canonical correlation.

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
- **`03_eeg_reliability.ipynb`** -- M2a: `eeg_features.reliability_table` +
  `plotting.plot_reliability_table`, pooled and per-group (CVD/protan/deutan
  expected to raise, shown via a `try`/`except` loop). Verdict: both
  derived features moderately, not strongly, reliable -- carried forward as
  a caveat into `04_fm100_vs_eeg.ipynb`.
- **`04_fm100_vs_eeg.ipynb`** -- M2b: merges `fm100_features.subject_pooled_features`
  with `eeg_features.subject_session_features` filtered to session 1 (EEG
  features aren't pooled across sessions the way FM100's are -- matches
  `ssvepBeh/`'s own convention of using EEG session 1). Runs
  `severity.cca_test`/`type_axis.circular_correlation_test` **completely
  unchanged from M1** against the EEG severity/type feature bundles, pooled
  and per-group, plus a context-only univariate table. Ends with a summary
  comparing M1's and M2's results directly.
- **`05_three_way_type_axis.ipynb`** (M3) -- merges all three feature
  tables (FM100 pooled, `beh` shape features, EEG session 1), one row per
  subject present in all three (43). Completes the triangle
  (`orientation_deg` vs. EEG ramp-angle -- **not significant pooled**,
  r=-0.23, p=0.13) then runs `joint_concordance_test` on all three angles
  (**significant pooled**, mean|r|=0.33, p=0.0012, despite the missing
  edge), pooled and per-group (`protan` alone significant on the
  triangle-completion edge specifically, r=-0.57, p=0.023, n=8 -- a lead,
  not a confirmed finding at that n). Ends with a summary of the whole
  three-way picture.
