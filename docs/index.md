# Where to find what

A map of this repo: every project, what its data is, and which document
answers which question. Start with `docs/findings.md` if you want the
results; start here if you want to know where something lives.

## How the docs relate

- **`docs/findings.md`** -- the results narrative, one section per project,
  in plain language with numbers and figures. Read this first for "what did
  we learn."
- **`PLAN<project>.md`** (repo root, one per project) -- the working task
  list: milestones, checkboxes, and a short writeup of each notebook's
  result as it landed. The most current single source for "what did notebook
  N actually find," often more detailed than `findings.md`'s summarized
  version.
- **`<project>/README.md`** -- data dictionary (raw file location, fields,
  quirks) and implementation decisions (bugs found and fixed, naming
  choices, cross-project gotchas). Read this before writing new code
  against a project's data.
- **`docs/<project>_api_reference.md`** -- every function's signature and
  parameters, one doc per project.
- A few projects also have a deeper standalone doc for material too long for
  `findings.md` or a README: `docs/methods.md` (SSVEP analysis conventions --
  normalization, axes, ICC, permutation), `docs/ssvep_analyses.md` (the
  seven proposed SSVEP analyses, M6-M10's source spec), `docs/ssvep_summary.md`
  (SSVEP work-to-date + a dated M1-M5 code review), `docs/ssvepbeh_reliability_gaps.md`
  (why the behavioral/EEG individual-differences correlation didn't survive
  correction, and what would fix it), `docs/experiment_summary.md` (shared
  experimental context: the stimulus, the metamer concept, why these
  particular measures), `docs/ExperimentalContext` (raw researcher notes the
  above was distilled from).

## Projects

Raw data always lives outside the repo (paths below); derived/tidy data, if
any, lives in the project's own `files/`.

### `standardizedScores/FM100/` -- FM100 hue test (clinical reference)
Raw: `/home/sebas/data/standardizedScores/repeatedSessionsPY.txt`. Docs:
`README.md`, `../../PLANScores.md`, `docs/fm100_api_reference.md`,
`docs/findings.md` section 1.

| Notebook | What it does |
|---|---|
| `01_explore.ipynb` | Load, score, verify against the original MATLAB template; radial/linear plots |
| `02_group_comparisons.ipynb` | Per-feature group comparisons (HC/protan/deutan/PD) |
| `03_flagged_subjects.ipynb` | MET020/MET047/MET021 close-up |
| `04_hc_vs_pd.ipynb` | HC vs PD profile comparison and DC-offset model |
| `05_outlier_flagging.ipynb` | Per-feature outlier boxplots (all groups) and offset re-run without CTR outliers |

### `beh/` -- behavioral (manual match) task
Raw: `/home/sebas/data/manualTest/behavioral_table.csv`. Docs: `README.md`,
`../PLANbeh.md`, `docs/beh_api_reference.md`, `docs/findings.md` section 2.

| Notebook | What it does |
|---|---|
| `01_explore.ipynb` | Load; per-subject/group plots; M1 centroid comparisons |
| `02_shape_features.ipynb` | PCA shape features (`orientation_deg`, `along_var`, `perp_var`) and comparisons |
| `03_centroids.ipynb` | Centroid plots, per-subject and per-group |
| `04_reliability.ipynb` | Session-to-session ICC/circular-r, HC and PD |
| `05_hc_vs_pd.ipynb` | HC vs PD point clouds, Hotelling T², within-session scatter |
| `06_outlier_rejection.ipynb` | Ellipse-based outlier detection, per-subject and per-group |

### `ssveps/` -- SSVEP (EEG) grid task
Raw: `/home/sebas/data/ssveps/` (62 `.mat` files, 43 subjects). Docs:
`README.md`, `../PLANssveps.md`, `docs/methods.md`, `docs/api_reference.md`,
`docs/ssvep_analyses.md`, `docs/ssvep_summary.md`, `docs/findings.md`
section 3.

| Notebook | What it does |
|---|---|
| `01_explore.ipynb` | Load and inspect fields |
| `02_plots.ipynb` | Raw grid maps for one subject |
| `03_group_comparisons.ipynb` | Groups, all normalization methods |
| `04_distributions.ipynb` | Pixel-level distributions, baseline comparison |
| `05_permutation_testing.ipynb` | M3: cluster-based permutation testing |
| `06_trough_surface_fit.ipynb` | M4: parametric surface fit for trough localization |
| `07_test_retest_reliability.ipynb` | M5: session 1 vs. session 2 reliability |
| `08_cvd_gamut.ipynb` | M6: CVD-vs-HC diagnostic via `fitted_at_bound` |
| `09_variance_components.ipynb` | M7: within- vs. between-subject variance |
| `10_gain_shape.ipynb` | M8: gain vs. shape decomposition |
| `11_reliability_outcomes.ipynb` | M9: reliability-first outcome selection |
| `12_pca.ipynb` | M10: joint PCA treatment of the full grid |
| `13_hc_vs_pd.ipynb` | M11: HC vs PD on `ramp_slope_red` |
| `14_hc_vs_subtypes.ipynb` | M11: HC vs protan vs deutan, pairwise |
| `15_permutation_stability.ipynb` | M11: protan vs deutan, 200-seed cluster-test stability (the localized subtype signal) |
| `16_grid_shape_features.ipynb` | M11: rotated (tilted) dip model, protan/deutan shape comparison |

### `ssvepBeh/` -- behavioral vs. EEG spatial agreement
No raw data of its own (reuses `beh/` and `ssveps/`). Docs: `README.md`,
`../PLANssvepvsBeh.md`, `docs/ssvepbeh_api_reference.md`,
`docs/ssvepbeh_reliability_gaps.md`, `docs/findings.md` section 4.

| Notebook | What it does |
|---|---|
| `01_explore.ipynb` | M1: spatial overlap tests (clicks vs. EEG low-response region) |
| `02_reliability.ipynb` | Multiple-comparisons correction + cross-session reliability |
| `03_clicks_on_grid.ipynb` | M2: EEG heatmap with clicks overlaid, per subject/group |
| `04_permutation_stability.ipynb` | M2: 200-seed stability of the overlap test |
| `05_toroidal_shift_explained.ipynb` | M2: from-scratch walkthrough of the toroidal-shift null model |

### `ssvep_beh_fm100/` -- FM100 vs. behavioral, and vs. EEG
No raw data of its own (reuses `standardizedScores/FM100/` and `beh/`).
Docs: `README.md`, `../PLANssvep_bh_fm100.md`,
`docs/ssvep_beh_fm100_api_reference.md`, `docs/findings.md` section 5.

| Notebook | What it does |
|---|---|
| `01_fm100_reliability.ipynb` | M1: FM100's own cross-session reliability |
| `02_fm100_vs_behavioral.ipynb` | M1: severity (CCA) and type/axis (circular correlation) vs. clicks |
| `03_eeg_reliability.ipynb` | M2: same reliability check, EEG features |
| `04_fm100_vs_eeg.ipynb` | M2: severity and type/axis vs. EEG |
| `05_three_way_type_axis.ipynb` | M3: clicks-vs-EEG directly, then joint three-way concordance |

### `dashboard/` -- Streamlit presentation layer
No analysis logic of its own -- every page imports the corresponding
project's `loader`/`plotting`/`comparisons` functions directly. Docs:
`README.md`, `../PLANdashboard.md`. Run: `uv run streamlit run dashboard/Home.py`.

| File | What it does |
|---|---|
| `Home.py` | Landing page |
| `pages/1_FM100.py` | FM100 group/subgroup selector + headline plots |
| `pages/2_Behavioral.py` | Behavioral equivalent |
| `pages/3_SSVEP.py` | SSVEP equivalent |
| `_pagesetup.py` | Cross-project import helper (`use_scripts`) |

### `cappuccino_index/` -- unrelated toy dataset
Crowd-sourced cappuccino-affordability data, kept separate from the
color-vision line of work above. Raw:
`/home/sebas/data/capuccinoIndex/Cappuccino Index 2026 (public).xlsx`. Docs:
`README.md`, `../PLANCappIndex.md`.

| Notebook | What it does |
|---|---|
| `01_explore.ipynb` | Load and inspect the three sheets |
| `02_basic_plotting.ipynb` | Cappuccino index by country |

## Root-level files

- `README.md` -- environment setup (`uv`), repo-wide conventions.
- `PLAN*.md` -- one plan per project (see table above for which goes with
  which); `PLANdashboard.md` and `PLANCappIndex.md` cover the two
  non-analysis-narrative projects.
- `docs/make_figures.py` -- regenerates every figure embedded in
  `docs/findings.md` and `docs/experiment_summary.md` straight from raw
  data (`uv run python docs/make_figures.py`).
