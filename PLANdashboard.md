An interactive Streamlit dashboard over the existing FM100/behavioral/SSVEP
analysis code, built as a thin presentation layer -- no data or plotting
logic gets duplicated, it only imports and calls what already exists in each
project's `scripts/`.

## Why

- **Exploration**: swap subject/group via widgets instead of hand-editing
  `categories`/`sub_ids` in a notebook cell and re-running it.
- **Sharing**: collaborators/advisors see the headline figures and their
  p-values without installing `uv` or opening Jupyter.
- **Portfolio**: a concrete, explainable artifact -- "exposed a real
  multi-dataset analysis pipeline as an interactive tool, reusing the
  existing stats/plotting functions" -- for the job applications that
  prompted this.

Explicitly *not* a replacement for notebooks: new findings still get
discovered there. The dashboard only presents results already computed.

## Decisions

- **Framework: Streamlit.** Pure Python (fits the uv-only rule), lowest
  learning curve, most commonly requested tool in DS/analytics job
  postings. Dash/Plotly considered and rejected for v1 -- more
  boilerplate for no benefit at this scale.
- **Same repo, new top-level `dashboard/` directory** (alongside `beh/`,
  `ssveps/`, `standardizedScores/`), not a separate repo. The dashboard
  imports directly from each project's `scripts/` package -- splitting
  repos would mean packaging or submoduling those imports for zero benefit
  while this stays local and single-user.
- **Native Streamlit multi-page layout**: `dashboard/Home.py` +
  `dashboard/pages/1_FM100.py`, `2_Behavioral.py`, `3_SSVEP.py`. Adding a
  line later (`ssvepBeh`, `ssvep_beh_fm100`) means adding one more
  `pages/N_*.py` file following the same pattern -- existing pages are
  untouched.
- **Data freshness: manual/occasional.** No live pipeline, no database.
  Pages call the same `loader.py` functions the notebooks use, wrapped in
  `st.cache_data`. Re-running the underlying build scripts to refresh
  derived data stays a manual step, same as today.
- **Hosting: local only for now.** `uv run streamlit run dashboard/Home.py`.
  No auth/deployment work in v1; revisit (and think about de-identifying
  data first) if a public/portfolio-hosted version is wanted later.
- **Common per-page pattern**: sidebar group/subgroup selector + subject
  multi-select, built into the same `categories`/`sub_ids` shape the
  notebooks already pass around; one headline plot from that project's
  `plotting.py`; a `st.metric`/text line with the matching comparison's
  p-value from `comparisons.py` (already computed there, just surfaced).
  Matplotlib figures rendered via `st.pyplot` -- no rewrite to Plotly for
  v1.

## M1: MVP -- three pages, one headline view each

- [x] `uv add streamlit`; `dashboard/README.md` (how to run, page-by-page
      description).
- [x] `dashboard/Home.py` -- landing page, links to the three lines below.
- [x] `dashboard/pages/1_FM100.py` -- category multiselect (HC/PD/CVD/
      protan/deutan), radial/linear toggle, `window=` slider;
      `plot_group_fm100`; if a single subject is selected,
      `plot_subject_fm100` below it; pairwise Mann-Whitney p-value table
      (`comparisons.compare_fm100_feature`, feature chosen from
      `comparisons.FEATURES`).
