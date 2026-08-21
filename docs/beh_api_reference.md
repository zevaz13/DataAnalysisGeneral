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
