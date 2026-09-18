# Dashboard: work-to-date summary

Kept current. Companion docs: `PLANdashboard.md` (index + open items),
`dashboard/README.md` (how to run, layout, how to add a page).

## What it is

A Streamlit app over the existing FM100/behavioral/SSVEP analysis code --
a thin presentation layer with no analysis logic of its own. Every page
imports and calls the same `loader.py`/`plotting.py`/`comparisons.py`
functions the corresponding notebook uses. Purpose: swap
subject/group via widgets instead of re-running notebook cells, let
collaborators see headline figures without installing `uv` or opening
Jupyter, and stand as a concrete portfolio artifact.

Explicitly not a replacement for notebooks -- new findings still get
discovered there; the dashboard only presents results already computed.
Run with `uv run streamlit run dashboard/Home.py`.

## Architecture

- **Framework: Streamlit**, pure Python, native multi-page layout.
  `dashboard/Home.py` is the landing page; one page per analysis line
  under `dashboard/pages/` (`1_FM100.py`, `2_Behavioral.py`, `3_SSVEP.py`).
  Adding a line later (`ssvepBeh`, `ssvep_beh_fm100`) means adding one more
  `pages/N_*.py` following the same pattern.
- **Same repo, new top-level `dashboard/` directory**, importing directly
  from each project's `scripts/`. Splitting into a separate repo would mean
  packaging those imports for zero benefit at this (local, single-user)
  scale.
- **`dashboard/_pagesetup.py`**: `beh/scripts`, `ssveps/scripts`, and
  `standardizedScores/FM100/scripts` each define their own bare-named
  `loader.py`/`plotting.py`/etc, which collide in `sys.modules` once more
  than one is imported in the same long-running process -- exactly what
  happens once all pages are live together in one Streamlit process.
  `use_scripts(rel_path, *names)` drops the stale cached module and
  re-imports from the correct directory before each page runs. Also holds
  `CATEGORY_OPTIONS` (shared dashboard-layer config, de-duplicated off all
  three pages in M2) and `sidebar_mode_header()` (M3's colored section
  headers).
- **Data freshness: manual/occasional.** No live pipeline, no database.
  Pages call the same loaders the notebooks use, wrapped in
  `st.cache_data`; refreshing derived data is the same manual
  build-script step as for the notebooks.
- **Hosting: local only.** No auth/deployment. A public/portfolio-hosted
  version (with de-identified or synthetic data) is a possible future
  milestone, not yet started.
- Matplotlib figures rendered via `st.pyplot` throughout -- no Plotly
  rewrite for interactivity yet.

## Current state per page

Each page uses `st.segmented_control()` as a mode switcher (replacing an
earlier `st.tabs()` version -- tabs can't tell the running script which
tab is visible, so sidebar widgets inside `with tab:` blocks rendered for
every tab regardless of which was selected; segmented control's return
value drives real conditional branching instead).

- **FM100** (`1_FM100.py`, red `#e34948` group-mode / blue `#4682b4`
  participant-mode headers): Group mode -- up to 4 categories, radial/linear
  toggle (radial defaults to cap-color wheel, linear defaults to cap-color
  overlay), 1-10 smoothing window, optional compare-to-participant overlay
  (`plot_group_vs_subjects_fm100`, dashed subject lines on solid group
  bands). Participant mode -- up to 4 participants (1 selected ->
  `plot_subject_fm100`, 2+ -> `plot_subjects_fm100`), same plot-style and
  smoothing controls. Pairwise Mann-Whitney p-value table for a
  user-chosen feature.
- **Behavioral** (`2_Behavioral.py`, green `#5f8158` shape-features header):
  Raw clicks mode -- up to 8 subjects, side-by-side (`plot_subjects_grid`,
  4-column layout) or overlaid (up to 4, `plot_subjects_cloud_overlay`;
  beyond 4 it silently falls back to side-by-side with an explanatory
  caption rather than raising the color cap). Shape features mode -- up to
  4 categories, x/y shape-feature picker over `plot_feature_space`, a
  single-subject `plot_subject_cloud(show_fit=True)` panel, and
  plain-language descriptions of `orientation_deg`/`along_var`/`perp_var`.
  Pairwise significance for both click location (Hotelling T²) and the
  selected shape feature (Mann-Whitney).
