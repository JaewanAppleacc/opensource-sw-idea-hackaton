import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ACQUISITION = REPO_ROOT / "scripts" / "acquisition"

if str(SCRIPTS_ACQUISITION) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ACQUISITION))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
