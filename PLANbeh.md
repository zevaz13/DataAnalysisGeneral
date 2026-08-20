The data in /home/sebas/data/manualTest includes results for the behavioral (manual test of my experiment.) This is to be implemented under /beh

## Documents

- `beh/README.md` -- data dictionary and function reference (loader,
  plotting, comparisons). **Read this first.**

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

## Next milestones

To be defined together.
