An interactive Streamlit dashboard over the existing FM100/behavioral/SSVEP
analysis code, built as a thin presentation layer -- no data or plotting
logic gets duplicated, it only imports and calls what already exists in each
project's `scripts/`.

## Documents

- `docs/dashboard_summary.md` -- what exists, architecture decisions,
  per-page current state, and the M1-M3 milestone narrative. **Read this
  first.**
- `dashboard/README.md` -- how to run it, page layout, how to add a page.
- `docs/index.md` -- where the dashboard fits among the other projects.

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

## Key decisions

Full rationale in `docs/dashboard_summary.md`'s Architecture section.

- Framework: Streamlit (pure Python, fits the uv-only rule).
- Same repo, new top-level `dashboard/` directory, importing directly from
  each project's `scripts/`.
- Native multi-page layout, one `pages/N_*.py` per analysis line.
- Data freshness is manual/occasional -- no live pipeline, no database.
- Local hosting only for now.

## Completed (M1-M3)

Delivered and in the repo. Detail and verification lives in
`docs/dashboard_summary.md`; this is the index.

- **M1 -- MVP.** Three pages (`1_FM100.py`, `2_Behavioral.py`, `3_SSVEP.py`),
  one headline plot and one pairwise p-value table each, calling directly
  into each project's existing `loader`/`plotting`/`comparisons` functions.
  `_pagesetup.py` added to solve cross-project module-name collisions.
- **M2 -- First-pilot improvements.** Tabs per page, category caps raised
  3->4 with two newly-validated colors, per-subject overlay views (FM100,
  Behavioral), SSVEP `db`-colormap bug fixed, duplicated dashboard plotting
  code promoted into `ssvepBeh/scripts/plotting.py`.
- **M3 -- Sidebar-per-mode UI.** `st.tabs()` replaced with
  `st.segmented_control()` on all three pages (tabs can't report which tab
  is selected, so sidebar widgets weren't actually mode-scoped before this);
  colored per-mode sidebar headers; `layout="wide"`; FM100 linear plots
  gained radial's cap-numbering convention.

## Next milestones

To be defined together. Candidates raised so far: `ssvepBeh` and
`ssvep_beh_fm100` pages following the same pattern; revisiting matplotlib
vs. Plotly for real interactivity; a hosted/portfolio version with
de-identified or synthetic data.

<!-- New work items go below this line. -->
