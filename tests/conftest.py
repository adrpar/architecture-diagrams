import sys
import pathlib

# Ensure project root (containing arch_diagrams) is on sys.path when tests executed via `uv run`.
ROOT = pathlib.Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
