# DataAnalysis

General-purpose workspace for ad-hoc data analysis. One shared Python environment for every project, so a new dataset never needs its own venv setup.

## Environment

Managed entirely with `uv`. Never use `pip`.

```bash
uv add <package>          # add a dependency
uv run python <script>    # run a script
uv run jupyter notebook   # launch notebooks
```

## Structure

Each dataset/topic gets its own top-level directory:

```
<project-name>/
  README.md      # what the data is, where raw data lives, notes
  notebooks/
  scripts/
  data/          # optional, only if kept in-repo (added to .gitignore then)
```

Raw data always lives outside the repo. Where intermediate/processed data is stored is decided per project.

See `PLAN<project>.md` (repo root, one per project) for current milestones,
`docs/findings.md` for the results narrative, and **`docs/index.md` for a
full map of every project, notebook, and doc in this repo.**