- **SSVEP** (`3_SSVEP.py`, yellow `#f1c232` individuals-mode header): Groups
  mode -- up to 4 categories, normalization radio (percent/db/raw, each
  with its own fixed colormap), optional per-panel behavioral-click overlay
  (`ssvepBeh/scripts/plotting.py`'s `plot_grids_with_clicks`), per-category
  subject breakdown, pairwise cluster-permutation significance
  (`n_perm` slider, cached). Individuals mode -- subject multiselect across
  every subject at session 1, same normalization and click-overlay
  controls, no significance-test section (removed entirely, not just
  hidden -- confirmed via `AppTest`).

## Milestone history

Full checklist detail lives in `PLANdashboard.md`; this is the narrative.

- **M1 (MVP).** Three pages, one headline plot and one p-value table each,
  built directly on each project's existing `loader`/`plotting`/`comparisons`
  functions. `_pagesetup.py`'s module-isolation fix was the one thing not
  anticipated in the original design -- needed as soon as more than one
  project's same-named scripts were imported into the same process.
  Verified via a full HTTP route check plus a direct in-process call
  sequence matching every page's imports, confirming p-values matched
  `docs/findings.md`'s already-documented numbers (e.g. behavioral
  `orientation_deg` protan-vs-deutan p=0.0003).
- **M2 (first-pilot improvements).** Tabs added per page (raw
  clicks/shape-features, groups/individuals, etc.); category caps raised
  from 3 to 4 using two newly-validated colorblind-safe colors
  (`#4a3aa7` accepted, `#eda100` rejected -- failed the dataviz skill's
  deltaE floor against an existing color); per-subject overlay views added
  to FM100 and Behavioral; SSVEP's `db` colormap bug fixed (a `cmap or
  EEG_CMAP` fallback was silently forcing viridis regardless of the
  sidebar's normalization choice for every other mode). Review-driven
  cleanup: duplicated inline plotting code in the dashboard was promoted to
  a proper `plot_grids_with_clicks` in `ssvepBeh/scripts/plotting.py`;
  `CATEGORY_OPTIONS` deduplicated into `_pagesetup.py`. Full suite
  171/171 (12 new) at milestone close.
- **M3 (sidebar-per-mode UI).** `st.tabs()` replaced with
  `st.segmented_control()` everywhere once the tabs-don't-report-selection
  problem above was identified; each mode now shows/hides its own sidebar
  widgets for real. `layout="wide"` added to every page. FM100 linear plots
  gained the same cap-numbering convention radial already had. Verified via
  `streamlit.testing.v1.AppTest` (every page, every mode, asserting the
  other mode's widgets are genuinely absent, not just visually hidden) plus
  an HTTP check on a scratch port. Full suite 253/253 at milestone close.

## Verification convention

Every milestone has used the same two-layer check: (1) an HTTP-level pass
hitting all routes on a scratch Streamlit instance, checking for
tracebacks in the server log, and (2) either a direct in-process call
sequence exercising every page's actual function calls, or (once
`streamlit.testing.v1.AppTest` came into use at M3) a scripted run of each
page through every mode with real widget selections, asserting on which
widgets are present. The underlying analysis test suites
(`beh/`, `standardizedScores/FM100/`, `ssveps/`, `ssvepBeh/`) are run in
full at each milestone close to catch regressions from any shared
`plotting.py`/`analysis.py` changes the dashboard work required.

## Where this stands

M1-M3 are complete and live (`uv run streamlit run dashboard/Home.py`).
No next milestone is committed yet -- see `PLANdashboard.md`'s "Next
milestones" for candidates under discussion (`ssvepBeh`/`ssvep_beh_fm100`
pages, Plotly interactivity, a hosted/de-identified public version).
