"""Skip collecting tests whose module-level imports require the vendored
minesweeper_solver submodule when it isn't checked out (e.g. in CI without
`git submodule update --init`). Marker-based deselection isn't enough: pytest
still *imports* every test module during collection, and these import
solver_bridge at module scope.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOLVER_SRC = _REPO_ROOT / 'vendor' / 'minesweeper_solver' / 'src'

collect_ignore = []
if not _SOLVER_SRC.exists():
    collect_ignore += ['test_solver_bridge.py', 'test_recorder.py']
