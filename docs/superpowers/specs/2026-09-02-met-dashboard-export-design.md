# MET dashboard standalone export -- design

## Context

The dashboard (`dashboard/` in this repo, see `docs/dashboard_summary.md`)
is a thin Streamlit presentation layer over the FM100/behavioral/SSVEP
analysis code. The user's boss wants to run it himself. This repo is a
personal, multi-project research repo with notebooks, docs, and workflows
that have no place in something handed to a third party -- so the dashboard
needs to become a standalone, public repository containing only what it
needs to run, with no analysis data committed to it.

Target location: `/home/sebas/projects/met_dashboard` (sibling to this
repo, already `git init`'d, remote added as a public GitHub repo,
`zevaz13/met_dashboard`). All git operations in that repo (and in this one)
are owned by the user -- Claude does not run git commands in either repo
unless explicitly asked.

## Scope

This is a one-time export. After it lands, `met_dashboard` is an
independent codebase -- future changes to the analysis code in this repo
are not automatically propagated; porting a change over later is a manual
decision, not tooling this iteration builds.

Out of scope for this iteration (possible future work, not decided):
a repeatable export/sync pipeline, hosting/deployment beyond local
`streamlit run`, an automated data-propagation mechanism, and carrying over
this repo's narrative docs (`findings.md`, `methods.md`, per-project
`README.md`s) -- `met_dashboard` gets one top-level `README.md` covering
setup and usage, not a docs/ tree.

## What gets vendored

Dashboard code is unchanged (`_pagesetup.py`'s `use_scripts()` resolves
paths relative to repo root, so preserving the same relative directory
layout means no dashboard code needs to change for this reason):

- `dashboard/` -- `Home.py`, `pages/`, `_pagesetup.py`, `color-wheel.jpg`
  (not `README.md` -- replaced by the new repo's own top-level README).

Full `scripts/` and `tests/` directories, copied as-is, for each of the
four projects the dashboard imports from -- not a hand-trimmed subset.
Runtime dependency tracing (done during design) confirmed the dashboard
only touches a subset of each project's modules (e.g. `ssveps/scripts/`:
`analysis`, `permutation`, `plotting`, `reliability` -- not `loader.py`,
`build_derived.py`, `update_derived.py`, `build_troughs.py`, `pca.py`,
`variance.py`), but vendoring whole directories is cheaper and safer than
maintaining a trimmed subset: the total is ~5,000 lines, and a trimmed copy
risks silently breaking on a bare `import` not caught during tracing (this
already happened once during tracing itself: `ssveps/scripts/plotting.py`
bare-imports `reliability`, which isn't in `use_scripts()`'s explicit
argument list). Unused modules (e.g. `build_derived.py`) ship as inert
reference code, not wired into the app.

Projects vendored: `beh/`, `ssveps/`, `standardizedScores/FM100/`,
`ssvepBeh/` -- each as `<project>/scripts/` + `<project>/tests/` at the
same relative path as in this repo.

## Data handling

No per-subject data -- raw or derived -- is committed to `met_dashboard`,
now that the repo is public. This includes files that are currently
committed to *this* repo (`ssveps/files/*.csv`): the same exclusion rule
applies uniformly regardless of whether data is raw or already-derived.

**Scaffolding, not data, lives in git.** A `data/` tree is committed with
the exact expected subfolders, each holding a placeholder (`.gitkeep` or a
short file naming what goes there) so the structure exists in git while
being empty of content:

```
data/
  standardizedScores/repeatedSessionsPY.txt   (placeholder only)
  manualTest/behavioral_table.csv             (placeholder only)
  ssveps/files/
    metadata.csv, runmap.csv, baselines.csv,
    subject_troughs.csv, group_troughs.csv, grid.json   (placeholders only)
```

`.gitignore` excludes everything under `data/` except the placeholders --
so real data dropped in later, and anything regenerated from it, is
excluded automatically with no ongoing attention needed.

**Data handoff is manual and out-of-band**: the user copies the actual
files to his boss's machine directly (no propagation script -- data is
small, ~150KB raw, one-time handoff, not worth building infrastructure
for).

**Code change required**: three loaders currently read from hardcoded or
repo-relative absolute paths and need to read from a configurable root
instead:

- `standardizedScores/FM100/scripts/loader.py` (`RAW_PATH`,
  `SSVEP_METADATA_PATH`)
- `beh/scripts/loader.py` (`RAW_PATH`, `SSVEP_METADATA_PATH`)
- `ssveps/scripts/analysis.py` (`FILES_DIR`)

All three switch to building their path from one new constant: the value
of the `MET_DASHBOARD_DATA_DIR` environment variable if set, else
`<repo_root>/data`. The relative structure under that root is unchanged
from today's layout, so this is a path-base swap, not a rewrite.

## Dependencies

Fresh, trimmed `pyproject.toml` for `met_dashboard` -- not a copy of this
repo's flat dependency list (which includes `notebook`, `ipykernel`,
`openpyxl`, `requests`, `polars`, none of which the dashboard touches).
Included: `streamlit`, `matplotlib`, `numpy`, `pandas`, `scipy`,
`pingouin` (transitively required via `ssveps/scripts/plotting.py` ->
`reliability.py`), `hotelling` (behavioral Hotelling T^2). The exact set,
including whether `scikit-learn` is needed (possible use in
`beh/scripts/features.py`'s shape-feature computation), is confirmed by
grepping the vendored files' actual imports during implementation rather
than assumed here. `pytest` stays as a dev dependency so the vendored test
suites remain runnable (`uv run pytest`).

## README

Already written (`/home/sebas/projects/met_dashboard/README.md`): what the
repo is, a 5-step quickstart (install `git`+`uv`, clone, `uv sync`, place
data per the `data/` layout or set `MET_DASHBOARD_DATA_DIR`, `uv run
streamlit run dashboard/Home.py`), the data layout, and a one-paragraph
map of the vendored directories.

## Verification

Split between what Claude does (structural, no real data needed) and what
the user does (functional, with real data):

**Claude's part:**
- The app starts without crashing when `data/` is empty, and any resulting
  error is self-explanatory (a `FileNotFoundError` naming the missing
  path) -- no custom error handling is being added beyond what the
  existing code already produces, since the path itself is diagnostic
  enough.
- Confirm `.gitignore` actually excludes files once something is placed
  into each scaffolded `data/` subfolder (checked with placeholder/dummy
  files standing in for real data, then removed -- no real data is needed
  or used for this check).
- The vendored test suites are collectible and any tests that don't depend
  on real data files pass.

**User's part:** once vendoring is complete, the user places real data
into `data/`, runs the full test suites and the dashboard himself, and
confirms results match this repo's before treating the export as done.

## Open items carried into implementation

- Exact trimmed dependency list (Dependencies section above) -- confirmed
  by import audit, not decided in this spec.
- Whether to include a `.gitkeep` file or a small descriptive placeholder
  file per empty `data/` subfolder -- either satisfies the design;
  implementation picks one convention and uses it consistently.
