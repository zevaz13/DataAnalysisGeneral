The data in /home/sebas/data/manualTest includes results for the behavioral (manual test of my experiment.) This is to be implemented under /beh

## Documents

- `beh/README.md` -- data dictionary and script/notebook index. **Read this
  first.**
- `docs/beh_api_reference.md` -- every function's signature and parameters
  (loader, plotting, comparisons).

## Decisions made while implementing M1

- **Hotelling T² package:** used [`hotelling`](https://github.com/dionresearch/hotelling)
  (PyPI, added to `pyproject.toml`) rather than a hand-rolled implementation,
  per your instruction to prefer a package if one exists. It implements the
  standard unpaired two-sample test (pooled covariance, unequal n) needed
  for the group comparisons below. Note `beh/templateCode/Hot_Tsqd_2samplesPaired.m`
  is a different test (paired, one-sample-on-differences, equal-n,
  row-matched) -- not a direct port target for these comparisons; the same
  `hotelling` package covers that case too (one-argument call) if a paired
  within-subject comparison is wanted later.
- **Unit of observation, made a parameter:** `compare_groups(..., unit=)` --
  `'subject'` (default, one mean point per subject, statistically
  independent, used for every p-value below) or `'point'` (every click
  pooled, pseudoreplicated but shows point-cloud shape -- needed for
  protan/deutan where n=7-8 subjects is too sparse to see shape at the
  subject level).
- **Subgroup lookup:** live from `ssveps/files/metadata.csv` at load time
  (not a persisted merged copy) -- same participants, shared data, no build
  step to remember to rerun.
- **Module naming collision (fixed, not just avoided):** `beh/scripts/`
  and `ssveps/scripts/` both have `loader.py`/`plotting.py`. A bare `pytest`
  at the repo root would silently cache whichever loads first under those
  bare names and break the other suite -- both `tests/` files now drop any
  stale cached module before importing their own, so this is safe regardless
  of collection order. See `beh/README.md`'s Tests section.

### M1

- [x] Load the data (`beh/scripts/loader.py`, `load_behavioral`), same
  participants as the SSVEP experiment.
    - [x] `PartType` -> `group`: 1=HC(CTR), 2=CVD, 3=PD, 4=HD -- confirmed to
      match `ssveps/files/metadata.csv`'s own `group` column exactly for all
      43 overlapping subjects (pinned by `beh/tests/test_beh.py`).
    - [x] `subgroup` (protan/deutan) for CVD participants, looked up live
      from `ssveps/files/metadata.csv`.
- [x] Plot one participant, one session (`plotting.plot_subject_session`).
- [x] Plot one participant, multiple sessions, each its own color
  (`plotting.plot_subject_sessions`).
- [x] Plot one participant, cloud of points across sessions
  (`plotting.plot_subject_cloud`).
- [x] Plot a group/subgroup: grid (max 5/row, `plotting.plot_subjects_grid`)
  or all pooled onto one plot (`plotting.plot_subjects_pooled`).
- [x] Plot an arbitrary hand-picked set of participants: same two functions,
  pass `sub_ids=` instead of `group=`/`subgroup=`.
- [x] Axis limits x=[0,3200], y=[0,2000] as plot defaults (not data
  clipping -- some subjects' green does run past 2000, left visible when
  `ylim=` is overridden). Labels "red"/"green".
- [x] Hotelling T² (`beh/scripts/comparisons.py`) -- see "package" decision
  above.
- [x] Groups side by side: HC, PD, CVD, protan, deutan
  (`plotting.plot_groups_side_by_side`) -- HD excluded, n=1, same convention
  as `ssveps/notebooks/04_distributions.ipynb`.
- [x] Group/subgroup comparisons, `unit='subject'` (`01_explore.ipynb`):
    - [x] HC vs PD -- T²=26.8, F=12.96, p=0.0001 (n=23, 8)
    - [x] HC vs CVD -- T²=24.7, F=12.01, p=0.0001 (n=23, 15)
    - [x] HC vs protan -- T²=19.7, F=9.52, p=0.0007 (n=23, 8)
    - [x] HC vs deutan -- T²=38.8, F=18.71, p<0.0001 (n=23, 7)
    - [x] protan vs deutan -- T²=20.3, F=9.36, p=0.0042 (n=8, 7)

**All five significant at the subject level**, including protan vs. deutan
-- notably clearer than the SSVEP `ramp_slope_red` subtype comparison
(`ssveps/notebooks/08_cvd_gamut.ipynb`: p=0.44). Plausible, not
contradictory: a direct behavioral report of the isoluminant point is a more
direct measure of the perceptual judgment than an indirect neural
correlate. Worth tracking as both datasets develop in parallel -- this task
may resolve some of what the SSVEP measures are still underpowered for.

### M2 Shape features and comparisons

**Aim:** M1 already found every group pair significant on subject-mean
location alone, including protan vs. deutan (p=0.0042) -- more clearly than
SSVEP's own `ramp_slope_red` subtype comparison (p=0.44). M2 goes past the
mean to ask whether the *shape* of a subject's point cloud (not just its
center) sharpens that split further, since protan and deutan clouds were
noted as each tracing a fairly uniform line rather than a blob.

- [x] Shape features (`beh/scripts/features.py`) -- PCA on each subject's
  pooled (red, green) clicks, giving three features per subject:
  `orientation_deg` (angle of the fitted line, folded to [0, 180)),
  `along_var` (spread along the line), `perp_var` (scatter off the line --
  match consistency). `group_features` collects these per group/subgroup.
- [x] Plotting (`beh/scripts/plotting.py`) -- `show_fit=True` on
  `plot_subject_cloud`/`plot_subjects_grid` overlays each subject's fitted
  PCA line; `plot_feature_space` scatters subjects in shape-feature space
  (e.g. orientation vs. perp_var), colored by group/subgroup, capped at 3
  categories per the dataviz skill's all-pairs scatter color limit.
- [x] Comparisons (`features.compare_shape_feature`) -- Mann-Whitney U +
  effect size (pingouin) per feature, since n=7-8 for protan/deutan is small
  and orientation isn't safely Gaussian. Not a single omnibus stat like
  Hotelling T^2 -- run once per feature to see which shape property (if any)
  drives a given group difference.
- [x] Run the same five group comparisons as M1 (HC vs PD, HC vs CVD, HC vs
  protan, HC vs deutan, protan vs deutan) on all three shape features in
  `beh/notebooks/02_shape_features.ipynb`.

**`orientation_deg` separates protan from deutan perfectly** (p=0.0003,
rank-biserial=1.0, common-language effect size=1.0 -- every protan
subject's line orientation falls on one side of every deutan subject's).
Cleaner than M1's mean-location Hotelling T² on the same groups (p=0.004),
and far cleaner than SSVEP's `ramp_slope_red` (p=0.44) -- the line's
*direction* carries more subtyping signal than its *position*. `along_var`
trends the same direction (p=0.07) but isn't significant at n=8,7.
`perp_var` (match consistency) doesn't separate any group pair in this
dataset -- HC vs PD is the only borderline case on any shape feature
(p=0.03), everything else involving CVD subtypes is far from significant.
Worth checking whether an orientation/direction-style feature can be
extracted from the SSVEP gamut data too, as it may outperform
`ramp_slope_red` there the same way.

## M3. other

- [ ] make a plot for centroids, per subject, and groups. The one per subject, please color code the grorups. 
- [ ] Do the same type of plot for all the new features. 

## Next milestones

To be defined together.
