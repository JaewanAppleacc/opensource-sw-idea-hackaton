import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ANNOTATION_OPS = REPO_ROOT / "scripts" / "annotation_ops"
SCRIPTS_DATA = REPO_ROOT / "scripts" / "data"

for p in (SCRIPTS_ANNOTATION_OPS, SCRIPTS_DATA):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
