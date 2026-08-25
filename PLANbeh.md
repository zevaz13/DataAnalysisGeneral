The data in /home/sebas/data/manualTest includes results for the behavioral (manual test of my experiment.) This is to be implemented under /beh

## Documents

- `beh/README.md` -- data dictionary, script/notebook index, and
  implementation decisions (Hotelling T² package choice, `unit=` parameter,
  subgroup lookup, module-naming-collision fix). **Read this first.**
- `docs/beh_api_reference.md` -- every function's signature and parameters.
- `docs/findings.md` section 2 -- results narrative and interpretation.

### M1. Load, plot, and compare groups on click location

- [x] Load data (`loader.load_behavioral`), same participants/groups/subgroups
  as the SSVEP experiment.
- [x] Per-subject and per-group/subgroup plotting (`plotting.py`).
- [x] Hotelling T² group comparisons (`comparisons.py`), `unit='subject'`.

**All five group comparisons significant** (HC vs PD/CVD/protan/deutan,
protan vs deutan) -- see `docs/findings.md` section 2.

### M2. Shape features and comparisons

- [x] PCA shape features per subject (`features.py`): `orientation_deg`,
  `along_var`, `perp_var`.
- [x] Plotting (`show_fit=`, `plot_feature_space`) and per-feature
  comparisons (`compare_shape_feature`, Mann-Whitney U) on the same five
  group pairs as M1.

**`orientation_deg` separates protan from deutan perfectly** (p=0.0003) --
the strongest single finding in this project so far. See `docs/findings.md`
section 2.

### M3. Centroid plots

- [x] Per-subject and per-group centroid plots, for click location
  (`plot_subject_centroids`/`plot_group_centroids`) and for the M2 shape
  features (`plot_feature_space`/`plot_feature_group_centroids`).

Confirms M1/M2 visually; deutan is the least internally-consistent group by
far. See `docs/findings.md` section 2.

### M4. 
- [ ] A notebook that explore the test-retest reliability ICCs for behavioral map features. Lets leave CVD participants out, since they have not done the experiment more than 1 (most of them) .
- [ ] Make a notbeook that plots and compares PD vs HC. Compare their resulting maps side to side, their features and explores statistical comparisons worth considering to address the differences between these groups.
- [ ] Lets find outlier clicks. I want to do this per participant first, fitting a rotated ellipse to the distribution of each participant's data. Leave out points that are 2 stds away from centroid. This could be a parameter. For now, I just want to see in a plot for all participants as a grid, their distribution of points, the fitted ellipse with the desired std, and with a different color, the points out of that ellipse. 
- [ ] Implement a group/subgroup specific outlier rejection routine. We fit a rotated ellipse to the distribution of each group/subgroup, and flag the points we leave out. We can apply these rejection to each individual in the sample and then put them all together. Plotting should be done similar as the item above.
## Next milestones

To be defined together.
