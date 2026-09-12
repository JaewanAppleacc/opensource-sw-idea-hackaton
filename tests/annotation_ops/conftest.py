import shutil
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ANNOTATION_OPS = REPO_ROOT / "scripts" / "annotation_ops"
SCRIPTS_DATA = REPO_ROOT / "scripts" / "data"
SCRIPTS_ACQUISITION = REPO_ROOT / "scripts" / "acquisition"

for p in (SCRIPTS_ANNOTATION_OPS, SCRIPTS_DATA, SCRIPTS_ACQUISITION):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture()
def real_private_subdir():
    """A uniquely-named, gitignored scratch directory under the actual
    repo's data/private/. Needed by any test exercising --private-dir
    join/gitignore enforcement, since `git check-ignore` can only classify
    paths inside this repository (not an arbitrary tmp_path outside it).
    Synthetic content only; removed after the test.
    """
    subdir = REPO_ROOT / "data" / "private" / f"pytest_tmp_{uuid.uuid4().hex}"
    yield subdir
    shutil.rmtree(subdir, ignore_errors=True)
