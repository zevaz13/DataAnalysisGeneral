# SSVEP project plan

Raw data: `/home/sebas/data/ssveps/` - 62 MATLAB files, 43 subjects.
`METxxx` is the subject id; the filename suffix gives the session
(none = 1, `b` = 2, `c` = 3; no `c` files exist in this dataset).

Reference MATLAB implementations live in `ssveps/templateCode/` (gitignored).

## Documents

- `docs/ssvep_summary.md` - section 1 (what exists) is kept current through
  M10; sections 2-4 are a dated M1-M5 code review. **Read section 1 first.**
- `docs/methods.md` - analysis conventions (normalization, axes, ICC, permutation)
  and the full methodology behind every M6-M10 analysis below.
- `docs/api_reference.md` - every public function's signature and parameters.
- `docs/ssvep_analyses.md` - the seven proposed analyses (2-5, 7 implemented
  as M6-M10 below).
- `docs/findings.md` section 3 - results narrative and interpretation.
- `ssveps/README.md` - data dictionary and script/notebook index.

## Completed (M1-M5)

Delivered and in the repo. Detail lives in `docs/ssvep_summary.md` section 1;
this is the index.

- **M1 - Ingest and visualize.** `loader.py`, `build_derived.py`,
  `update_derived.py`; tidy CSVs in `ssveps/files/`; three normalizations
  (percent/db/zscore) over selectable baseline scope and trial subsets;
  single-subject, group, and interpolated heatmaps. Notebooks 01-03.
- **M2 - Distributions and trough location.** Boxplots/histograms per subject,
  per group (pooled and mean-grid); `trough_location` plus persisted
  `subject_troughs.csv` / `group_troughs.csv`. Notebook 04.
- **M3 - Cluster-based permutation testing.** Three functions mirroring the
  three MATLAB templates (size, size+weight, directional), generalized to any
  group/subgroup pair, seeded, with a corrected negative-cluster null.
  Notebook 05.
- **M4 - Parametric trough surface fit.** `fit_paraboloid` and `fit_gaussian`
  behind `fit_trough_surface`, with `fit_valid` and `r_squared` reported.
  Notebook 06.
- **M5 - Test-retest reliability.** Per-pixel ICC(A,1) maps via `pingouin`,
  paired-subject discovery, Bland-Altman and session-scatter plots.
  Notebook 07.

## Open issues

From the code review in `docs/ssvep_summary.md` section 2, which carries the
evidence and the suggested fix for each.

Next up:

- [x] **Re-run every notebook.** The axis fix changed all reported trough
  coordinates, and the subsampling fix changed M3's results.
- [x] Work through `docs/ssvep_analyses.md` proposals 2, 3, 4, 5, 7 -- see
  M6-M10 below.

Cleanup:

- [ ] Small correctness and consistency items (2.7): permutation p-value `+1`
  correction, `zscore` `ddof`, `plotting` -> `reliability` import chain,
  `load_grid_axes` caching, inconsistent `normalize` defaults.
- [ ] Factor the repeated subject/category resolution in `plotting.py` (2.8).
- [ ] Repo hygiene (2.9): remove `Untitled Folder/`, decide on notebook
  outputs, make the notebook import path robust.

## Done since the review

Bug fixes and refactors from the M1-M5 code review, all landed. Evidence and
detail: `docs/ssvep_summary.md` sections 2 and 4.

- [x] Trough surface fit replaced (2.4) with `fit_ramp_gaussian`, now the
  default; converges on 62/62 rows.
- [x] `docs/ssvep_analyses.md` written -- seven proposed analyses.
- [x] Red/green axis naming fixed at the source (2.1) -- a real bug, verified
  against the reference image.
- [x] Test suite added (2.2) -- `uv run pytest ssveps/tests -q`, 14 tests.
- [x] Permutation no longer discards subjects (2.3).
- [x] Both build scripts unified (2.5) onto `loader.write_derived_csv`,
  fixing two data quality issues found while verifying.
- [x] `ssveps/README.md` rewritten, `methods.md`'s permutation section
  corrected (2.6).
