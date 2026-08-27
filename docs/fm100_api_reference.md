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
- **`label_mode=`** (both functions, M2): `'angle'` (default, matplotlib's
  own angle-in-degrees radial ticks) or `'cap'` -- relabels the radial
  plot's ticks with the FM100 test's own printed-diagram convention
  (`_apply_cap_labels`, `RADIAL_TICK_STEP=5`): the label sequence starts at
  cap 85 (not cap 1) at angle 0, then continues 1, 2, ... 84
  (`_cap_label(position_index) = ((position_index - 1) % 85) + 1`). One
  label every 5th cap (17 labels total). No-op for `kind='linear'`.
- **`show_cap_wheel=`** (both functions, plus `plot_group_vs_subjects_fm100`,
  M3): draws `fm100radialTemplate.png`'s outer ring instead --
  `_draw_cap_wheel` scatters all 85 caps just outside the plotted data,
  colored by `CAP_WHEEL_CMAP` (a cyclic colormap sampled by each cap's own
  angular position, approximating the physical hue circle the caps sit on)
  and individually numbered via `_cap_label`. No every-Nth-cap tradeoff to
  make, unlike `label_mode='cap'` -- takes priority over `label_mode` when
  both are set. No-op for `kind='linear'`.
- **`group_profiles(df, *, group=None, subgroup=None, sub_ids=None, window=1) -> ndarray`**
  (renamed from `_group_profiles`, now public) One smoothed error profile
  per subject matching the filter (`(n_subjects, 85)`), each subject's own
  sessions averaged together first. `plot_group_fm100`'s own internal
  building block, exposed so `comparisons.py`'s `estimate_offset` can
  bootstrap over the same per-subject profiles without recomputing them.
- **`plot_feature_boxplot(df, feature, categories, *, seed=0, ax=None) -> Axes`**
  (M3) One box per category (Tukey 1.5xIQR whiskers, `showfliers=False`),
  every subject's own value scattered on top with a small horizontal
  jitter and labeled with their id minus `MET`. Points
  `comparisons.tukey_outlier_mask` flags against their own category get a
  black edge and bold label instead of the default white edge/plain gray
  label. `categories` follows `plot_group_fm100`'s shape; up to
  `len(FULL_PALETTE)` (8).
- **`plot_feature_boxplots_grid(df, categories, *, features=comparisons.FEATURES, seed=0) -> Figure`**
  (M3) `plot_feature_boxplot`, one panel per feature in a 2-column grid.

## `comparisons.py` -- group comparisons and offset quantification (M2)

Deliberately self-contained -- doesn't import `ssvep_beh_fm100/`, even
though that project already has similar per-subject score-pooling logic,
to keep this base modality's dependencies one-directional (see the module
docstring).

`FEATURES = ["TES", "PES_RG", "PES_BY", "VKS_MajRad", "VKS_MinRad", "VKS_Angle"]`,
`ANGLE_FEATURE = "VKS_Angle"` (periodic, folds to `[0, 180)` -- pooled
circularly, but compared with the same folded-Mann-Whitney approximation
`beh/scripts/features.py`'s `compare_shape_feature` already uses for
`orientation_deg`).

- **`subject_pooled_scores(df) -> DataFrame`**
  One row per subject: each of `FEATURES` averaged (linear mean) across
  that subject's sessions, except `VKS_Angle` (circular mean, folded back
  into `[0, 180)`). Adds `n_sessions`. `df` is the raw `loader.load_fm100_raw`-shaped
  table (has a `caps` column) -- internally calls `scores.build_scores`.
- **`group_pooled_scores(df, *, group=None, subgroup=None) -> DataFrame`**
  `subject_pooled_scores` filtered to one group/subgroup.
