The data in /home/sebas/data/standardizedScores includes results for the FM100 hue test. Code is to be implemented under /standardizedScores/FM100

## Documents

- `standardizedScores/FM100/README.md` -- data dictionary and script/notebook
  index. **Read this first.**
- `docs/fm100_api_reference.md` -- every function's signature and parameters
  (loader, scores, plotting).

Under /standardizedScores/FM100/templateCode, I have made some code we have used in the past available to interact with these data

## Decisions made while implementing M1

- **Raw-file quirk (root-caused, not guessed):** the raw file's first line
  is a byte-identical duplicate of the second (MET000) row, not a header --
  confirmed by diffing the two lines. The template's `skiprows=1` happens to
  drop it (its docstring's "skip header" claim is wrong, but the effect is
  the one we want); `load_fm100_raw` keeps that behavior with the correct
  explanation.
- **Group/subgroup lookup:** live from `ssveps/files/metadata.csv` by
  `sub_id`, same pattern as `beh/scripts/loader.py` -- no `partINFO.csv`
  (the raw data dir doesn't have one). MET047 (no SSVEP/behavioral data at
  all) gets `group='UNKNOWN'`. MET021 keeps its existing `CTR` label from
  `ssveps/` as-is, per your call -- even though its scores (TES 96/64, well
  above the CTR mean of ~49) are consistent with the "different deficiency"
  flag.
- **Scores computed live, not persisted** -- 69 rows, cheap to recompute on
  every load, same choice as `beh/`.
- **`scores.py` is a refactor, not a re-derivation** -- `templateCode/FM100.py`'s
  TES/PES/tray/VKS math (including the PES red-green/blue-yellow index
  groups and the VKS lookup table, both non-obvious) is transcribed
  verbatim rather than re-derived from first principles, since getting
  either wrong silently would corrupt every downstream score. Verified
  bit-for-bit identical to the template's own output on all 69 real rows
  (`tests/test_fm100.py`), with the one genuine simplification being that
  `err_vals` (the shared per-cap error) is computed once and reused for
  TES and PES, instead of the template's three separate copies of the same
  loop.
- **Group-plot variability band is subject-level, not row-level:** 19/48
  subjects have 2-3 FM100 sessions -- `plot_group_fm100` averages each
  subject's own sessions into one profile *before* computing the group
  mean/±1 SD, so a 3-session subject doesn't outweigh a 1-session one (the
  same pseudoreplication concern `beh`'s `unit='subject'` addresses).
- **Group-plot color, no 3-category cap:** unlike `beh`'s scatter plots
  (all-pairs color rule, capped at 3), the group linear/radial plots are
  *line* charts, so the dataviz skill's weaker adjacent-pair rule applies --
  all 8 `FULL_PALETTE` slots are colorblind-safe in fixed order, so
  HC/PD/CVD/protan/deutan fit on one panel without faceting.

## M1. Implementation and modularization of Fm100 routines
- [x] Implement the functionalities in the template code to load, group, and plot FM100 data.
- [x] For feature extraction lets extract TES, PES red green, PES blue yellow and vyngris scores-derived values
- [x] Subjects in the list coincide with the ssvep and behavioral subjects. MET047 is a new participant that I have not been able to allocate. They seemed to have a different CVD to red green. So it is not good to add them to HC, or CVD groups (or any of the subgroups) . However, this subject might be a good test to understand different type of deficiencies (as MET021 is too).
- [x] I would like to have functions to make linear plots per participant (with some gentle filtering as a parameter)
- [x] Appart from the plotting tools already in the list,  I want to add the trademar FM100 radial plot that just puts the linear rtesults on a circle. 
- [x] I want to be able to make the plots above, for one participant, a group of participants (HC, CVD, PD, protan, deutan), for a list of participant IDs.
    - [x] In these group plots, I want to be able to also add variability related shaded areas.

`standardizedScores/FM100/notebooks/01_explore.ipynb` walks through all of
this on the real data. Headline findings: protan and deutan both show
PES_RG clearly exceeding PES_BY (the classic red-green pattern); MET047's
TES (216) is comparable to the CVD group mean (~215) but its PES_RG (104)
and PES_BY (108) are roughly balanced -- consistent with a real deficiency
that isn't the classic red-green one, matching why you flagged it as a
useful "different type of deficiency" test case.

## Next milestones

To be defined together.
