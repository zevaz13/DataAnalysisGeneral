# Behavioral (manual match) scripts and notebooks: reference

Everything lives in `beh/scripts/`. Notebooks (`beh/notebooks/`) call these
directly after `sys.path.append('../scripts')`. See `beh/README.md` for the
data dictionary and rationale behind the design decisions (subgroup lookup,
`unit=` parameter, the module-naming collision with `ssveps/scripts/` and how
it's handled). Function reference below; jump to "Notebooks" at the end for
what each notebook demonstrates.

## `loader.py` -- data access

- **`load_behavioral(path: str = RAW_PATH, *, ssvep_metadata_path: str = SSVEP_METADATA_PATH) -> DataFrame`**
  The tidy behavioral table: `sub_id, session, click, red, green, group,
  subgroup, date, folder`. `path` defaults to
  `/home/sebas/data/manualTest/behavioral_table.csv` (read in place).
  `group` is derived from the raw file's `PartType` (1=CTR, 2=CVD, 3=PD,
  4=HD). `subgroup` (protan/deutan/NA) is looked up by `sub_id` from
  `ssvep_metadata_path` (default `ssveps/files/metadata.csv`) at load time --
  a subject absent from that file gets `subgroup='NA'`.
- **`subjects_in_group(df: DataFrame, *, group: str | None = None, subgroup: str | None = None) -> list[str]`**
  Subject IDs matching `group`/`subgroup` (mirrors
  `ssveps/scripts/analysis.py`'s function of the same name). No session
  argument -- every session's rows are just more of that subject's own
  clicks, nothing here needs single-session filtering to avoid
  double-counting the way `ssveps/`'s grids do.

## `plotting.py` -- scatter plots

Red is always x, green is always y. Default axis limits `XLIM=(0, 3200)`,
`YLIM=(0, 2000)` (the SSVEP grid's own range, for visual comparability) --
**not clipped**; some subjects' points fall outside this window and are just
plotted against the fixed default, pass `xlim=`/`ylim=` to see the full
range. Multi-panel figures wrap to at most `MAX_PANEL_COLS=5` per row.
`POINT_COLOR` (single-series default) and `SESSION_COLORS` (the first 3
slots of the dataviz skill's validated categorical palette -- the only slots
validated for an all-pairs/scatter comparison, and this dataset never has
more than 3 sessions) are the two color constants; multi-subject/multi-group
figures use one color and one panel per subject/group instead of encoding
identity in hue -- see `beh/README.md`.

- **`plot_subject_session(df, sub_id, session, *, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  One subject, one session.
- **`plot_subject_sessions(df, sub_id, *, sessions=None, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  One subject, every session overlaid, one `SESSION_COLORS` entry per
  session, with a legend. `sessions` defaults to every session that subject
  has, in order.
- **`plot_subject_cloud(df, sub_id, *, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  One subject, every session pooled into one color -- the session dimension
  is dropped entirely, unlike `plot_subject_sessions`.
- **`plot_subjects_grid(df, *, sub_ids=None, group=None, subgroup=None, xlim=XLIM, ylim=YLIM) -> Figure`**
  One panel per subject (each subject's own `plot_subject_cloud`), wrapped at
  `MAX_PANEL_COLS`. Pass `sub_ids` for an arbitrary hand-picked set of
  subjects instead of a `group`/`subgroup` filter -- the same choice
  `plot_subjects_pooled` offers.
- **`plot_subjects_pooled(df, *, sub_ids=None, group=None, subgroup=None, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  Every click from every matching subject, pooled onto one panel and one
  color.
- **`plot_groups_side_by_side(df, categories, *, xlim=XLIM, ylim=YLIM) -> Figure`**
  One panel per category, each a `plot_subjects_pooled` call. `categories`
  is a list of `{"label", "group", "subgroup"}` dicts, the same shape as
  `ssveps/scripts/plotting.py`'s function of the same name.
- **`plot_feature_space(df, categories, *, x_feature='orientation_deg', y_feature='perp_var', ax=None) -> Axes`**
  M2: one subject-level point per category, in shape-feature space
  (`features.subject_shape_features`'s keys). `categories` is the same
  `{"label", "group", "subgroup"}` shape as `plot_groups_side_by_side`, but
  overlaid by hue on one panel (like `plot_subject_sessions`) rather than
  faceted -- capped at `len(SESSION_COLORS)` (3) categories, the dataviz
  skill's all-pairs scatter color limit; raises `ValueError` past that.

`plot_subject_cloud` and `plot_subjects_grid` additionally take
`show_fit: bool = False` (M2) -- overlays each subject's fitted PCA line
(`features.subject_pca_line`), in `FIT_LINE_COLOR` (secondary ink, since
it's a derived overlay, not a data series).

- **`plot_subject_outliers(df, sub_id, *, n_std=2.0, pca=None, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`** (M4)
  One subject's clicks, colored by whether they fall outside a fitted
  ellipse at `n_std` standard deviations along each principal axis
  (`OUTLIER_COLOR`, the same validated slot as `SESSION_COLORS[1]`, for
  outliers; `POINT_COLOR` for inliers), with the ellipse itself drawn
  (`FIT_LINE_COLOR`, dashed). `pca=None` (default): fit the ellipse to this
  subject's own points (the per-participant check). `pca=<a
  group_outliers result's "pca">`: classify this subject's points against
  a shared group/subgroup ellipse instead -- the group-level check.
- **`plot_subjects_outliers_grid(df, *, sub_ids=None, group=None, subgroup=None, n_std=2.0, shared_pca=None, xlim=XLIM, ylim=YLIM) -> Figure`** (M4)
  One panel per subject (`plot_subject_outliers`), wrapped to
  `MAX_PANEL_COLS`. `shared_pca=None`: each panel fits its own subject's
  ellipse. `shared_pca=<group_outliers(...)["pca"]>`: every panel draws
  the same shared ellipse, classifying each subject's own points against
  it -- one call serves both the per-participant and group-level checks.

- **`plot_subject_centroids(df, categories, *, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  M3: one point per subject, at that subject's own mean (red, green) --
  `comparisons.group_points(..., unit='subject')`'s points, plotted
  directly. Same `categories` shape and `len(SESSION_COLORS)` (3) cap as
  `plot_feature_space`, for the same all-pairs-scatter reason.
- **`plot_group_centroids(df, categories, *, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  M3: one marker per category, at the mean of its subjects' own (red, green)
  means, with ±1 SD error bars across those subject centroids. No category
  cap -- a handful of large, legended marks rather than a dense scatter,
  so identity is carried by `CENTROID_MARKERS` (shape) as well as color
  (`FULL_PALETTE`, the dataviz skill's full 8-hue order), not by hue alone.
- **`plot_feature_group_centroids(df, categories, *, x_feature='orientation_deg', y_feature='perp_var', ax=None) -> Axes`**
  M3: the shape-feature analog of `plot_group_centroids` -- one marker per
  category at the mean of its subjects' `x_feature`/`y_feature` values, same
  ±1 SD error bars, same no-cap/marker-shape treatment.

## `features.py` -- PCA shape features and per-feature comparisons (M2)

Complements `comparisons.py`: instead of comparing groups' (red, green)
*means*, this fits a PCA line to each subject's own pooled clicks and
compares groups on the shape of that fit.

- **`subject_shape_features(df, sub_id) -> dict`**
  PCA on one subject's pooled (red, green) clicks (every session). Returns
  `{orientation_deg, along_var, perp_var, n}` -- `orientation_deg` is the
  first principal component's angle, folded into `[0, 180)` since a line has
  no direction; `along_var` is the along-line spread (PC1 variance);
  `perp_var` is the off-line scatter (PC2 variance, i.e. match consistency).
  Raises `ValueError` if the subject has fewer than 2 points.
- **`subject_pca_line(df, sub_id) -> (ndarray, ndarray)`**
  The two endpoints of the fitted PCA line, spanning that subject's actual
  data extent along PC1 -- for `plotting.py`'s `show_fit` overlay.
- **`group_features(df, *, group=None, subgroup=None) -> DataFrame`**
  `subject_shape_features` for every subject in a group/subgroup, one row
  per subject (indexed by `sub_id`).
- **`compare_shape_feature(df, feature, *, group1=None, subgroup1=None, group2=None, subgroup2=None) -> dict`**
  Mann-Whitney U test + effect size (`pingouin.mwu`) on one feature between
  two groups/subgroups. `feature` is one of `subject_shape_features`'s keys.
  Returns `{feature, u_val, p_value, rbc, cles, n1, n2}` -- `rbc` (rank-
  biserial correlation) and `cles` (common language effect size) come
  straight from pingouin. Chosen over a multivariate test (e.g. 3D Hotelling
  T²) because it's per-feature (shows which shape property drives a
  difference) and doesn't assume the small protan/deutan samples are
  Gaussian. Note: orientation comparisons assume a group's angles don't
  straddle the 0/180 wrap point -- true for this dataset (see `features.py`
  module docstring) but not a general circular-safe statistic.

### M4 additions: per-session features, click consistency, outlier ellipse

- **`subject_session_features(df) -> DataFrame`**
  `subject_shape_features` plus centroid, computed **per (sub_id, session)**
  rather than pooled across a subject's sessions like `subject_shape_features`/
  `group_features` (M2) do. One row per (sub_id, session) with `>= 2` clicks:
  `sub_id, session, centroid_red, centroid_green, orientation_deg, along_var,
  perp_var, n`. What `retest.py`'s reliability check needs -- a reliability
  check is meaningless on features already pooled across the sessions being
  compared.
- **`within_session_scatter(df, sub_id) -> float`**
  A subject's average within-session click consistency: for each of their
  sessions, the RMS Euclidean distance of that session's clicks to that
  session's own centroid, averaged across sessions (each session weighted
  equally). Answers "how much does this subject's hand wander within one
  sitting" -- distinct from *where* they aim (location) or their overall
  click-cloud shape pooled across sessions (M2's features), and the reason
  it exists: PD's motor symptoms could plausibly inflate this without
  moving either of those (`05_hc_vs_pd.ipynb`).
- **`outlier_mask(pca, points, *, n_std=2.0) -> ndarray[bool]`**
  Which rows of `points` fall outside the ellipse at `n_std` standard
  deviations along each of `pca`'s principal axes (`pca` is a
  `_points_pca`/`_subject_pca`-shaped dict: `mean`, `pc1`, `along_var`,
  `perp_var`). `pca` and `points` need not come from the same subject/group
  -- `group_outliers` applies one shared group-level `pca` to each
  individual subject's own `points`.
- **`subject_outliers(df, sub_id, *, n_std=2.0) -> dict`**
  One subject's own points classified against their own fitted ellipse.
  Returns `{pca, points, outlier_mask}`.
- **`group_outliers(df, *, group=None, subgroup=None, n_std=2.0) -> dict`**
  One ellipse fit to a whole group/subgroup's pooled clicks, then applied
  back to each individual subject's own points -- "does this subject's data
  look like an outlier relative to the group as a whole", not relative to
  their own cloud. Returns `{pca, table}`: `pca` is the group-level fit (for
  drawing the shared ellipse); `table` has one row per click (`sub_id, red,
  green, is_outlier`) across every subject in the group, groupable by
  `sub_id` to see how many of a given subject's points were flagged.

## `retest.py` -- cross-session feature reliability (M4)

Deliberately not named `reliability.py` -- `ssveps/scripts/` already has
one, and this module needs to import that one under the same bare name it
would otherwise claim for itself (a genuine self-collision, not the usual
cross-project one; see the module docstring). Mirrors
`ssvep_beh_fm100/scripts/fm100_features.py`'s `paired_sessions`/
`reliability_table` structure closely, reusing `ssveps/scripts/reliability.py`'s
`feature_icc` directly rather than reimplementing ICC.

`MAGNITUDE_FEATURES = ["centroid_red", "centroid_green", "along_var", "perp_var"]`,
`ANGLE_FEATURE = "orientation_deg"` (periodic, folds to `[0, 180)` -- checked
with `pingouin.circ_corrcc` after `circ_axial` folding, not a linear ICC,
same split `fm100_features.py` makes for `VKS_Angle`).

- **`paired_subjects(df, *, group=None, subgroup=None, sessions=(1, 2)) -> list[str]`**
  Subject IDs present at both of `sessions` (default session 1 and session
  2, not "any 2 sessions" -- keeps results comparable across subjects with
  a differing total session count, same convention
  `ssveps/scripts/reliability.py`'s own `paired_subjects` uses), optionally
  filtered by group/subgroup.
- **`paired_sessions(df, *, group=None, subgroup=None, sessions=(1, 2)) -> DataFrame`**
  Centroid/shape features for `paired_subjects`, one row per subject, each
  feature suffixed `_session{n}`. Raises `ValueError` below 3 qualifying
  subjects (`feature_icc`'s own minimum).
- **`reliability_table(df, *, group=None, subgroup=None, sessions=(1, 2)) -> DataFrame`**
  ICC(A,1) for the four `MAGNITUDE_FEATURES`, `circ_corrcc` for
  `orientation_deg`. Returns `feature, n, statistic ('icc'|'circ_r'), value,
  p_value` -- same shape as `fm100_features.reliability_table`, so
  `ssvep_beh_fm100/scripts/plotting.py`'s `plot_reliability_table` is
  directly reusable on the result (`04_reliability.ipynb` does this).

## `comparisons.py` -- Hotelling T² group comparisons

Uses the [`hotelling`](https://github.com/dionresearch/hotelling) PyPI
package (Hotelling 1931; pooled-covariance two-sample test, unequal n
supported) rather than a hand-rolled implementation. **Not a port of**
`beh/templateCode/Hot_Tsqd_2samplesPaired.m` -- that MATLAB function is the
*paired* one-sample-on-differences test (equal-length, row-matched x/y,
e.g. the same subjects' session 1 vs session 2 -- a repeated-measures
design). The group-vs-group comparisons this project needs are between
different, unequal-sized groups of different subjects -- an unpaired
two-sample test, which `hotelling.stats.hotelling_t2(x, y)` (two arguments)
implements. A paired within-subject comparison, if wanted later (mirroring
`ssveps/`'s M5/M9 test-retest work), is the same package's one-sample path
(`hotelling_t2(x)`, one argument) called on `session1_points -
session2_points`.

- **`group_points(df, *, group=None, subgroup=None, unit='subject') -> ndarray`**
  `(red, green)` observations for one group/subgroup, shaped `(n, 2)` for
  `hotelling_t2`.
  - `unit='subject'` (default): one row per subject -- that subject's own
    mean across every click they have. The statistically independent unit
    (clicks from one subject aren't independent of each other); what
    `compare_groups` uses by default and what every reported p-value in
    `01_explore.ipynb` uses.
  - `unit='point'`: every click from every subject, pooled.
    Pseudoreplicated -- correlated clicks treated as independent, so
    p-values from this are not to be trusted at face value -- but the only
    way to see a group's actual point-cloud *shape* rather than just its
    central tendency. Needed specifically for protan/deutan: at n=7-8
    subjects there aren't enough subject-means to show a distribution's
    shape at all, while each contributes 20+ clicks that do.
- **`compare_groups(df, *, group1=None, subgroup1=None, group2=None, subgroup2=None, unit='subject') -> dict`**
  `group_points` for both sides, then `hotelling_t2`. Returns `{t2_stat,
  f_stat, p_value, pooled_cov, n1, n2, unit}`.

  **How to use this differently:**
  - *Compare two subgroups instead of two top-level groups* -- pass
    `subgroup1`/`subgroup2` (e.g. `group1='CVD', subgroup1='protan',
    group2='CVD', subgroup2='deutan'`); `group1`/`group2` narrow the pool
    `subgroup1`/`subgroup2` filters within, same as
    `loader.subjects_in_group`.
  - *See the pseudoreplication effect directly* -- call twice, once per
    `unit`, on the same comparison; the `unit='point'` p-value will be many
    orders of magnitude smaller for the same underlying groups, which is the
    inflation to distrust, not a stronger finding (`01_explore.ipynb`'s
    "Understanding..." section walks through why).

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- **`01_explore.ipynb`** -- M1: single-subject/single-session,
  multi-session (colored), and pooled-cloud scatter plots; group/subgroup
  grid and pooled plots, and an arbitrary hand-picked subject selection;
  groups side by side (HC/PD/CVD/protan/deutan); an "Understanding..."
  section on Hotelling T² and the `unit=` choice; and the five group
  comparisons `PLANbeh.md` M1 asks for, at both `unit='subject'` (the
  trustworthy significance numbers) and `unit='point'` (shown explicitly
  alongside, to make the pseudoreplication effect visible rather than
  theoretical). All five are significant at the subject level, including
  protan vs. deutan (p=0.004, n=8 vs 7). *Edit:* the `some_subjects` list
  (arbitrary-selection section) and `comparison_specs` (the five
  comparisons) to look at different subjects/groups.
- **`02_shape_features.ipynb`** -- M2: fitted-line overlays
  (`plot_subjects_grid(..., show_fit=True)`) for the protan/deutan grids;
  a feature-space scatter (`plot_feature_space`); and the same five group
  comparisons as M1, run via `compare_shape_feature` on each of
  `orientation_deg`, `along_var`, `perp_var`. *Edit:* `comparison_specs`
  (shared with `01_explore.ipynb`'s list) to look at different group pairs.
- **`03_centroids.ipynb`** -- M3: `plot_subject_centroids` (HC/PD/CVD, then
  HC/protan/deutan) and `plot_group_centroids` (all 5 categories at once)
  in (red, green) space; the same two plot types in shape-feature space
  (`plot_feature_space`/`plot_feature_group_centroids`) for all three
  pairwise combinations of `orientation_deg`, `along_var`, `perp_var`.
  *Edit:* `top_level_categories`/`subtype_categories`/`all_categories` to
  look at different group sets.
- **`04_reliability.ipynb`** -- M4: `retest.reliability_table` for HC and
  PD (CVD excluded -- most subjects lack a second session), plotted via
  `ssvep_beh_fm100/scripts/plotting.py`'s `plot_reliability_table` (reused
  cross-project, no new chart code). HC is mostly not reliable
  session-to-session (only `centroid_green` clears significance, ICC=0.60,
  p=0.0013); PD (n=6) has nothing significant either, at a sample size too
  small to confirm its own suggestively high point estimates. *Edit:*
  `group=`/`subgroup=` on the `reliability_table` calls for a different
  category (will raise below 3 paired subjects).
- **`05_hc_vs_pd.ipynb`** -- M4: point clouds side by side, Hotelling T²
  (p=0.0001, matching M1's earlier number), all three `compare_shape_feature`
  tests (all significant for this pair), and `within_session_scatter`
  compared via `pingouin.mwu` -- PD is significantly less consistent within
  a single sitting (p=0.023, ~70% larger RMS scatter than HC), a specific
  answer to whether PD's motor symptoms show up as noisier clicking. *Edit:*
  `categories` (top cell) for a different pair -- note `within_session_scatter`'s
  motor-symptom framing is PD-specific, not a generic template for any pair.
- **`06_outlier_rejection.ipynb`** -- M4: `plotting.plot_subjects_outliers_grid`
  at `n_std=2.0`, per-subject (each panel its own ellipse) then group-level
  (`features.group_outliers`'s `pca` shared across every panel), for
  HC/PD/protan/deutan. Flagged fractions are similar and unremarkable
  across every group (10.5%-15.5% of clicks) -- exploratory, nothing here
  filters persisted data, and nothing turned up that argues for adding
  automatic rejection to the pipeline. *Edit:* `N_STD`, `categories` (top
  cell).
