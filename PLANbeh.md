The data in /home/sebas/data/manualTest includes results for the behavioral (manual test of my experiment.) This is to be implemented under /beh

## Documents

- `beh/README.md` -- data dictionary, script/notebook index, and
  implementation decisions (Hotelling T² package choice, `unit=` parameter,
  subgroup lookup, module-naming-collision fix). **Read this first.**
- `docs/beh_api_reference.md` -- every function's signature and parameters.
- `docs/findings.md` section 2 -- results narrative and interpretation.

### M1. Load, plot, and compare groups on click location

- [x] Load data (`loader.load_behavioral`), same participants/groups/subgroups
  as the SSVEP experiment.
- [x] Per-subject and per-group/subgroup plotting (`plotting.py`).
- [x] Hotelling T² group comparisons (`comparisons.py`), `unit='subject'`.

**All five group comparisons significant** (HC vs PD/CVD/protan/deutan,
protan vs deutan) -- see `docs/findings.md` section 2.

### M2. Shape features and comparisons

- [x] PCA shape features per subject (`features.py`): `orientation_deg`,
  `along_var`, `perp_var`.
- [x] Plotting (`show_fit=`, `plot_feature_space`) and per-feature
  comparisons (`compare_shape_feature`, Mann-Whitney U) on the same five
  group pairs as M1.

**`orientation_deg` separates protan from deutan perfectly** (p=0.0003) --
the strongest single finding in this project so far. See `docs/findings.md`
section 2.

### M3. Centroid plots

- [x] Per-subject and per-group centroid plots, for click location
  (`plot_subject_centroids`/`plot_group_centroids`) and for the M2 shape
  features (`plot_feature_space`/`plot_feature_group_centroids`).

Confirms M1/M2 visually; deutan is the least internally-consistent group by
far. See `docs/findings.md` section 2.

### M4. Reliability, HC vs PD, outlier ellipse

- [x] **`04_reliability.ipynb`** -- cross-session ICC/circular-r for
  centroid + M2 shape features, HC and PD only (CVD excluded: 6/7 deutan
  and 6/8 protan have only 1 session). New `beh/scripts/retest.py`, reusing
  `ssveps/scripts/reliability.py`'s `feature_icc` directly.
  **HC (n=21 paired) is mostly not reliable session-to-session** -- only
  `centroid_green` clears significance (ICC=0.60, p=0.0013); `centroid_red`,
  `along_var`, `perp_var`, `orientation_deg` all non-significant. **PD
  (n=6) has nothing significant either**, though `along_var`
  (ICC=0.58)/`orientation_deg` (circular r=0.76) are suggestively high at a
  sample size too small to confirm it. Doesn't contradict M2's headline
  `orientation_deg` finding (that used clicks pooled across all of a
  subject's sessions, a different and more forgiving question) but is a
  real caveat worth carrying forward before treating any single session's
  features as individually trustworthy.
- [x] **`05_hc_vs_pd.ipynb`** -- point clouds, Hotelling T² (p=0.0001,
  matches M1's number), all three shape features (all significant for this
  pair: orientation_deg p=0.006, along_var p=0.034, perp_var p=0.030), plus
  a new PD-specific check: `features.within_session_scatter` (click
  consistency within one sitting). **PD is significantly less consistent
  within a session** (Mann-Whitney p=0.023, ~70% larger RMS scatter than
  HC, 552 vs 320) -- a specific, confirmed answer to whether PD's motor
  symptoms show up as noisier clicking rather than (or alongside) a shifted
  match point.
- [x] **`06_outlier_rejection.ipynb`** -- new outlier-ellipse machinery in
  `features.py` (`outlier_mask`, `subject_outliers`, `group_outliers`) and
  `plotting.py` (`plot_subject_outliers`/`plot_subjects_outliers_grid`,
  `n_std=` parameter, default 2.0). Per-participant (each subject's own
  ellipse) and group-level (one shared group/subgroup ellipse, applied back
  to every individual subject) versions, sharing one plotting function via
  a `shared_pca=` override. **Flagged fractions are similar and
  unremarkable across every group** (HC 12.6%, PD 15.5%, protan 10.5%,
  deutan 11.5% of clicks) and nearly every subject has at least one point
  flagged, which is expected at `n_std=2.0` with ~20-60 clicks per subject,
  not a sign of a systematic problem in any one group. Purely exploratory
  -- nothing here filters persisted data. Read as an honest "nothing
  alarming turned up" rather than a case for adding automatic rejection to
  the pipeline by default.

## Next milestones

To be defined together.