- [x] `dashboard/pages/2_Behavioral.py` -- category multiselect (capped at
      3, matching `plot_feature_space`'s all-pairs-scatter color limit);
      `plot_feature_space` with an x/y shape-feature picker;
      `plot_groups_side_by_side` (raw click clouds) below; optional single
      subject -> `plot_subject_cloud(show_fit=True)`; pairwise p-value
      tables for both click location (Hotelling T², `comparisons.compare_groups`)
      and the selected shape feature (Mann-Whitney, `features.compare_shape_feature`).
      (Design doc originally paired `plot_feature_space` with a `show_fit`
      toggle -- that parameter doesn't exist on that function; corrected
      during implementation to the feature-picker + separate subject-level
      `show_fit` plot described above.)
- [x] `dashboard/pages/3_SSVEP.py` -- category multiselect (capped at 3, to
      keep the permutation test's runtime bounded), normalization radio
      (percent-change default, db, raw), session fixed at 1 (matches every
      `ssveps/` notebook); `plot_groups_side_by_side`; per-category
      `plot_subjects_side_by_side` breakdown; pairwise cluster-permutation
      significance (`permutation.permutation_test_weighted`, `n_perm`
      slider, cached) reporting each pair's minimum cluster p-value.
- [x] `dashboard/_pagesetup.py` -- **not in the original design doc**,
      added during implementation: `beh/scripts`, `ssveps/scripts`, and
      `standardizedScores/FM100/scripts` each define their own
      `loader.py`/`plotting.py`/etc under the same bare names (see
      `beh/README.md`'s Tests section), which collide in `sys.modules`
      once more than one is imported in the same long-running process --
      exactly what happens as soon as this dashboard's pages are all live
      together. `use_scripts(rel_path, *names)` drops the stale cached
      module and re-imports from the correct directory before each page
      runs.
- [x] Smoke-test pass: launched the app (`uv run streamlit run
      dashboard/Home.py`), confirmed all three page routes load with no
      tracebacks; separately ran the exact import/plot/comparison calls
      each page makes in one Python process (switching "pages" in
      sequence, the same way a user would) to verify the module-isolation
      fix actually works and that p-values match already-documented
      numbers (e.g. behavioral `orientation_deg` protan-vs-deutan
      p=0.0003, matching `docs/findings.md`).

## M2. Improvements to first pilot

Two new all-pairs colorblind-safe categorical colors were needed for this
milestone (FM100/Behavioral's per-subject overlay views, and the 3->4
category cap): `#4a3aa7` (purple, already in `FULL_PALETTE`) validated
clean; `#eda100` (the palette's natural next slot) failed the dataviz
skill's normal-vision floor against `#eb6834` (deltaE 13.7 < 15) and was
rejected. Each project defines its own `SUBJECT_COLORS`/`SCATTER4_COLORS`
constant with the validated 4-color set, following this repo's existing
per-project-own-constants convention (no shared palette module).

### Home
- [x] `color-wheel.jpg` displayed via `st.image`.
- [x] Removed the "each page reuses the same..." paragraph.
- [x] Three `st.page_link` buttons in `st.columns(3)`, each with a one-line
      description underneath (FM100/Behavioral/SSVEP).
- [x] Footer links to the GitHub repo, README.md, and docs/findings.md
      (`zevaz13/DataAnalysisGeneral`, confirmed from `git remote`) --
      local-only hosting means these can't link to local files directly, so
      they point at the same repo's GitHub-rendered copies instead.
### FM100
- [x] Smoothing window slider: 1-10, step 1 (was 1-9 step 2, odd only --
      nothing in `_smooth_circular` requires an odd window).
- [x] `st.tabs(["Group", "Participant"])` replaces the single-screen layout.
- [x] Radial `label_mode` ('angle'/'cap') toggle, disabled outside radial mode.
- [x] Participant tab: multiselect up to 4 -- 1 selected reuses
      `plot_subject_fm100` (every session); 2+ uses new `plot_subjects_fm100`
      (session 1 only per subject, own color each).
- [x] Group tab: optional participant multiselect overlays onto the group
      plot via new `plot_group_vs_subjects_fm100` (group bands solid,
      individual subjects dashed on the same axes -- dash, not just color,
      carries the group-vs-individual distinction, since a subject's color
      can coincide with an unrelated category's).
### Behavioral
- [x] `st.tabs(["Raw clicks", "Shape features"])`, raw clicks first/default.
- [x] Raw clicks tab: subject multiselect (up to 4) with a
      side-by-side/overlaid radio -- side-by-side reuses existing
      `plot_subjects_grid` unchanged; overlaid uses new
      `plot_subjects_cloud_overlay` (one panel, one color per subject).
- [x] Category cap raised 3->4 (`plot_feature_space`'s hard cap now
      `SCATTER4_COLORS`, the new validated 4-color set).
- [x] Feature tab shows a plain-language description of each shape feature
      (orientation_deg/along_var/perp_var) above the feature-space plot.
### SSVEP
- [x] `db` normalization gets its own diverging colormap, `DIVERGING_GREEN_RED`
      (green pole reuses this project's own already-validated green rather
      than a new hex value; red pole and neutral midpoint match
      `DIVERGING_BLUE_RED` so "positive change = red" stays consistent
      across every diverging ramp). Percent/raw keep their existing ramps.
- [x] `st.tabs(["Groups", "Individuals"])`.
- [x] Groups tab: category cap raised 3->4 (heatmap facets have no
      color-safety cap, unlike the scatter views). "Show behavioral clicks"
      toggle rebuilds the panel grid via `analysis.mean_grid_across_subjects`
      + `ssvepBeh/scripts/plotting.py`'s `plot_grid_with_clicks(ax=...)` per
      category instead of `plot_groups_side_by_side`, since the toggle needs
      per-panel click overlays that function doesn't produce. Per-group
      subject breakdown (`plot_subjects_side_by_side`) kept at the end of
      the tab.
- [x] Individuals tab: subject multiselect draws from every subject at
      session 1, not one group (`plot_subjects_side_by_side`'s existing
      `sub_ids=` param already supports this -- no new plotting code
      needed). Same behavioral-click toggle as the Groups tab.
- [x] `plot_grid_with_clicks` gained `s=`/`alpha=`/`cmap=` params (previously
      hardcoded); dashboard overlay calls use `s=8, alpha=0.4` (smaller/more
      transparent than the notebooks' `s=20, alpha=0.8` defaults) and pass
      through the db colormap override.
- [x] Full test suite (`beh/`, `standardizedScores/FM100/`, `ssveps/`,
      `ssvepBeh/`) still passes (171/171, 12 new); dashboard smoke-tested
      both via HTTP (all 4 routes, no server-log tracebacks) and by directly
      calling every new/changed function with real data in one process.

### Review-driven cleanup (not in the original ask)
- [x] The behavioral-click-overlay grids were first built as two near-
      identical inline `plt.subplots` loops in `dashboard/pages/3_SSVEP.py`
      (Groups and Individuals tabs) -- flagged in review as duplicated
      plotting logic living in the dashboard instead of `scripts/`, with no
      shared color scale or panel-wrapping across the panels it drew (unlike
      every sibling multi-panel function in this repo). Replaced with a
      proper `plot_grids_with_clicks` in `ssvepBeh/scripts/plotting.py`
      (its own `_multi_panel_figure`/`_auto_clim`, mirroring
      `ssveps/scripts/plotting.py`'s), called once per tab.
- [x] `CATEGORY_OPTIONS` was duplicated verbatim across all three pages --
      moved to `dashboard/_pagesetup.py` as shared dashboard-layer config.
- [x] Added tests for the three new plotting functions
      (`plot_subjects_fm100`, `plot_group_vs_subjects_fm100`,
      `plot_subjects_cloud_overlay`) and for `plot_grid_with_clicks`'s new
      `s=`/`alpha=`/`cmap=`/`vmin=`/`vmax=` params and the new
      `plot_grids_with_clicks`, matching this repo's existing
      one-test-per-plot-function-plus-cap-rejection convention.
- [x] **Dashboard matched to the latest FM100 plotting.py** (M3's radial
      hole/clockwise-cap fixes were already automatic/unconditional, so
      nothing to wire up there; `show_cap_wheel`/`show_cap_colors` weren't
      exposed at all). Checked `beh/`/`ssveps/` for the same kind of drift
      first (`git log`/`git status` on their `plotting.py` files) -- neither
      has changed since M2, so this was FM100-only.
- [x] **Radial FM100 defaults to cap colors.** `1_FM100.py`: `show_cap_wheel
      = kind == "radial"`, `show_cap_colors = kind == "linear"` -- both
      plot styles show their cap-color feature automatically now (you
      confirmed linear should default on too, matching radial). Added
      `show_cap_wheel` to `plot_subjects_fm100` (`standardizedScores/FM100/
      scripts/plotting.py`) since the dashboard's multi-participant view
      needed it and it was the one of the four FM100 plotting functions
      that didn't have it yet. Removed the now-dead "Radial tick labels"
      angle/cap sidebar toggle (`show_cap_wheel` always overrides
      `label_mode` for radial now, so it had no effect left) -- you
      confirmed removing it rather than leaving it inert.
- [x] **SSVEP colormaps fixed to match your spec.** `3_SSVEP.py`:
      `CMAP_OVERRIDES` is now a complete `{normalize_label: cmap}` map
      instead of a partial one with a `None`/fallback gap -- percent stays
      `DIVERGING_BLUE_RED`, raw stays `SEQUENTIAL_BLUE` (both unchanged,
      identical to what `plot_groups_side_by_side`'s own internal default
      already produced), db changes from `DIVERGING_GREEN_RED` to
      `overlap_plotting.EEG_CMAP` (viridis). `DIVERGING_GREEN_RED` removed
      from `ssveps/scripts/plotting.py` (no longer used anywhere; its one
      other mention, a docstring example in `ssvepBeh/scripts/plotting.py`,
      now points at `DIVERGING_BLUE_RED` instead).
- [x] **Behavioral-click overlay no longer forces viridis.** Root cause:
      both `plot_grids_with_clicks` calls passed `cmap=cmap or
      overlap_plotting.EEG_CMAP` -- since `cmap` was `None` for percent/raw
      (no entry in the old partial `CMAP_OVERRIDES`), the `or` always fell
      through to `EEG_CMAP` (viridis) regardless of the sidebar's
      normalization selection, ignoring it entirely. With `CMAP_OVERRIDES`
      now always resolved, both calls just pass `cmap=cmap` directly --
      verified by rendering all three normalizations with clicks on and
      reading back each panel's actual `get_cmap()`: percent ->
      `diverging_blue_red`, db -> `viridis`, raw -> `sequential_blue`, each
      matching its own non-click counterpart exactly.

Verified via direct call-sequence smoke tests (every FM100 plotting
function x both `kind`s; every SSVEP normalization x click-overlay on/off,
reading back the rendered colormap) and an HTTP-level check of the running
app (`uv run streamlit run dashboard/Home.py`, all four routes 200, no
tracebacks in the server log) -- same two-layer smoke-test convention as
M1. Full test suite (244/244, no regressions from removing
`DIVERGING_GREEN_RED`) plus one new test for `plot_subjects_fm100`'s new
`show_cap_wheel` param.
## Next milestones

To be defined together -- likely candidates once M1 is live: `ssvepBeh` and
`ssvep_beh_fm100` pages following the same pattern; revisiting matplotlib
vs. Plotly for real interactivity; a hosted/portfolio version with
de-identified or synthetic data.
