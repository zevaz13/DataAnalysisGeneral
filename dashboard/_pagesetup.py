"""Import isolation for the per-project scripts/ modules this dashboard
reuses.

beh/scripts, ssveps/scripts, and standardizedScores/FM100/scripts each have
their own loader.py/plotting.py/etc, independently, by convention (see
beh/README.md's Tests section) -- each is written to be imported with its
own directory on sys.path via a bare `import loader`. That's fine for a
notebook or a single pytest file, but this dashboard is one long-running
process with pages for all three projects, so a second project's
same-named module would otherwise be served from sys.modules' cache
instead of being read from disk.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def use_scripts(rel_path: str, *names: str) -> dict:
    """Import `names` (e.g. "loader", "plotting") from
    <repo_root>/<rel_path>, dropping any already-cached module of the same
    name first and putting that directory first on sys.path. Returns
    {name: module}."""
    for name in names:
        sys.modules.pop(name, None)
    scripts_dir = str(REPO_ROOT / rel_path)
    if scripts_dir in sys.path:
        sys.path.remove(scripts_dir)
    sys.path.insert(0, scripts_dir)
    return {name: __import__(name) for name in names}
