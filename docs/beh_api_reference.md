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
