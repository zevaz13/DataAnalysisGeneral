# SSVEP project plan

Raw data: `/home/sebas/data/ssveps/` - 62 MATLAB files, 43 subjects.
`METxxx` is the subject id; the filename suffix gives the session
(none = 1, `b` = 2, `c` = 3; no `c` files exist in this dataset).

Reference MATLAB implementations live in `ssveps/templateCode/` (gitignored).

## Documents

- `docs/ssvep_summary.md` - what has been built, code review findings, and the
  suggested order of work. **Read this first.**
- `docs/methods.md` - analysis conventions (normalization, axes, ICC, permutation).
- `docs/api_reference.md` - every public function's signature and parameters.
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
  coordinates, and the subsampling fix changed M3's results. `02_plots.ipynb`
  also has stale pre-wrapping output (cell 18 stores all 21 CTR panels in one
  6729px-wide row).
- [x] Work through `docs/ssvep_analyses.md` proposals 2, 3, 4, 5, 7 -- see
  **Next milestones** below for the decided scope and order.

Cleanup:

- [ ] Small correctness and consistency items (2.7): permutation p-value `+1`
  correction, `zscore` `ddof`, `plotting` -> `reliability` import chain,
  `load_grid_axes` caching, inconsistent `normalize` defaults.
- [ ] Factor the repeated subject/category resolution in `plotting.py` (2.8).
- [ ] Repo hygiene (2.9): remove `Untitled Folder/`, decide on notebook
  outputs, make the notebook import path robust.

## Done since the review

- [x] **Trough surface fit replaced** (2.4) with `fit_ramp_gaussian` (linear
  ramp + bounded Gaussian dip), now the default. Converges on 62/62 rows and
  adds `fitted_amp`/`fitted_sigma_red`/`fitted_sigma_green`. Also added
  `fitted_at_bound`, which surfaced that most CVD subjects' troughs lie beyond
  the sampled red range -- see `docs/ssvep_analyses.md` section 2.
- [x] **`docs/ssvep_analyses.md`** -- seven proposed analyses with the
  supporting measurements.
- [x] **Red/green axis naming fixed at the source** (2.1). `loader.to_rows`
  reads `runMap[green_idx, red_idx, run]`; `_plot_heatmap` displays `grid.T`.
  Every heatmap verified pixel-identical before/after; HC's trough now reads
  red 2133 / green 889, matching the reference image.
- [x] **Test suite added** (2.2). `uv run pytest ssveps/tests -q`, 14 tests,
  mutation-checked against the axis bug.
- [x] **Permutation no longer discards subjects** (2.3). `n1`/`n2` default to
  the full group sizes; they remain parameters for reproducing the templates.
- [x] **Both build scripts unified** (2.5) onto `loader.write_derived_csv` --
  verified byte-identical output. Fixed two problems found while verifying: a
  dtype quirk that silently disabled the float formatting on a first run, and
  389 committed values that were 1 ULP off the raw data (now regenerated; no
  scientific change).
- [x] **`ssveps/README.md` rewritten** to cover M2-M5, and `methods.md`'s
  permutation section corrected (2.6).
- [x] **`04_distributions.ipynb`: raw baseline comparison across groups**
  (`plot_groups_baseline_boxplot`, `analysis.pooled_baseline_values`) --
  addresses proposal 6's flag that PD's baseline is itself lower than CTR's,
  by making it directly visible rather than inferred from normalized numbers.

## Next milestones (M6-M10): proposed analyses

We are implementing proposals 2, 3, 4, 5, and 7 from `docs/ssvep_analyses.md`,
in that order. Proposal 6 (normalization choice) is settled, not a milestone --
see the convention below. Proposal 1 (power) is context, not an analysis to
run.

**Governing goal.** The strongest, best-powered effect in the dataset is
CVD vs HC. The question we actually want the test to answer is bifold:
(1) does this person have a CVD, and (2) if so, which type -- deutan or
protan. Proposal 2 (the CVD-gamut / at-bound finding) is the primary lever
for both halves, so it leads.

**Normalization convention (from proposal 6, already decided):** percent
change is the primary outcome measure; db is reported as a sensitivity check
(it's a monotone transform of the same ratio, so agreement is a consistency
check, not independent evidence); z-score is not used for cross-group
comparisons since it conflates baseline stability with response amplitude.
Carry this into `methods.md` when M6-M10 land.

