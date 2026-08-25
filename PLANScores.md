The data in /home/sebas/data/standardizedScores includes results for the FM100 hue test. Code is to be implemented under /standardizedScores/FM100

## Documents

- `standardizedScores/FM100/README.md` -- data dictionary, script/notebook
  index, and implementation decisions (raw-file header quirk, group/subgroup
  lookup, MET047/MET021 handling, `scores.py` verification against the
  template). **Read this first.**
- `docs/fm100_api_reference.md` -- every function's signature and parameters.
- `docs/findings.md` section 1 -- results narrative and interpretation.

Under `/standardizedScores/FM100/templateCode`, reference code from past work
is available.

## M1. Implementation and modularization of FM100 routines

- [x] Load, group, and plot FM100 data (`loader.py`, `plotting.py`),
  refactored from `templateCode/FM100.py` and verified bit-for-bit identical
  on all 69 real rows.
- [x] Feature extraction: TES, PES red-green, PES blue-yellow, VKS
  ellipse metrics (`scores.build_scores`).
- [x] MET047 kept unlabeled (not HC/CVD/any subgroup) -- a distinct-deficiency
  candidate, alongside MET021.
- [x] Per-participant linear plots with gentle filtering, plus the classic
  FM100 radial plot.
- [x] All plot types for one participant, a group (HC/CVD/PD/protan/deutan),
  or an arbitrary participant list, with variability shading on group plots.

`standardizedScores/FM100/notebooks/01_explore.ipynb` walks through all of
this on the real data. See `docs/findings.md` section 1 for the MET047/MET021
headline findings.

## M2. Radial cap labels, group comparisons, flagged subjects, HC vs PD offset

- [x] **Radial cap-number labels.** `plotting.py`'s `plot_subject_fm100`/
  `plot_group_fm100` gained `label_mode='angle'|'cap'` (radial only).
  `'cap'` relabels the ticks with the FM100 diagram's own convention --
  sequence starts at 85 at angle 0, then 1, 2, ... 84, one label every 5th
  cap (17 labels). `_group_profiles` renamed to `group_profiles` (made
  public) along the way, reused directly by the new offset function below.
- [x] **`02_group_comparisons.ipynb`** -- new `comparisons.py`,
  `compare_fm100_feature` (Mann-Whitney U, mirroring `beh/`'s
  `compare_shape_feature`) across `TES, PES_RG, PES_BY, VKS_MajRad,
  VKS_MinRad, VKS_Angle` for all four requested pairs. **HC vs protan and
  HC vs deutan significant on every magnitude feature** (p<0.02 throughout,
  most p<0.001); `VKS_Angle` significant for protan (p=0.013) but not
  deutan (p=0.10) -- an asymmetry worth noting alongside `docs/findings.md`
  section 5's own protan/deutan asymmetries. **Protan vs deutan: nothing
  significant** on any feature, consistent with every other protan-vs-
  deutan comparison in this project being underpowered at n=8 vs 7. **CTR
  vs PD: significant on every magnitude feature, but not `VKS_Angle`** --
  PD's error is elevated in overall size, not in confusion-axis direction,
  which foreshadows the offset finding below.
- [x] **`03_flagged_subjects.ipynb`** -- MET020, MET047, MET021, linear and
  both radial label modes, individually and combined.
- [x] **`04_hc_vs_pd.ipynb`** -- HC vs PD profiles, the same comparison
  battery filtered to this pair, and the DC-offset question via new
  `comparisons.estimate_offset` (subject-level bootstrap CI/p-value, not a
  per-cap-position test -- see the function's docstring for why that
  distinction matters here). **A real offset exists** (c=1.04, 95% CI
  [0.32, 1.81], p=0.003, doesn't include 0) **but only explains about half
  of PD's own shape** (R²=0.50) -- "PD looks like HC + a number" is a real,
  statistically solid partial description, not the whole story; real
  per-position structure remains beyond the constant.

## Next milestones

To be defined together.
