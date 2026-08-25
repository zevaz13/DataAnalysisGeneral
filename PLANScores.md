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

## M2. 
- [ ] For the radar plots, we should add the possibility of changing the numbers around it. by default, we can use the angles (which has clear interpretation). However, the test usually is presented with the cap number instead. [85 1: 84], notice that the vector starts with 85, instead of 1. 
- [ ] Make FM100 group comparisons between groups. We should compare the features CTR vs PD, HC vs protan, HC vs deutan, protan vs deutan.
- [ ] I want to see specific plots for MET020, MET047, MET021.
- [ ] Make specific plots between HC and PD. and lets quantify the dc offset between the groups, PD looks like HC + a number, when compared. 
## Next milestones

To be defined together.