- [x] **M6 - Proposal 2: CVD gamut as a diagnostic.** `08_cvd_gamut.ipynb`.
  - [x] Report `fitted_at_bound` sensitivity/specificity (0.73/0.81) with a
    subject-level bootstrap CI: sensitivity [0.47, 0.93], specificity
    [0.62, 0.95] (95%, n=2000). Fisher exact CVD-vs-CTR odds ratio 11.7,
    p=0.0019, confirmed against the earlier point estimate.
  - [x] `analysis.fit_ramp` (ramp only, no dip) added; `ramp_slope_red` is now
    persisted in `subject_troughs.csv` for every subject-session, so all 15
    CVD subjects have it, pegged or not.
  - [x] `analysis.extrapolate_ramp_crossing` + a run-level bootstrap CI
    (`analysis.bootstrap_ci`, `analysis.run_grids`), targeted against each
    subgroup's own `fitted_valid` median depth/green rather than the pegged
    subject's own fit. Explicitly flagged as unstable per-subject (some CIs
    span tens of thousands of red units, two point estimates are even
    negative) -- kept as group-level qualitative support only, not a
    per-subject measure to compare on.
  - [x] Protan vs. deutan on `ramp_slope_red`: Welch p=0.44, Mann-Whitney
    p=0.69, Cohen's d=0.41 (n=8 vs 7) -- same order of magnitude as the
    PD-vs-CTR effect proposal 1 already flagged as underpowered. **Not
    significant with current sample sizes** -- the subtype question proposal
    2 set up doesn't have an answer yet, but the measure to answer it with
    (`ramp_slope_red`) now exists and is reusable.
  - [x] Recommendation written into the notebook and `docs/methods.md`:
    extend the red stimulus axis -- this is what would turn section 4's
    suggestive-but-not-significant result into a real one.
- [x] **M7 - Proposal 3: variance decomposition (within vs. between subject).**
  `09_variance_components.ipynb`, `variance.py`. Fit a random-intercept
  MixedLM **per group** (not one pooled model with `vc_formula` -- see
  `docs/methods.md` for why) plus a subject-level bootstrap CI, replacing the
  point-estimate SD split.
  - [x] Within-subject SD: PD (0.104) not elevated vs. CTR (0.142) -- confirms
    the earlier point estimate on a proper footing.
  - [x] Between-subject SD with 95% bootstrap CI (n_boot=2000): CTR 0.282
    [0.19, 0.35], PD 0.414 [0.12, 0.56] (wide, overlaps CTR -- not
    established as more variable, confirms proposal 3), protan 0.194 [0.10,
    0.23] (overlaps CTR), deutan 0.091 [0.00, 0.13] (**does not** overlap
    CTR -- lower, not higher). The deutan result is new and unexpected --
    opposite direction from "condition increases heterogeneity" -- flagged
    as a real finding to revisit with more data, not explained away.
  - [x] Within-subject CV (scale-corrected): roughly flat across groups
    (CTR 0.19, PD 0.17, protan 0.21, deutan 0.23) -- confirms it's not
    response-size scaling driving the within-subject picture.
  - [x] Covariates note written into `docs/methods.md`/the notebook: PD
    severity/duration/medication state, CVD severity score -- none currently
    in the dataset, highest-value addition if this line is worth pursuing.
- [x] **M8 - Proposal 4: gain vs. shape decomposition.** `10_gain_shape.ipynb`.
  - [x] Per-subject `fit_gain_shape`: `grid ~= gain*CTR_template + intercept`
    over all 100 cells, for every subject at session 1.
  - [x] `trough_region_residual` at the *template's* own trough (not each
    subject's own -- the point, for subjects whose own trough couldn't be
    located): PD and deutan residuals indistinguishable from zero (p=0.56,
    p=0.63); **protan's is not** (mean -0.10, p=0.030, n=8, one test,
    uncorrected) -- a genuine trough-specific effect beyond gain. Connects to
    M6: protan had the shallowest `ramp_slope_red`, i.e. the trough sitting
    furthest beyond the sampled range on average.
  - [x] Cross-check: `gain` vs. `ramp_intercept` (M6) r=0.87, p<1e-13 -- two
    independent gain proxies agree well. `trough_region_residual` vs.
    `fitted_amp` (M4/M6) r=0.04, p=0.79 -- genuinely don't agree, because
    they measure different things (template-centered vs. subject-centered);
    not a bug, written up as such in `docs/methods.md`.
- [ ] **M9 - Proposal 5: reliability-first outcome selection.**
  - [ ] Extend the `reliability.py` ICC machinery from per-pixel maps to the
    per-subject features (`depth`, `fitted_green`, `fitted_amp`, `fitted_red`)
    and report ICC with CIs for each.
  - [ ] Compute the minimum detectable effect at actual n for each candidate
    feature.
  - [ ] Confirm `depth` (r=0.78 test-retest) as the primary outcome and
    `fitted_red` as unreliable; record the decision in `methods.md`.
- [ ] **M10 - Proposal 7: joint (PCA) treatment of the 100-cell grid.**
  - [ ] PCA across subjects on the 100-cell vectors, regularized given
    n=42 subjects vs. 100 features.
  - [ ] Interpret the first few components (expected: gain, trough depth,
    trough position as separate axes).
  - [ ] Group-compare component scores instead of cell-wise tests.
  - [ ] Treat this as preparation for a larger sample -- it improves SNR over
    cell-wise testing but does not rescue power at n=6 for PD.
