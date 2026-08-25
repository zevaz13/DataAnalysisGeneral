# Behavioral (manual match) data

Manual/behavioral task data: for each of several sessions, a participant
clicks a (red, green) point that looks isoluminant to them -- the same
physical judgment the SSVEP grid experiment (`ssveps/`) probes
electrophysiologically, reported here directly instead.

Raw data: `/home/sebas/data/manualTest/behavioral_table.csv` (read in place,
not copied into the repo). Already tidy, one row per click -- no build step.
Function-by-function reference: `docs/beh_api_reference.md`. Plan and
milestone status: `../PLANbeh.md`.

## Fields (raw `behavioral_table.csv`, as loaded by `loader.load_behavioral`)

Raw column -> tidy column, renamed for consistency with `ssveps/`'s naming:

- `SubID` -> `sub_id` -- subject id (`METxxx`), the same ids `ssveps/` uses.
- `Red`, `Green` -> `red`, `green` -- the clicked point. No axis limits are
  applied at load time; some subjects' `green` runs past 2000 (the SSVEP
  grid's own range) -- see `scripts/plotting.py`.
- `RunNumber` -> `click` -- numbers a session's clicks in raw-file order.
  Renamed from "run" deliberately: there is no grid repeat here like
  `ssveps/`'s "run" concept, just a sequence of individual point matches
  (~15-25 per session in this dataset).
- `session` -- 1, 2, or 3.
- `PartType` -> `group` -- 1=CTR (HC), 2=CVD, 3=PD, 4=HD. Confirmed to match
  `ssveps/files/metadata.csv`'s own `group` column exactly for every one of
  the 43 subjects present in both datasets (`tests/test_beh.py`).
- `subgroup` -- **not in the raw file.** Looked up live from
  `ssveps/files/metadata.csv` by `sub_id` at load time (protan/deutan/NA),
  since these are the same participants who completed the SSVEP experiment
  and subgroup is genuinely shared data. A subject present here but absent
  from that file (tested behaviorally but not, or not yet, on SSVEP -- 4
  subjects in this dataset today: `MET013`, `MET014`, `MET041`, `MET042`)
  gets `subgroup='NA'`, matching `ssveps/`'s own convention for non-CVD
  subjects. Decided against persisting a merged copy under `beh/files/`: no
  build step to remember to rerun, always consistent with `ssveps/`'s own
  hand-corrected subgroup values.
- `Date`, `FolderOrg` -> `date`, `folder` -- carried through unchanged, not
  currently used by any analysis.

## Scripts

- `scripts/loader.py` -- `load_behavioral` (the tidy table above),
  `subjects_in_group` (mirrors `ssveps/scripts/analysis.py`'s function of
  the same name).
- `scripts/plotting.py` -- scatter plots. Red on x, green on y; default axis
  limits `(0, 3200)`/`(0, 2000)` (the SSVEP grid's own range, for visual
  comparability, not a data clip). Single subject/session, multi-session
  (colored), pooled-cloud, group/subgroup grid or pooled, arbitrary
  hand-picked subject selection, and groups side by side.
