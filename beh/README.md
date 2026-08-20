# Behavioral (manual match) data

Manual/behavioral task data: for each of several sessions, a participant
clicks a (red, green) point that looks isoluminant to them -- the same
physical judgment the SSVEP grid experiment (`ssveps/`) probes
electrophysiologically, reported here directly instead.

Raw data: `/home/sebas/data/manualTest/behavioral_table.csv` (read in place,
not copied into the repo). Already tidy, one row per click -- no build step.
Conventions and rationale below; plan and milestone status in
`../PLANbeh.md`.

## Fields (raw `behavioral_table.csv`, as loaded by `loader.load_behavioral`)

Raw column -> tidy column, renamed for consistency with `ssveps/`'s naming:

- `SubID` -> `sub_id` -- subject id (`METxxx`), the same ids `ssveps/` uses.
- `Red`, `Green` -> `red`, `green` -- the clicked point. No axis limits are
  applied at load time; some subjects' `green` runs past 2000 (the SSVEP
  grid's own range) -- see `plotting.py`.
- `RunNumber` -> `click` -- numbers a session's clicks in raw-file order.
  Renamed from "run" deliberately: there is no grid repeat here like
  `ssveps/`'s "run" concept, just a sequence of individual point matches
  (~15-25 per session in this dataset).
- `session` -- 1, 2, or 3.
- `PartType` -> `group` -- 1=CTR (HC), 2=CVD, 3=PD, 4=HD. Confirmed to match
  `ssveps/files/metadata.csv`'s own `group` column exactly for every one of
  the 43 subjects present in both datasets (`beh/tests/test_beh.py`).
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

## `scripts/loader.py` -- data access

- **`load_behavioral(path=RAW_PATH, *, ssvep_metadata_path=SSVEP_METADATA_PATH) -> DataFrame`**
  The tidy table described above: `sub_id, session, click, red, green, group,
  subgroup, date, folder`.
- **`subjects_in_group(df, *, group=None, subgroup=None) -> list[str]`**
  Subject IDs matching group/subgroup (mirrors `ssveps/scripts/analysis.py`'s
  function of the same name). No session argument -- unlike `ssveps/`'s
  grids, nothing here needs single-session filtering to avoid double-counting
  a subject; every session's rows are just more of that subject's own clicks.

## `scripts/plotting.py` -- scatter plots

Red is always x, green is always y (matching `ssveps/`). Default axis limits
are `XLIM=(0, 3200)`, `YLIM=(0, 2000)` -- the SSVEP grid's own range, for
visual comparability -- **not clipped**, some subjects' points fall outside
this window and are simply plotted against a fixed default; pass your own
`xlim=`/`ylim=` to see the full range. Multi-panel figures wrap to at most
`MAX_PANEL_COLS=5` panels per row.

Color: per-session overlays use the first 3 slots of the dataviz skill's
validated categorical palette (the only slots validated for an all-pairs/
scatter comparison, and this dataset never has more than 3 sessions).
Multi-subject/multi-group figures use one panel per subject/group (faceting)
with a single uniform point color instead -- identity comes from the panel
title, the same convention `ssveps/scripts/plotting.py` uses for its
boxplots, and it sidesteps the >3-category scatter-color problem entirely.

