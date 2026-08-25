# CVD study dashboard

Interactive Streamlit views over the FM100/behavioral/SSVEP analysis code.
This is a thin presentation layer -- every page imports and calls the same
`loader`/`plotting`/`comparisons` functions the corresponding notebook
uses, so nothing here recomputes or duplicates analysis logic. See
`PLANdashboard.md` for the design decisions and `docs/findings.md` for the
results narrative.

## Run it

```
uv run streamlit run dashboard/Home.py
```

Opens at `http://localhost:8501`. Use the sidebar to switch between the
FM100, Behavioral, and SSVEP pages.

## Layout

- `Home.py` -- landing page.
- `pages/1_FM100.py`, `pages/2_Behavioral.py`, `pages/3_SSVEP.py` -- one
  page per analysis line, each with a group/subgroup selector, the
  headline plot(s), and a pairwise significance table.
- `_pagesetup.py` -- `use_scripts(rel_path, *names)`, a small import helper.
  `beh/scripts`, `ssveps/scripts`, and `standardizedScores/FM100/scripts`
  each have their own `loader.py`/`plotting.py`/etc (independently, by
  convention -- see `beh/README.md`'s Tests section), written to be
  imported bare (`import loader`) with their own directory on `sys.path`.
  That collides once more than one is imported in the same long-running
  process, which is exactly what a multi-page Streamlit app does -- this
  helper drops the stale cached module and re-imports from the right
  directory before each page uses it.

## Adding a page

Follow the same pattern: call `use_scripts` with that project's
`scripts/` path and the module names it needs, load data through
`st.cache_data`, build a `categories` list matching the notebooks'
`{"label", "group"/"subgroup"}` shape, and call the existing plotting
functions directly.