- [x] Raw baseline comparison across groups added to `04_distributions.ipynb`
  (addresses proposal 6's PD-baseline flag directly).

## Next milestones (M6-M10): proposed analyses

Implemented proposals 2, 3, 4, 5, and 7 from `docs/ssvep_analyses.md`, in
that order. Proposal 6 (normalization choice) is settled, not a milestone.
Proposal 1 (power) is context, not an analysis.

**Governing goal.** The strongest, best-powered effect in the dataset is
CVD vs HC. The question we actually want the test to answer is bifold:
(1) does this person have a CVD, and (2) if so, which type -- deutan or
protan. Proposal 2 is the primary lever for both halves, so it leads.

**Normalization convention:** percent change is the primary outcome measure;
db is a sensitivity check; z-score is not used for cross-group comparisons.
Full reasoning in `docs/methods.md`.

- [x] **M6 - Proposal 2: CVD gamut as a diagnostic.** `08_cvd_gamut.ipynb`.
  `fitted_at_bound` as a CVD-vs-HC classifier (sensitivity 0.73, specificity
  0.81, p=0.0019); `ramp_slope_red` established as the reusable per-subject
  measure. Protan-vs-deutan not yet significant (p=0.44) at current n.
  Method and full numbers: `docs/methods.md`; results: `docs/findings.md`
  section 3.
- [x] **M7 - Proposal 3: variance decomposition.** `09_variance_components.ipynb`,
  `variance.py`. Per-group random-intercept MixedLM. PD within-subject SD
  not elevated vs CTR; deutan's between-subject SD came out lower than CTR's
  (unexpected, flagged as a real finding to revisit). Method: `docs/methods.md`.
- [x] **M8 - Proposal 4: gain vs. shape decomposition.** `10_gain_shape.ipynb`.
  `fit_gain_shape` per subject; protan shows a genuine trough-specific
  residual beyond gain (p=0.030), PD/deutan don't. Method: `docs/methods.md`.
- [x] **M9 - Proposal 5: reliability-first outcome selection.**
  `11_reliability_outcomes.ipynb`. `ramp_slope_red`/`gain` are more reliable
  (ICC 0.85/0.90) than `depth` (0.76) and now the recommended primary
  outcome for CVD/subtype work; `fitted_red` (ICC 0.18) ruled unusable.
  Recorded in `docs/methods.md`.
- [x] **M10 - Proposal 7: joint (PCA) treatment of the 100-cell grid.**
  `12_pca.ipynb`, `pca.py`. Only PC1 (75% of variance) clears the
  permutation-based noise floor; PC1 tracks `gain`/`ramp_intercept` almost
  exactly (r=-0.93). Method: `docs/methods.md`.

## M6-M10: where this leaves things

Full writeup: `docs/findings.md` section 3. The two standing experimental
recommendations, unchanged since M6:

- Extend the red stimulus axis -- would directly address the protan/deutan
  subtype question (several measures point the same direction but none
  individually clears significance at n=7 vs 8).
- Collect more PD/protan/deutan subjects -- would directly address every
  underpowered comparison above; no analytical method rescues power that
  isn't there.
## M11.

- [x] **MET047 SSVEP data -- blocked, not added.** `MET047.mat` exists in
  `/home/sebas/data/ssveps/` but doesn't match the schema every other
  subject's raw file has: no `session`, `group`, `subgroup`, `runMap`, or
  `baselines` -- running it through `update_derived.py` crashes
  (`KeyError: 'session'`). Instead it has `MatrixRawNorm (10,10,3)`,
  `NormMatrix (10,10)`, `NormMatrixIntr (100,100)`, `reconstrMatrix (10,10,3)`,
  `baselineCCAr (4,3)` -- looks like an already-processed/normalized export
  from a different pipeline, not a raw recording. Per your call: **hold off
  until a standard-schema export exists**, rather than guessing what those
  fields mean and silently mislabeling a real subject's data. Needs, from
  whoever produced this file: `session`, `group` (your instinct to use
  `'UNKNOWN'` matches this project's own precedent -- `standardizedScores/
  FM100/` already labels MET047 `group='UNKNOWN'` for exactly this "not sure
  what deficiency this is" reason), `subgroup='NA'`, `runMap` (raw
  10x10xN_runs amplitude), and `baselines` (trial x run), same shape as
  every other `MET*.mat` file (`ssveps/README.md`'s Fields section).
- [x] **`13_hc_vs_pd.ipynb`** -- side-by-side raw/percent grids, a
  `permutation_test_size` difference map, and `ramp_slope_red` (subject-
  level, the number the significance claim rests on, per your decision) +
  pixel-level pooled boxplot (descriptive only) for HC vs PD. **Not
  significant** (Mann-Whitney p=0.89) -- consistent with PD being
  underpowered everywhere else in this project, not a new finding.
- [x] **`14_hc_vs_subtypes.ipynb`** -- same structure, three-way
  HC/protan/deutan, three pairwise `ramp_slope_red` comparisons
  (uncorrected, matching `beh/`'s own M1 convention). **HC vs protan
  (p=0.0019) and HC vs deutan (p=0.048) significant; protan vs deutan is
  not** (p=0.69) -- matches M6's earlier number on the same measure almost
  exactly.
- [x] **`15_permutation_stability.ipynb`** -- protan vs deutan, all three
  `permutation_test_*` variants, 200 independent seeds each. **A
  corrected-significant cluster is found in 173-196 of 200 seeds
  (86.5%-98%)** -- a stable, seed-robust result, not a fluke.
  **Unexpected finding, not what this item set out to check:** this
  contradicts the project's working narrative that protan-vs-deutan "isn't
  significant yet" (M6's `ramp_slope_red` p=0.44, M10's PCA PC1 p=0.092).
  Reconciled, not a bug: those are whole-grid scalar summaries; this
  cluster-based test finds the real difference is spatially localized (low-
  red/high-green corner, protan higher than deutan there), which a
  whole-grid summary averages away. This exact result already existed at a
  single seed in `05_permutation_testing.ipynb` (p=0.046) but was never
  carried into this plan's M3/M6 write-ups -- not a computation error, just
  a finding that never made it into the narrative until this stability
  check surfaced it. See `docs/methods.md`'s M3 section for the full
  writeup and the cluster's exact location.
- [x] **`fit_rotated_gaussian`** (`ssveps/scripts/analysis.py`, purely
  additive) -- generalizes `fit_ramp_gaussian`'s axis-aligned dip to a
  rotated, anisotropic one (`sigma_major`/`sigma_minor`/`orientation_deg`,
  folded to `[0, 180)` matching `beh/`'s own convention), per your direction
  to start from `fit_ramp_gaussian`. Tests (including a synthetic
  known-tilted-dip recovery check) in `ssveps/tests/test_ssveps.py`; new
  `rotated_*` columns added to `subject_troughs.csv` alongside the existing
  ones (verified byte-identical, nothing existing changed).
- [x] **`16_grid_shape_features.ipynb`** -- the new fit applied per subject;
  `rotated_orientation_deg` vs `rotated_sigma_major` scatter, the direct
  analog of `beh/notebooks/02_shape_features.ipynb`'s `plot_feature_space`.
  **Not enough valid fits yet to compare protan vs deutan** (`rotated_valid`
  is 25% for protan (2/8), 43% for deutan (3/7), vs 90%/100% for HC/PD) --
  the tilt is one more parameter to identify, on top of CVD's already-common
  pegged-trough failure mode (M6). Model itself works as intended (see the
  test suite); what's missing is data -- more CVD/protan/deutan subjects is
  the standing recommendation here too, now also blocking this specific
  comparison.
- [x] **CVD gamut analysis, explained** -- answered directly in
  conversation (not a doc section): `fit_ramp_gaussian` fits a ramp with a
  dip; for most CVD subjects the dip's best fit wants to sit beyond the
  sampled red range and pegs at the boundary instead (`at_bound=True`, 11/15
  CVD vs 4/21 CTR at session 1). M6 uses that peg/no-peg split itself as the
  CVD-vs-HC classifier (73%/81% sensitivity/specificity, p=0.0019), and
  introduces `ramp_slope_red` (ramp only, no dip, always defined) as the
  usable severity measure for subjects whose dip can't be located.
  `extrapolate_ramp_crossing` is a separate, explicitly unstable attempt to
  guess where a pegged subject's trough would be -- group-level qualitative
  support only, never a per-subject number to compare on.

## Next milestones

The M11 stability check surfaced a real, specific lead worth prioritizing
before anything else: the protan-vs-deutan grid difference in the low-red/
high-green corner (`15_permutation_stability.ipynb`, `docs/methods.md`'s
M3 section) is more solid than any previously-reported subtype signal in
this project and hasn't been investigated beyond "a cluster survives
correction" -- worth a closer look (e.g. does `10_gain_shape.ipynb`'s
protan trough-region residual sit in the same region?) before the next
round of analysis design.

The two standing experimental recommendations are otherwise unchanged:
extend the red stimulus axis, and collect more PD/protan/deutan subjects
(now also the blocker for M11's own rotated-fit shape-feature comparison).

The metric for measuring the shape of the metamer could be based on a threshold.
To be defined together when we come back to this.
