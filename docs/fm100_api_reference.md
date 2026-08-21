# FM100 scripts and notebooks: reference

Everything lives in `standardizedScores/FM100/scripts/`. Notebooks
(`standardizedScores/FM100/notebooks/`) call these directly after
`sys.path.append('../scripts')`. See `standardizedScores/FM100/README.md`
for the data dictionary and rationale (raw-file quirks, MET047/MET021
handling, the module-naming collision with `beh/`'s and `ssveps/`'s
scripts). Function reference below; jump to "Notebooks" at the end for what
each notebook demonstrates.

## `loader.py` -- data access

- **`load_fm100_raw(path=RAW_PATH, *, ssvep_metadata_path=SSVEP_METADATA_PATH) -> DataFrame`**
  The tidy table: `sub_id, session, group, subgroup, sex, date, caps`.
  `path` defaults to `/home/sebas/data/standardizedScores/repeatedSessionsPY.txt`
  (read in place). `caps` is a length-85 int array (cap IDs in placement
  order). `group`/`subgroup` looked up by `sub_id` from
  `ssvep_metadata_path` (default `ssveps/files/metadata.csv`); a subject
  absent from that file gets `group='UNKNOWN'`, `subgroup='NA'`.
- **`subjects_in_group(df, *, group=None, subgroup=None) -> list[str]`**
  Subject IDs matching `group`/`subgroup` (mirrors `beh`'s/`ssveps`'s
  function of the same name).

## `scores.py` -- FM100 scoring

A refactor of `templateCode/FM100.py`'s math (not a rewrite) -- every
function's output is pinned against the original template on all 69 real
rows in `tests/test_fm100.py`, bit-for-bit. TES, PES, and the tray scores
all derive from the same per-cap circular error (`err_vals`), computed once
and shared, rather than recomputed per metric as the template did.

- **`err_vals(caps) -> ndarray`**
  Per-cap circular hue error (length 85): `dist(prev, curr) + dist(next,
  curr) - 2`, wrapping around the full 85-cap circle. 0 for a perfectly
  ordered neighborhood.
- **`tes(caps) -> dict`**
  `{TES, SqrtTES}` -- Total Error Score (`err_vals.sum()`) and its square
  root.
- **`pes(caps) -> dict`**
  `{PES_RG, PES_BY, PES_RG_sqrt, PES_BY_sqrt}` -- `err_vals` summed over
  the red-green vs. blue-yellow axis cap subsets. The index groups are
  transcribed verbatim from the template, not re-derived.
- **`tes_trays(caps) -> dict`**
  `{TES_tray (length-4 array), TES_tray_sqrt, TES_whole, TES_whole_sqrt}` --
  TES computed separately within each of the 4 22-cap trays, using that
  tray's own local wrap boundaries (distinct from `err_vals`'s whole-circle
  wrap).
- **`vks(caps) -> dict`**
  `{VKS_Angle, VKS_MajRad, VKS_MinRad, VKS_TotErr, VKS_Sindex, VKS_Cindex}` --
  Vingrys-King-Smith confusion-ellipse metrics (fitted ellipse angle,
  major/minor radii, total error, elongation/selectivity index, and
  confusion index relative to a normative subject). Raises `ValueError` if
  `caps` isn't a permutation of 1..85.
- **`score_row(caps) -> dict`**
  `tes`/`pes`/`tes_trays` (flattened to `TES_tray1`..`TES_tray4`)/`vks`
  merged into one flat dict.
- **`build_scores(df) -> DataFrame`**
  `score_row` for every row of a `loader.load_fm100_raw` table, joined with
  `sub_id, session, group, subgroup`. Computed live, not persisted.

## `plotting.py` -- linear and radial error-profile plots

Both plot the per-cap error profile (`scores.err_vals`, possibly smoothed):
linear puts cap position (1-85) on x, error on y; radial wraps the same
profile onto a circle (angle=cap position, radius=error) -- the FM100 field's
standard polar diagram. `SESSION_COLORS` (first 3 categorical slots,
all-pairs validated) colors per-session overlays; `FULL_PALETTE` (all 8
slots, adjacent-pair validated) colors group lines, since a line chart only
needs the weaker adjacent-pair color guarantee, not the scatter-plot
all-pairs one.

- **`plot_subject_fm100(df, sub_id, *, kind='linear', sessions=None, window=1, ax=None) -> Axes`**
  One participant, one line per session (at most 3 in this dataset).
  `kind='linear'` or `'radial'`; `ax` must already be a polar axes for
  `'radial'` if passed explicitly (otherwise one is created for you).
- **`plot_group_fm100(df, categories, *, kind='linear', window=1, ax=None) -> Axes`**
  One mean line + shaded ±1 SD band per category. `categories` is the same
  `{"label", "group", "subgroup"}` shape used throughout this project, plus
  `"sub_ids"` for an explicit hand-picked list. Each *subject* contributes
  one profile (their own sessions averaged first) to the mean/SD, so
  multi-session subjects don't outweigh single-session ones. Up to
  `len(FULL_PALETTE)` (8) categories, no faceting needed (see module
  docstring).
- **`window=`** (both functions): circular moving-average size (1 = no
  smoothing) -- wraps around the hue circle rather than truncating at caps
  1/85, since they're real neighbors.

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- **`01_explore.ipynb`** -- M1: load and score every row
  (`scores.build_scores`); `MET047`/`MET021` looked at individually; group
  score table (`PES_RG` vs. `PES_BY` by group/subgroup -- protan/deutan
  show the classic red-green-dominant pattern, MET047 doesn't); linear and
  radial plots for one participant with the `window=` filter; group plots
  with ±1 SD shading for HC/PD/CVD/protan/deutan; a hand-picked `sub_ids`
  example grouping MET047 and MET021 together against protan/deutan.
