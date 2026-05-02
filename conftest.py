import sys
from pathlib import Path

# Ensure the repository root is on sys.path so that top-level packages
# (e.g. `packages.contracts`) are importable regardless of which
# subdirectory pytest is collecting from.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
