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
## M3. Cap-color radial wheel, multiple-comparisons correction, outlier flagging

- [x] **Cap-color radial wheel.** `plotting.py` gained `show_cap_wheel=True`
  (radial only, on `plot_subject_fm100`/`plot_group_fm100`/
  `plot_group_vs_subjects_fm100`), reproducing
  `fm100radialTemplate.png`: a ring of all 85 caps drawn just outside the
  data, colored by a cyclic colormap following each cap's own position on
  the test's hue circle, every one individually numbered (`_cap_label`) --
  unlike `label_mode='cap'`'s every-5th-cap ticks, which `show_cap_wheel`
  takes priority over when both are set. Demoed in `01_explore.ipynb`
  (MET020).
- [x] **Multiple-comparisons correction.** `comparisons.correct_multiple_comparisons`
  (Holm, self-contained copy of `ssvepBeh/scripts/correlation.py`'s
  function of the same name), applied once per pair (6 features/family) in
  both `02_group_comparisons.ipynb` and `04_hc_vs_pd.ipynb`. **Real
  consequence, not just plumbing: CTR vs PD loses every feature under
  correction** (smallest corrected p is 0.052, `PES_RG`) and protan vs
  deutan had nothing significant to begin with -- **only HC vs protan and
  HC vs deutan survive** (11 of the 24 total tests, all magnitude
  features plus protan's `VKS_Angle`). Matches the "underpowered
  CTR-vs-PD/protan-vs-deutan, solid HC-vs-subtype" pattern the rest of
  this project already shows.
- [x] **Outlier boxplots + flagging.** New `05_outlier_flagging.ipynb`:
  `plotting.plot_feature_boxplots_grid` (6-feature grid, CTR/PD/protan/
  deutan side by side, Tukey-rule fliers `comparisons.tukey_outlier_mask`
  marked distinctly, every subject's own value scattered and labeled by id
  minus `MET`) for the visual "who looks like deutan / who looks unlike
  their own group" read, plus `comparisons.subject_feature_outliers` for a
  reproducible per-subject outlier count. **Only one CTR subject
  (MET020) is an outlier on a majority of the 6 features** -- already one
  of this project's own flagged edge cases (`03_flagged_subjects.ipynb`,
  `docs/findings.md` section 1).
- [x] **Offset re-run without MET020.** Dropping the one majority-outlier
  CTR subject barely moves the HC-vs-PD offset (1.04 -> 1.11), tightens
  the p-value (0.0030 -> 0.0010), and doesn't improve R² (0.505 -> 0.465,
  if anything slightly worse). **"PD looks like HC + a constant" isn't an
  artifact of one unusual control** -- a genuine group-level pattern.
- [ ] Notice how in the template the cap numbers grow clockwise. Our plots should mimic this convention. 
`standardizedScores/FM100/tests/test_fm100.py` covers every new function
(correction math, Tukey masking, the wheel's point count and tick
overrides, the boxplot grid's panel count) -- 51/51 passing, 222/222 across
the whole repo.

## Next milestones

To be defined together.