- **`plot_subject_session(df, sub_id, session, *, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  One subject, one session.
- **`plot_subject_sessions(df, sub_id, *, sessions=None, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  One subject, every session overlaid, one color per session (legend).
- **`plot_subject_cloud(df, sub_id, *, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  One subject, every session pooled into one color.
- **`plot_subjects_grid(df, *, sub_ids=None, group=None, subgroup=None, xlim=XLIM, ylim=YLIM) -> Figure`**
  One panel per subject (that subject's whole point cloud). Pass `sub_ids`
  for an arbitrary hand-picked set of subjects instead of a group/subgroup
  filter.
- **`plot_subjects_pooled(df, *, sub_ids=None, group=None, subgroup=None, xlim=XLIM, ylim=YLIM, ax=None) -> Axes`**
  Every click from every matching subject, pooled onto one panel. Same
  `sub_ids` vs. `group`/`subgroup` choice as `plot_subjects_grid`.
- **`plot_groups_side_by_side(df, categories, *, xlim=XLIM, ylim=YLIM) -> Figure`**
  One panel per category (`{"label", "group", "subgroup"}` dicts, same shape
  as `ssveps/scripts/plotting.py`'s function of the same name), each showing
  that category's pooled cloud.

## `scripts/comparisons.py` -- Hotelling T² group comparisons

Uses the [`hotelling`](https://github.com/dionresearch/hotelling) PyPI
package (Hotelling 1931; pooled-covariance two-sample test, unequal n
supported) rather than a hand-rolled implementation. **This is not a port of
`templateCode/Hot_Tsqd_2samplesPaired.m`** -- that MATLAB function is the
*paired* one-sample-on-differences test (equal-length, row-matched x/y, e.g.
the same subjects' session 1 vs session 2). The group-vs-group comparisons
this project needs (HC vs PD, HC vs CVD, HC vs protan, HC vs deutan, protan
vs deutan) are between different, unequal-sized groups of different subjects
-- an unpaired two-sample test, which is what `hotelling.stats.hotelling_t2(x,
y)` (two arguments) implements. If a paired within-subject comparison is
wanted later (e.g. session 1 vs session 2 test-retest, mirroring
`ssveps/`'s M5/M9), the same package's one-sample path
(`hotelling_t2(x)`, one argument) covers it -- pass it
`session1_points - session2_points`.

- **`group_points(df, *, group=None, subgroup=None, unit='subject') -> ndarray`**
  `(red, green)` observations for one group/subgroup, shaped for
  `hotelling_t2`. `unit='subject'` (default): one row per subject, that
  subject's own mean across every click they have -- the statistically
  independent unit. `unit='point'`: every click from every subject, pooled
  -- pseudoreplicated (correlated clicks treated as independent; p-values
  from this are not to be trusted), but the only way to see a group's actual
  point-cloud *shape* rather than just its central tendency, which matters
  specifically for protan/deutan (n=7-8 subjects -- too sparse at the
  subject level to show shape at all).
- **`compare_groups(df, *, group1=None, subgroup1=None, group2=None, subgroup2=None, unit='subject') -> dict`**
  `group_points` for both sides, then `hotelling_t2`. Returns `{t2_stat,
  f_stat, p_value, pooled_cov, n1, n2, unit}`.

## Tests

`uv run pytest beh/tests -q`. Note: `beh/scripts/` and `ssveps/scripts/` both
have a `loader.py` and a `plotting.py` (independently, by convention, not by
design) -- if both test suites are collected in one pytest session (e.g. a
bare `pytest` at the repo root), each test file defensively drops any
already-cached `loader`/`plotting` module from `sys.modules` before
importing its own, so collection order can't leak the wrong project's module
into the other's tests. Notebooks never hit this: each runs in its own
kernel process, so `sys.path.append('../scripts')` + `import loader` is
unambiguous there regardless of what any other notebook does.

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- **`01_explore.ipynb`** -- M1: single-subject/single-session,
  multi-session (colored), and pooled-cloud scatter plots; group/subgroup
  grid and pooled plots, and an arbitrary hand-picked subject selection;
  groups side by side (HC/PD/CVD/protan/deutan); an "Understanding..."
  section on Hotelling T² and the `unit=` choice; and the five group
  comparisons PLANbeh.md M1 asks for, at both `unit='subject'` (the
  trustworthy significance numbers) and `unit='point'` (shown explicitly
  alongside, to make the pseudoreplication effect visible rather than
  theoretical). *Edit:* the `some_subjects` list (arbitrary-selection
  section) and `comparison_specs` (the five comparisons) to look at
  different subjects/groups.