- `scripts/comparisons.py` -- Hotelling T² group comparisons via the
  [`hotelling`](https://github.com/dionresearch/hotelling) PyPI package
  (not a port of `templateCode/Hot_Tsqd_2samplesPaired.m` -- that's the
  *paired* one-sample test; the group comparisons here are unpaired
  two-sample). `unit='subject'` (default, statistically independent) vs.
  `unit='point'` (pooled clicks, pseudoreplicated but shows point-cloud
  shape) is a parameter, not a fixed choice -- see
  `docs/beh_api_reference.md`.
- `scripts/features.py` -- M2: per-subject shape features (PCA on each
  subject's pooled clicks -- line orientation, spread along it, scatter off
  it) and per-feature group comparisons (Mann-Whitney U + effect size, via
  `pingouin`), complementing `comparisons.py`'s mean-only Hotelling T².
- `scripts/plotting.py` also gained (M3) `plot_subject_centroids`/
  `plot_group_centroids` (each subject's, or each group's, own mean (red,
  green) as a single point) and `plot_feature_group_centroids` (the same for
  shape features) -- see below.
- `scripts/features.py` also gained (M4) `subject_session_features`
  (per-(sub_id, session), not pooled -- what a reliability check needs),
  `within_session_scatter` (a subject's own click consistency within a
  sitting), and the outlier-ellipse machinery: `outlier_mask`,
  `subject_outliers` (a subject's own fitted ellipse), `group_outliers`
  (one ellipse fit to a whole group/subgroup, applied back to every
  individual subject).
- `scripts/retest.py` -- M4: cross-session reliability (ICC(A,1) for
  centroid/`along_var`/`perp_var`, `pingouin.circ_corrcc` for the periodic
  `orientation_deg`), reusing `ssveps/scripts/reliability.py`'s
  `feature_icc` directly rather than reimplementing ICC. **Not named
  `reliability.py`** -- `ssveps/scripts/` already has one, and this file
  needs to import that one under the same bare name it would otherwise
  claim for itself (a genuine self-collision, not just the usual
  cross-project one -- see the module docstring).
- `scripts/plotting.py` also gained (M4) `plot_subject_outliers`/
  `plot_subjects_outliers_grid` -- the outlier-ellipse visualization, with
  an optional `shared_pca=`/`pca=` override so the same grid function
  renders both the per-subject and the group-level check (pass
  `group_outliers`'s `"pca"` to classify each subject's own points against
  a shared group ellipse instead of their own).

## Tests

`uv run pytest beh/tests -q`. Note: `beh/scripts/` and `ssveps/scripts/`
both have a `loader.py` and a `plotting.py` (independently, by convention,
not by design) -- if both test suites are collected in one pytest session
(e.g. a bare `pytest` at the repo root), each test file defensively drops
any already-cached `loader`/`plotting` module from `sys.modules` before
importing its own, so collection order can't leak the wrong project's
module into the other's tests. Notebooks never hit this: each runs in its
own kernel process, so `sys.path.append('../scripts')` + `import loader` is
unambiguous there regardless of what any other notebook does.

`scripts/retest.py` is deliberately not named `test_*.py`/`*_test.py` --
pytest's default discovery would otherwise try to collect it as a test
module in its own right (it lives under `scripts/`, not `tests/`, so
nothing currently scopes discovery away from it).

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- `01_explore.ipynb` -- M1: single-subject/single-session, multi-session
  (colored), and pooled-cloud scatter plots; group/subgroup grid and pooled
  plots, and an arbitrary hand-picked subject selection; groups side by side
  (HC/PD/CVD/protan/deutan); an "Understanding..." section on Hotelling T²
  and the `unit=` choice; and the five group comparisons `PLANbeh.md` M1
  asks for. All five are significant at the subject level, including protan
  vs. deutan (p=0.004, n=8 vs 7).
- `02_shape_features.ipynb` -- M2: PCA-derived shape features per subject
  (orientation, along-line spread, perpendicular tightness); fitted-line
  overlays and a feature-space scatter; the same five group comparisons as
  M1, run per feature instead of on the mean.
- `03_centroids.ipynb` -- M3: per-subject and per-group centroid plots, in
  both (red, green) space and shape-feature space (all three feature
  pairings).
- `04_reliability.ipynb` -- M4: cross-session ICC/circular-r for centroid
  and shape features, HC and PD only (CVD mostly lacks a second session).
  HC is mostly not reliable session-to-session (only `centroid_green`
  clears significance); PD (n=6) has no significant feature either, at a
  sample size too small to confirm the suggestively high `along_var`/
  `orientation_deg` point estimates.
- `05_hc_vs_pd.ipynb` -- M4: point clouds, Hotelling T², per-feature shape
  comparisons for HC vs PD (all significant), plus a PD-specific
  within-session click-consistency check -- PD is significantly less
  consistent within a single sitting (p=0.023, ~70% larger RMS scatter),
  a specific, confirmed answer to whether PD's motor symptoms show up as
  noisier clicking rather than (or in addition to) a shifted match point.
- `06_outlier_rejection.ipynb` -- M4: a fitted rotated ellipse (PCA) flags
  points beyond `n_std` (default 2.0) standard deviations, per-subject and
  group-level (one shared ellipse per group, applied to every individual).
  Nothing here filters persisted data -- exploratory, and nothing alarming
  turned up (flagged fractions are similar and unremarkable across every
  group).
