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

## Next milestones

To be defined together -- likely candidates once M1 is live: `ssvepBeh` and
`ssvep_beh_fm100` pages following the same pattern; revisiting matplotlib
vs. Plotly for real interactivity; a hosted/portfolio version with
de-identified or synthetic data.
