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
  shading.

## Tests

`uv run pytest standardizedScores/FM100/tests -q`. Same module-naming-
collision defense as `beh/`'s and `ssveps/`'s test files (see
`beh/README.md`'s Tests section) -- `loader`/`plotting`/`scores` are dropped
from `sys.modules` before import.

## Notebooks

Each opens with `sys.path.append('../scripts')`, so run them with
`notebooks/` as the working directory.

- `01_explore.ipynb` -- M1: load and score every row; MET047/MET021 in
  detail; group score table (PES_RG vs. PES_BY by group/subgroup); linear
  and radial plots for one participant, with the moving-average filter;
  group plots with ±1 SD shading (HC/PD/CVD/protan/deutan); an arbitrary
  hand-picked set (MET047 + MET021 together).
