# MET Dashboard Standalone Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a standalone, public `met_dashboard` repo containing the Streamlit dashboard and the analysis code it depends on, with no per-subject data committed to it, so the user's boss can clone it, add his own copy of the data, and run it.

**Architecture:** One-time export (not an ongoing sync). Copy the full `scripts/`+`tests/` directories of the four projects the dashboard imports from (`standardizedScores/FM100/`, `beh/`, `ssveps/`, `ssvepBeh/`) plus `dashboard/` itself into `/home/sebas/projects/met_dashboard`, preserving the same relative paths so `_pagesetup.py`'s `use_scripts()` needs no changes. Patch exactly three files (the ones with hardcoded/personal data paths) to read from a `MET_DASHBOARD_DATA_DIR`-configurable root instead. Scaffold an empty, gitignored `data/` tree so the repo documents where data goes without ever holding it.

**Tech Stack:** Python 3.13, `uv`, Streamlit, pandas/numpy/scipy/matplotlib/pingouin/statsmodels/hotelling, pytest.

**Spec:** `docs/superpowers/specs/2026-09-02-met-dashboard-export-design.md`

## Global Constraints

- Target repo: `/home/sebas/projects/met_dashboard` -- already `git init`'d and has a public GitHub remote (`zevaz13/met_dashboard`) set up by the user.
- **Never run `git` commands inside `/home/sebas/projects/met_dashboard`.** The user owns all git operations there. Every task ends with a checkpoint that hands off to the user instead of committing.
- Vendor full `scripts/` + `tests/` directories per project -- not a hand-trimmed subset (spec: safer than maintaining a trimmed copy, ~5,000 total lines either way).
- No per-subject data -- raw or derived, real or placeholder -- may ever be committed to `met_dashboard`. Only the `data/` directory *structure* is tracked.
- `requires-python = ">=3.13"` (matches the source repo).
- Exactly three files get a data-path patch: `standardizedScores/FM100/scripts/loader.py`, `beh/scripts/loader.py`, `ssveps/scripts/analysis.py`. No other vendored file is modified.
- Source repo for copying: `/home/sebas/projects/DataAnalysis` (this repo). Do not modify anything in the source repo as part of this plan.

---

## File Structure

```
/home/sebas/projects/met_dashboard/
  pyproject.toml                              (new)
  README.md                                   (already written)
  .gitignore                                  (new)
  data/                                       (new, scaffolding only)
    standardizedScores/README.md
    manualTest/README.md
    ssveps/files/README.md
  standardizedScores/FM100/
    scripts/{loader,scores,plotting,comparisons}.py   (copied, loader.py patched)
    tests/test_fm100.py                       (copied)
  beh/
    scripts/{loader,features,comparisons,plotting,retest}.py  (copied, loader.py patched)
    tests/test_beh.py                         (copied)
  ssveps/
    scripts/{analysis,loader,build_derived,update_derived,build_troughs,pca,permutation,plotting,reliability,variance}.py  (copied, analysis.py patched)
    tests/test_ssveps.py                      (copied)
  ssvepBeh/
    scripts/{plotting,overlap,correlation,session_reliability}.py  (copied, unmodified)
    tests/test_ssvepbeh.py                    (copied)
  dashboard/
    Home.py, _pagesetup.py, color-wheel.jpg   (copied, unmodified)
    pages/{1_FM100,2_Behavioral,3_SSVEP}.py   (copied, unmodified)
```

---

### Task 1: Dependencies and environment

**Files:**
- Create: `/home/sebas/projects/met_dashboard/pyproject.toml`

**Interfaces:**
- Produces: a synced `uv` environment (`.venv/`) that every later task's `uv run` commands rely on.

- [ ] **Step 1: Write `pyproject.toml`**

