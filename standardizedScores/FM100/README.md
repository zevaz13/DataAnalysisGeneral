# FM100 (Farnsworth-Munsell 100 Hue test)

Standardized clinical color-vision test: each participant arranges 85 caps
in hue order; how far the final arrangement deviates from the correct order
is scored several ways (TES, PES, VKS ellipse metrics -- see
`docs/fm100_api_reference.md`).

Raw data: `/home/sebas/data/standardizedScores/repeatedSessionsPY.txt` (read
in place, not copied into the repo), one row per (subject, session) --
subjects are the same MET* IDs used by `ssveps/` and `beh/`.
Function-by-function reference: `docs/fm100_api_reference.md`. Plan and
milestone status: `../../PLANScores.md`.

## Fields (tidy table, as loaded by `loader.load_fm100_raw`)

- `sub_id`, `session` -- parsed from the raw file's Reference field
  (`MET000` -> session 1, `MET000b` -> session 2, `MET000c` -> session 3).
- `group`, `subgroup` -- looked up live from `ssveps/files/metadata.csv` by
  `sub_id` (same pattern as `beh/scripts/loader.py`, not a persisted merged
  copy). A subject absent from that file gets `group='UNKNOWN'`,
  `subgroup='NA'` -- currently just `MET047` (new to this dataset, no
  SSVEP/behavioral data at all). `MET021` *is* in `ssveps/`'s metadata
  (`CTR`) and keeps that label here, even though it was flagged as possibly
  a different (non-red-green) deficiency type -- see the M1 notebook for
  why that flag looks plausible in the scores themselves.
- `sex`, `date` -- carried through unchanged, not currently used by any
  analysis (like `beh/`'s `date`/`folder`).
- `caps` -- length-85 int array, the cap IDs in placement order.

The raw file's other columns (an apparent duration field and an unlabeled
numeric field) have inconsistent formats across rows (`"8"`, `"6 min"`,
`"715"`) and aren't parsed.

**Raw-file quirk:** the first line is a byte-identical duplicate of the
second (`MET000`) row -- a data export glitch, not a header. `skiprows=1`
in `load_fm100_raw` drops it.

## Scripts

- `scripts/loader.py` -- `load_fm100_raw`, `subjects_in_group` (own copy,
  independently implemented per project like `beh/`'s and `ssveps/`'s).
- `scripts/scores.py` -- TES, PES (red-green/blue-yellow), tray-level TES,
  and VKS ellipse metrics. A refactor of `templateCode/FM100.py`'s scoring
  math, not a rewrite -- `tests/test_fm100.py` pins every function's output
  against the original template on all 69 real rows. Computed live on load
  (not persisted to a derived CSV) -- cheap at this size.
- `scripts/plotting.py` -- linear (cap position vs. error) and radial (the
  "trademark" FM100 polar diagram) plots, for one participant (one line per
  session), a group/subgroup, or a hand-picked `sub_ids` list, with a
  circular moving-average `window=` filter and ±1 SD group-variability
  shading. `label_mode='cap'` (M2) relabels the radial plot's angle ticks
  with the FM100 test's own printed-diagram convention (`85, 5, 10, ... 80`
  -- the sequence starts at cap 85, not cap 1) instead of matplotlib's
  default angle-in-degrees ticks. `group_profiles` (renamed from
  `_group_profiles`, now public) is reused directly by `comparisons.py`'s
  `estimate_offset`.
- `scripts/comparisons.py` -- M2: `compare_fm100_feature` (Mann-Whitney U +
  effect size on `subject_pooled_scores`, mirroring
  `beh/scripts/features.py`'s `compare_shape_feature`) over `FEATURES`
  (`TES, PES_RG, PES_BY, VKS_MajRad, VKS_MinRad, VKS_Angle`), and
  `estimate_offset` (does one group's profile look like another's + a
  constant -- subject-level bootstrap CI/p-value, not a per-cap-position
  test, which would pseudoreplicate). Deliberately self-contained (doesn't
  import `ssvep_beh_fm100/`, even though that project already has similar
  per-subject pooling logic) -- keeps this base modality's dependencies
  one-directional, matching the project's layering convention.

## Tests

`uv run pytest standardizedScores/FM100/tests -q`. Same module-naming-
collision defense as `beh/`'s and `ssveps/`'s test files (see
`beh/README.md`'s Tests section) -- `loader`/`plotting`/`scores`/
`comparisons` are dropped from `sys.modules` before import (`comparisons`
because `beh/scripts/` already has one under the same bare name).

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- `01_explore.ipynb` -- M1: load and score every row; MET047/MET021 in
  detail; group score table (PES_RG vs. PES_BY by group/subgroup); linear
  and radial plots for one participant, with the moving-average filter;
  group plots with ±1 SD shading (HC/PD/CVD/protan/deutan); an arbitrary
  hand-picked set (MET047 + MET021 together).
- `02_group_comparisons.ipynb` -- M2: `compare_fm100_feature` across all 6
  `FEATURES` for CTR vs PD, HC vs protan, HC vs deutan, protan vs deutan.
  HC vs protan/deutan significant on every magnitude feature (TES/PES_RG/
  PES_BY/VKS_MajRad/VKS_MinRad); `VKS_Angle` significant for protan
  (p=0.013) but not deutan (p=0.10); protan vs deutan not significant on
  anything at this n; CTR vs PD significant on every magnitude feature but
  not `VKS_Angle` either.
- `03_flagged_subjects.ipynb` -- M2: linear and radial (both `label_mode`s)
  plots for MET020, MET047, MET021 individually, then together.
- `04_hc_vs_pd.ipynb` -- M2: HC vs PD profiles and the DC-offset question.
  `estimate_offset`: offset=1.04 (bootstrap 95% CI [0.32, 1.81], p=0.003 --
  a real, non-zero constant), but R2=0.50 -- the constant explains only
  about half of PD's own cap-to-cap shape relative to HC's, so "PD = HC + a
  number" is a real but partial description, not the whole story.
