from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import clear_settings_cache  # noqa: E402
from app.datasets.loader import clear_dataset_cache  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.rules.field_rules import clear_rules_cache  # noqa: E402
from app.services.real_postings import clear_real_postings_cache  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BACKEND_DATASET_FIXTURE = BACKEND_ROOT / "app" / "datasets" / "jeonbuk_fixture.jsonl"


def _clear_all_caches() -> None:
    clear_settings_cache()
    clear_dataset_cache()
    clear_rules_cache()
    clear_real_postings_cache()


@pytest.fixture(autouse=True)
def _reset_caches(monkeypatch):
    """Every test starts and ends with fresh, env-var-driven caches.

    Several modules (settings, dataset loader, rule config) cache on first
    read so the app doesn't re-parse files per-request. Tests that monkeypatch
    the relevant env vars must see those changes take effect immediately.
    """
    # Unit tests retain the backend track's stable fixture. Integration tests
    # can explicitly point at the merged data-track corpus.
    monkeypatch.setenv("JEONBUK_DATASET_PATH", str(BACKEND_DATASET_FIXTURE))
    _clear_all_caches()
    yield
    _clear_all_caches()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(fastapi_app)