- **`compare_fm100_feature(df, feature, *, group1=None, subgroup1=None, group2=None, subgroup2=None) -> dict`**
  Mann-Whitney U + effect size (`pingouin.mwu`) on one `FEATURES` entry
  between two groups/subgroups, on `group_pooled_scores` (one independent
  observation per subject). Returns `{feature, u_val, p_value, rbc, cles,
  n1, n2}` -- same shape as `beh/scripts/features.py`'s
  `compare_shape_feature`, run once per feature for the same reason (shows
  which feature drives a difference; doesn't assume Gaussian samples).
- **`estimate_offset(profiles1, profiles2, *, n_boot=2000, seed=0) -> dict`**
  Quantifies "group 2's profile looks like group 1's + a constant".
  `profiles1`/`profiles2` are `(n_subjects, 85)` per-subject profile arrays
  (e.g. `plotting.group_profiles`'s output), not the two group means
  directly. Point estimate `offset = mean(mean(profiles2) - mean(profiles1))`
  across cap positions. **Resamples subjects for the CI/p-value, not cap
  positions** -- the 85 positions are correlated points along one smoothed
  curve per subject, not independent observations, so a per-position test
  would pseudoreplicate; bootstraps subjects with replacement instead
  (`n_boot` times), same "resample the actual unit of replication"
  approach as `ssveps/scripts/analysis.py`'s `bootstrap_ci`. Returns
  `{offset, ci_lower, ci_upper, p_value, r_squared}`: `p_value` uses the
  `(1 + count) / (1 + n_boot)` correction used by every permutation/
  bootstrap test elsewhere in this project; `r_squared` is the standard
  regression R² for the model `mean(profiles2) ~= mean(profiles1) + offset`
  (SS_total is `mean(profiles2)`'s own across-position variance) -- **not**
  `1 - var(diff - mean(diff))/var(diff)`, which is mathematically always 0
  (caught by this module's own test suite before shipping; see the
  function's docstring). The additive analog of
  `ssveps/scripts/analysis.py`'s `fit_gain_shape` (M8), gain fixed at 1.
- **`correct_multiple_comparisons(result, *, method='holm', alpha=0.05) -> DataFrame`**
  (M3) Adds `p_corrected`/`significant` columns to any DataFrame with a
  `p_value` column, via `statsmodels.stats.multitest.multipletests`. A
  self-contained copy of `ssvepBeh/scripts/correlation.py`'s function of
  the same name (not imported from there, same no-cross-import
  convention). Scoped to whatever rows are passed in -- call once per
  comparison pair (`FEATURES` gives 6 tests/family).
- **`tukey_outlier_mask(values) -> ndarray[bool]`**
  (M3) Classic Tukey rule: `True` where a value falls more than 1.5xIQR
  beyond its own `[Q1, Q3]` box -- the same rule matplotlib's own
  `boxplot(showfliers=True)` uses. Shared by `plot_feature_boxplot` and
  `subject_feature_outliers`.
- **`subject_feature_outliers(df, *, group=None, subgroup=None, features=FEATURES) -> DataFrame`**
  (M3) One row per subject, one bool column per feature
  (`tukey_outlier_mask` against that group's own `group_pooled_scores`)
  plus `n_flagged`. `MAJORITY_FEATURES = 4` (> half of `FEATURES`) is the
  exclusion threshold `05_outlier_flagging.ipynb` uses to rerun the HC-vs-PD
  offset without CTR subjects who look unlike their own group on most
  features.

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
- **`02_group_comparisons.ipynb`** -- M2: `comparisons.compare_fm100_feature`
  across all 6 `FEATURES` for CTR vs PD, HC vs protan, HC vs deutan, protan
  vs deutan. *Edit:* `pairs`/`pair_labels` (top cell) for a different set
  of comparisons.
- **`03_flagged_subjects.ipynb`** -- M2: `plot_subject_fm100` (linear, then
  radial at both `label_mode`s) for MET020, MET047, MET021 individually,
  then a combined `plot_group_fm100` with `sub_ids=` for all three.
  *Edit:* `flagged` (top cell) for a different set of subjects.
- **`04_hc_vs_pd.ipynb`** -- M2: HC vs PD profiles side by side (both
  `kind`s), the `compare_fm100_feature` battery filtered to this pair
  (plus its M3 `correct_multiple_comparisons` addition -- nothing survives
  at this family size), and `comparisons.estimate_offset(plotting.group_profiles(df,
  group='CTR'), plotting.group_profiles(df, group='PD'))` with a plot
  overlaying HC's mean, PD's mean, and "HC + offset" to show the fit
  visually. *Edit:* `categories` (top cell) for a different pair.
- **`05_outlier_flagging.ipynb`** -- M3: `plot_feature_boxplots_grid` for
  CTR/PD/protan/deutan across all 6 `FEATURES`; `subject_feature_outliers`
  to list which CTR subjects are flagged, and on how many features; the
  `MAJORITY_FEATURES`-threshold exclusion list (one subject, MET020); and
  `estimate_offset` rerun on HC-minus-that-subject vs. PD, compared
  side by side with `04_hc_vs_pd.ipynb`'s original numbers.