Dependency list confirmed by grepping every file slated for vendoring (`grep -hE "^(import|from) "` across all four projects' `scripts/`+`tests/` and `dashboard/`) for third-party names, matched against this repo's own `pyproject.toml` version floors:

```toml
[project]
name = "met-dashboard"
version = "0.1.0"
description = "Standalone Streamlit dashboard for the MET colorblindness study"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "hotelling>=0.5.0",
    "matplotlib>=3.11.1",
    "numpy>=2.5.2",
    "pandas>=3.0.5",
    "pingouin>=0.6.1",
    "scipy>=1.18.0",
    "statsmodels>=0.14.6",
    "streamlit>=1.62.0",
]

[dependency-groups]
dev = [
    "pytest>=9.1.1",
]
```

- [ ] **Step 2: Sync the environment**

Run: `cd /home/sebas/projects/met_dashboard && uv sync`
Expected: completes with no errors, creates `.venv/` and `uv.lock`.

- [ ] **Step 3: Checkpoint (user commit)**

Do not run git commands. Tell the user: "`pyproject.toml`, `uv.lock`, and `.venv/` are set up in `met_dashboard` -- ready for you to `git add pyproject.toml uv.lock` and commit whenever you'd like (`.venv/` will be gitignored in Task 2)."

---

### Task 2: Data scaffolding and `.gitignore`

**Files:**
- Create: `/home/sebas/projects/met_dashboard/.gitignore`
- Create: `/home/sebas/projects/met_dashboard/data/standardizedScores/README.md`
- Create: `/home/sebas/projects/met_dashboard/data/manualTest/README.md`
- Create: `/home/sebas/projects/met_dashboard/data/ssveps/files/README.md`

**Interfaces:**
- Produces: the `data/` directory tree that Tasks 3-5's patched loaders will read from (`data/standardizedScores/`, `data/manualTest/`, `data/ssveps/files/`), and a `.gitignore` rule verified to exclude everything placed under `data/` except the `README.md` placeholders.

- [ ] **Step 1: Create the scaffolding directories with placeholder READMEs**

```bash
mkdir -p /home/sebas/projects/met_dashboard/data/standardizedScores
mkdir -p /home/sebas/projects/met_dashboard/data/manualTest
mkdir -p /home/sebas/projects/met_dashboard/data/ssveps/files
```

`data/standardizedScores/README.md`:
```markdown
Place `repeatedSessionsPY.txt` in this folder.
```

`data/manualTest/README.md`:
```markdown
Place `behavioral_table.csv` in this folder.
```

`data/ssveps/files/README.md`:
```markdown
Place these files in this folder: `metadata.csv`, `runmap.csv`,
`baselines.csv`, `subject_troughs.csv`, `group_troughs.csv`, `grid.json`.
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
# Python
__pycache__/
*.pyc
*.pyo

# uv / venv
.venv/

# OS
.DS_Store

# Data -- the folder structure is tracked (README.md placeholders below),
# actual data (raw or derived, real or test) is never committed.
data/**
!data/**/
!data/**/README.md
```

- [ ] **Step 3: Verify the ignore rule actually excludes data, using dummy files (no real data used or needed)**

```bash
cd /home/sebas/projects/met_dashboard
touch data/standardizedScores/repeatedSessionsPY.txt
touch data/manualTest/behavioral_table.csv
touch data/ssveps/files/metadata.csv data/ssveps/files/runmap.csv
git status --porcelain
```

Expected: the four dummy files do **not** appear in `git status --porcelain` output (nothing listed as untracked for them); only genuinely new tracked-candidate files (like `.gitignore` itself, and the `README.md` placeholders if not yet committed) show up.

- [ ] **Step 4: Remove the dummy files**

```bash
rm /home/sebas/projects/met_dashboard/data/standardizedScores/repeatedSessionsPY.txt
rm /home/sebas/projects/met_dashboard/data/manualTest/behavioral_table.csv
rm /home/sebas/projects/met_dashboard/data/ssveps/files/metadata.csv
rm /home/sebas/projects/met_dashboard/data/ssveps/files/runmap.csv
```

- [ ] **Step 5: Checkpoint (user commit)**

Do not run git commands. Tell the user: "`.gitignore` and the empty `data/` scaffolding (with `README.md` placeholders) are ready in `met_dashboard`, and I verified dummy files dropped into each folder are correctly ignored. Ready for you to commit."

---

### Task 3: Vendor `standardizedScores/FM100`

**Files:**
- Create: `/home/sebas/projects/met_dashboard/standardizedScores/FM100/scripts/{loader,scores,plotting,comparisons}.py`
- Create: `/home/sebas/projects/met_dashboard/standardizedScores/FM100/tests/test_fm100.py`
- Modify (post-copy): `standardizedScores/FM100/scripts/loader.py`'s `RAW_PATH`/`SSVEP_METADATA_PATH` constants

**Interfaces:**
- Consumes: `data/standardizedScores/`, `data/ssveps/files/` from Task 2; the synced environment from Task 1.
- Produces: `loader.load_fm100_raw()` now resolves against `MET_DASHBOARD_DATA_DIR` (or `<repo_root>/data` by default) instead of a hardcoded personal path -- later tasks don't consume this directly, but it establishes the pattern Tasks 4-5 repeat.

- [ ] **Step 1: Copy the source files**

```bash
mkdir -p /home/sebas/projects/met_dashboard/standardizedScores/FM100/scripts
mkdir -p /home/sebas/projects/met_dashboard/standardizedScores/FM100/tests
cp /home/sebas/projects/DataAnalysis/standardizedScores/FM100/scripts/{loader,scores,plotting,comparisons}.py \
   /home/sebas/projects/met_dashboard/standardizedScores/FM100/scripts/
cp /home/sebas/projects/DataAnalysis/standardizedScores/FM100/tests/test_fm100.py \
   /home/sebas/projects/met_dashboard/standardizedScores/FM100/tests/
```

- [ ] **Step 2: Patch `loader.py`'s data paths**

In `/home/sebas/projects/met_dashboard/standardizedScores/FM100/scripts/loader.py`, replace:

```python
RAW_PATH = "/home/sebas/data/standardizedScores/repeatedSessionsPY.txt"

# ssveps/files/metadata.csv, three levels up from this file's directory
# (standardizedScores/FM100/scripts/ -> repo root -> ssveps/files/).
SSVEP_METADATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ssveps", "files", "metadata.csv")
```

with:

```python
# Data lives outside this repo's git history (per-subject data is never
# committed) -- MET_DASHBOARD_DATA_DIR overrides where it's found, defaulting
# to <repo_root>/data (standardizedScores/FM100/scripts/ -> repo root is
# three levels up).
DATA_DIR = os.environ.get(
    "MET_DASHBOARD_DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"),
)

RAW_PATH = os.path.join(DATA_DIR, "standardizedScores", "repeatedSessionsPY.txt")
SSVEP_METADATA_PATH = os.path.join(DATA_DIR, "ssveps", "files", "metadata.csv")
```

- [ ] **Step 3: Run the test suite and confirm it fails informatively, not incorrectly**

```bash
cd /home/sebas/projects/met_dashboard
uv run pytest standardizedScores/FM100/tests -q
```

Expected: **0 collection errors** (every test is discovered, no `ImportError`/`ModuleNotFoundError`). Most tests fail (there's no real data in `data/` yet -- that's expected, the user adds it later), but every failure traces back to a `FileNotFoundError` (or pandas' wrapping of one) naming a path under `.../met_dashboard/data/standardizedScores/...` or `.../met_dashboard/data/ssveps/files/metadata.csv` -- **not** `/home/sebas/data/...`. That confirms the patch is wired correctly even though there's no data to actually pass against yet.

- [ ] **Step 4: Checkpoint (user commit)**

Do not run git commands. Tell the user: "FM100's `scripts/` and `tests/` are vendored into `met_dashboard`, `loader.py` now reads from `MET_DASHBOARD_DATA_DIR`/`data/`, and the test suite fails only on missing data (confirmed by the error paths), not on the code itself. Ready for you to commit."

---

### Task 4: Vendor `beh`

**Files:**
- Create: `/home/sebas/projects/met_dashboard/beh/scripts/{loader,features,comparisons,plotting,retest}.py`
- Create: `/home/sebas/projects/met_dashboard/beh/tests/test_beh.py`
- Modify (post-copy): `beh/scripts/loader.py`'s `RAW_PATH`/`SSVEP_METADATA_PATH` constants

**Interfaces:**
- Consumes: `data/manualTest/`, `data/ssveps/files/` from Task 2; the synced environment from Task 1.
- Produces: `loader.load_behavioral()` resolves against `MET_DASHBOARD_DATA_DIR`, same pattern as Task 3.

- [ ] **Step 1: Copy the source files**

```bash
mkdir -p /home/sebas/projects/met_dashboard/beh/scripts
mkdir -p /home/sebas/projects/met_dashboard/beh/tests
cp /home/sebas/projects/DataAnalysis/beh/scripts/{loader,features,comparisons,plotting,retest}.py \
   /home/sebas/projects/met_dashboard/beh/scripts/
cp /home/sebas/projects/DataAnalysis/beh/tests/test_beh.py \
   /home/sebas/projects/met_dashboard/beh/tests/
```

- [ ] **Step 2: Patch `loader.py`'s data paths**

In `/home/sebas/projects/met_dashboard/beh/scripts/loader.py`, replace:

```python
RAW_PATH = "/home/sebas/data/manualTest/behavioral_table.csv"

# ssveps/files/metadata.csv, two levels up from this file's directory
# (beh/scripts/ -> repo root -> ssveps/files/).
SSVEP_METADATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ssveps", "files", "metadata.csv")
```

with:

```python
# Data lives outside this repo's git history (per-subject data is never
# committed) -- MET_DASHBOARD_DATA_DIR overrides where it's found, defaulting
# to <repo_root>/data (beh/scripts/ -> repo root is two levels up).
DATA_DIR = os.environ.get(
    "MET_DASHBOARD_DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "data"),
)

RAW_PATH = os.path.join(DATA_DIR, "manualTest", "behavioral_table.csv")
SSVEP_METADATA_PATH = os.path.join(DATA_DIR, "ssveps", "files", "metadata.csv")
```

- [ ] **Step 3: Run the test suite and confirm it fails informatively**

```bash
cd /home/sebas/projects/met_dashboard
uv run pytest beh/tests -q
```

Expected: same as Task 3 Step 3 -- 0 collection errors, failures trace to `FileNotFoundError` naming `.../met_dashboard/data/manualTest/behavioral_table.csv` or `.../data/ssveps/files/metadata.csv`, never the old `/home/sebas/data/...` path.

- [ ] **Step 4: Checkpoint (user commit)**

Do not run git commands. Tell the user: "`beh`'s `scripts/` and `tests/` are vendored, `loader.py` patched the same way as FM100's. Ready for you to commit."

---

### Task 5: Vendor `ssveps`

**Files:**
- Create: `/home/sebas/projects/met_dashboard/ssveps/scripts/{analysis,loader,build_derived,update_derived,build_troughs,pca,permutation,plotting,reliability,variance}.py`
- Create: `/home/sebas/projects/met_dashboard/ssveps/tests/test_ssveps.py`
- Modify (post-copy): `ssveps/scripts/analysis.py`'s `FILES_DIR` constant

**Interfaces:**
- Consumes: `data/ssveps/files/` from Task 2; the synced environment from Task 1.
- Produces: `analysis.py`'s `load_runmap`/`load_baselines`/`load_metadata`/`load_grid_axes` now read from `MET_DASHBOARD_DATA_DIR`/`ssveps/files/` -- consumed by `dashboard/pages/3_SSVEP.py` in Task 7.

Note: `build_derived.py`/`update_derived.py`'s `RAW_DIR = "/home/sebas/data/ssveps"` (for rebuilding these CSVs from raw `.mat` files) and `test_ssveps.py`'s `RAW_DIR = Path("/home/sebas/data/ssveps")` are **not** patched -- per the spec, only `analysis.py`'s `FILES_DIR` is in scope. These become inert on any machine but this one; the dashboard never calls them.

- [ ] **Step 1: Copy the source files**

```bash
mkdir -p /home/sebas/projects/met_dashboard/ssveps/scripts
mkdir -p /home/sebas/projects/met_dashboard/ssveps/tests
cp /home/sebas/projects/DataAnalysis/ssveps/scripts/{analysis,loader,build_derived,update_derived,build_troughs,pca,permutation,plotting,reliability,variance}.py \
   /home/sebas/projects/met_dashboard/ssveps/scripts/
cp /home/sebas/projects/DataAnalysis/ssveps/tests/test_ssveps.py \
   /home/sebas/projects/met_dashboard/ssveps/tests/
```

- [ ] **Step 2: Patch `analysis.py`'s data path**

In `/home/sebas/projects/met_dashboard/ssveps/scripts/analysis.py`, replace:

```python
FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "files")
```

with:

```python
# Data lives outside this repo's git history (per-subject data is never
# committed) -- MET_DASHBOARD_DATA_DIR overrides where it's found, defaulting
# to <repo_root>/data (ssveps/scripts/ -> repo root is two levels up).
DATA_DIR = os.environ.get(
    "MET_DASHBOARD_DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "data"),
)
FILES_DIR = os.path.join(DATA_DIR, "ssveps", "files")
```

- [ ] **Step 3: Run the test suite and confirm it fails informatively**

```bash
cd /home/sebas/projects/met_dashboard
uv run pytest ssveps/tests -q
```

Expected: 0 collection errors. Most tests fail on `FileNotFoundError` naming `.../met_dashboard/data/ssveps/files/...` (proving the `analysis.py` patch works). `test_loader_reads_runmap_green_first` and any other test using the unpatched `RAW_DIR` will fail naming `/home/sebas/data/ssveps/...` instead -- that's expected and out of scope (noted above), not a regression to fix here.

- [ ] **Step 4: Checkpoint (user commit)**

Do not run git commands. Tell the user: "`ssveps`'s `scripts/` and `tests/` are vendored, `analysis.py` patched. A couple of tests that read raw `.mat` files directly (`RAW_DIR`) will always fail outside this machine -- that's expected and unrelated to the dashboard, which never calls those functions. Ready for you to commit."

---

### Task 6: Vendor `ssvepBeh`

**Files:**
- Create: `/home/sebas/projects/met_dashboard/ssvepBeh/scripts/{plotting,overlap,correlation,session_reliability}.py`
- Create: `/home/sebas/projects/met_dashboard/ssvepBeh/tests/test_ssvepbeh.py`

**Interfaces:**
- Consumes: `beh/scripts/loader.py` (Task 4) and `ssveps/scripts/analysis.py` (Task 5) at runtime, via `dashboard/_pagesetup.py`'s `use_scripts`.
- Produces: `plotting.plot_grids_with_clicks`, consumed by `dashboard/pages/3_SSVEP.py` in Task 7.

No data-path patch needed here -- `ssvepBeh/scripts/plotting.py` only bare-imports `overlap` (no file I/O of its own); it receives data through function arguments from the dashboard page, which gets that data from the already-patched `beh`/`ssveps` loaders.

- [ ] **Step 1: Copy the source files**

```bash
mkdir -p /home/sebas/projects/met_dashboard/ssvepBeh/scripts
mkdir -p /home/sebas/projects/met_dashboard/ssvepBeh/tests
cp /home/sebas/projects/DataAnalysis/ssvepBeh/scripts/{plotting,overlap,correlation,session_reliability}.py \
   /home/sebas/projects/met_dashboard/ssvepBeh/scripts/
cp /home/sebas/projects/DataAnalysis/ssvepBeh/tests/test_ssvepbeh.py \
   /home/sebas/projects/met_dashboard/ssvepBeh/tests/
```

- [ ] **Step 2: Run the test suite and confirm it fails informatively**

```bash
cd /home/sebas/projects/met_dashboard
uv run pytest ssvepBeh/tests -q
```

Expected: 0 collection errors. Tests that call `beh_loader.load_behavioral()` fail on the same `FileNotFoundError` pattern as Task 4 (proving the shared `beh` loader patch is picked up correctly here too).

- [ ] **Step 3: Checkpoint (user commit)**

Do not run git commands. Tell the user: "`ssvepBeh`'s `scripts/` and `tests/` are vendored, no patch needed. Ready for you to commit."

---

### Task 7: Vendor `dashboard/`

**Files:**
- Create: `/home/sebas/projects/met_dashboard/dashboard/Home.py`
- Create: `/home/sebas/projects/met_dashboard/dashboard/_pagesetup.py`
- Create: `/home/sebas/projects/met_dashboard/dashboard/color-wheel.jpg`
- Create: `/home/sebas/projects/met_dashboard/dashboard/pages/1_FM100.py`
- Create: `/home/sebas/projects/met_dashboard/dashboard/pages/2_Behavioral.py`
- Create: `/home/sebas/projects/met_dashboard/dashboard/pages/3_SSVEP.py`

**Interfaces:**
- Consumes: every vendored `scripts/` directory from Tasks 3-6, via `_pagesetup.py`'s `use_scripts(rel_path, *names)` (unchanged signature, unchanged behavior -- relies only on the preserved relative directory layout).
- Produces: the running Streamlit app, consumed by Task 8's verification.

Note: `dashboard/README.md` from the source repo is **not** copied -- `met_dashboard`'s own top-level `README.md` (already written) replaces it.

- [ ] **Step 1: Copy the source files**

```bash
mkdir -p /home/sebas/projects/met_dashboard/dashboard/pages
cp /home/sebas/projects/DataAnalysis/dashboard/Home.py \
   /home/sebas/projects/DataAnalysis/dashboard/_pagesetup.py \
   /home/sebas/projects/DataAnalysis/dashboard/color-wheel.jpg \
   /home/sebas/projects/met_dashboard/dashboard/
cp /home/sebas/projects/DataAnalysis/dashboard/pages/1_FM100.py \
   /home/sebas/projects/DataAnalysis/dashboard/pages/2_Behavioral.py \
   /home/sebas/projects/DataAnalysis/dashboard/pages/3_SSVEP.py \
   /home/sebas/projects/met_dashboard/dashboard/pages/
```

- [ ] **Step 2: Confirm every vendored file is byte-identical to its source**

```bash
diff /home/sebas/projects/DataAnalysis/dashboard/Home.py /home/sebas/projects/met_dashboard/dashboard/Home.py
diff /home/sebas/projects/DataAnalysis/dashboard/_pagesetup.py /home/sebas/projects/met_dashboard/dashboard/_pagesetup.py
diff /home/sebas/projects/DataAnalysis/dashboard/pages/1_FM100.py /home/sebas/projects/met_dashboard/dashboard/pages/1_FM100.py
diff /home/sebas/projects/DataAnalysis/dashboard/pages/2_Behavioral.py /home/sebas/projects/met_dashboard/dashboard/pages/2_Behavioral.py
diff /home/sebas/projects/DataAnalysis/dashboard/pages/3_SSVEP.py /home/sebas/projects/met_dashboard/dashboard/pages/3_SSVEP.py
cmp /home/sebas/projects/DataAnalysis/dashboard/color-wheel.jpg /home/sebas/projects/met_dashboard/dashboard/color-wheel.jpg
```

Expected: no output from any command (no differences).

- [ ] **Step 3: Checkpoint (user commit)**

Do not run git commands. Tell the user: "`dashboard/` is vendored unchanged. Ready for you to commit."

---

### Task 8: End-to-end verification

**Files:** none (verification only).

**Interfaces:**
- Consumes: everything from Tasks 1-7.

- [ ] **Step 1: Launch the app on a scratch port**

```bash
cd /home/sebas/projects/met_dashboard
uv run streamlit run dashboard/Home.py --server.headless true --server.port 8599 > /tmp/met_dashboard_smoke.log 2>&1 &
sleep 5
```

- [ ] **Step 2: Hit all four routes**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8599/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8599/FM100
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8599/Behavioral
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8599/SSVEP
```

Expected: `200` for all four (Streamlit serves the page shell at 200 even when the page body raises -- the shell itself loading confirms there's no import-time/syntax error in any page).

- [ ] **Step 3: Confirm the in-page errors (no data yet) are the informative kind**

```bash
grep -o "FileNotFoundError[^<]*" /tmp/met_dashboard_smoke.log | head -5
```

Expected: any matches reference a path under `/home/sebas/projects/met_dashboard/data/...` -- confirming that even end-to-end through the full page-render path (not just direct module calls), the patched loaders are being hit and are pointed at the right (empty, scaffolded) place. Note for the user: with no real data in `data/`, every page is expected to show a "file not found" message rather than plots -- that's expected, and disappears once you add the real data.

- [ ] **Step 4: Stop the server**

```bash
kill %1
```

- [ ] **Step 5: Report to the user**

Tell the user: "All four routes load without a broken page shell, and every error observed is a `FileNotFoundError` pointing at the empty `data/` scaffolding, not a code bug. The export is structurally complete. Next: copy your real data into `met_dashboard/data/` per the `README.md`, re-run `uv run pytest` across all four test suites and `uv run streamlit run dashboard/Home.py` yourself, and confirm the numbers match what you see in `DataAnalysis`. Once you're satisfied, commit and push whenever you're ready."

---

## Self-Review

**Spec coverage:**
- Repo location, no-Claude-git-commands, public repo -> Global Constraints. ✓
- Full `scripts/`+`tests/` vendoring, not trimmed -> File Structure + Tasks 3-7. ✓
- No per-subject data (raw or derived) in git -> Task 2. ✓
- Three-file data-path patch via `MET_DASHBOARD_DATA_DIR` -> Tasks 3, 4, 5. ✓
- Trimmed `pyproject.toml`, confirmed by import audit -> Task 1 (exact list derived from a real grep, not assumed). ✓
- README already written -> noted, not re-done. ✓
- Verification split (Claude: structural; user: functional with real data) -> Task 8 + each task's test step; Step 5 hands off the real-data verification explicitly. ✓

**Placeholder scan:** no TBD/TODO; every step has literal code/commands; no "similar to Task N" shortcuts (each patch is written out in full per task even though the pattern repeats, since an implementer may work tasks out of order).

**Type/name consistency:** `MET_DASHBOARD_DATA_DIR` and `DATA_DIR` spelled identically across Tasks 3/4/5; `use_scripts(rel_path, *names)` signature referenced in Task 7 matches `_pagesetup.py`'s actual definition (verified against source during design).
