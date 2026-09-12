"""Adapter over the curated Jeonbuk posting dataset.

Reads a local JSONL file. Defaults to this track's small synthetic fixture
(jeonbuk_fixture.jsonl) so /postings/match works with zero setup. Set
JEONBUK_DATASET_PATH to point at the data track's final curated file
instead -- the API and matching logic do not change either way.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator

_REPO_ROOT = Path(__file__).resolve().parents[3]
_INTEGRATED_DATASET_PATH = _REPO_ROOT / "data" / "postings" / "postings.jsonl"
_BACKEND_FIXTURE_PATH = Path(__file__).with_name("jeonbuk_fixture.jsonl")
_DEFAULT_FIXTURE_PATH = (
    _INTEGRATED_DATASET_PATH if _INTEGRATED_DATASET_PATH.exists() else _BACKEND_FIXTURE_PATH
)


class JeonbukPostingRecord(BaseModel):
    # extra="ignore": the data track's final file may carry additional
    # columns (collection date, source name, etc.) this MVP matcher does
    # not need.
    model_config = ConfigDict(extra="ignore")

    posting_id: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    region: str = "jeonbuk"
    municipality: Optional[str] = None
    occupation: str
    employment_type: str
    company_name: Optional[str] = None
    full_text: Optional[str] = None
    source_name: Optional[str] = None
    is_synthetic: bool = False

    @model_validator(mode="before")
    @classmethod
    def _adapt_data_track_record(cls, value: object) -> object:
        """Accept both the backend fixture and the data-track JSONL schema."""
        if not isinstance(value, dict):
            return value
        adapted = dict(value)
        adapted.setdefault("region", adapted.get("region_group", "jeonbuk"))
        adapted.setdefault("source_url", adapted.get("source_id_url"))
        adapted.setdefault("source_id", adapted.get("source_name"))
        adapted.setdefault(
            "is_synthetic",
            adapted.get("source_name") == "synthetic_fixture_v1"
            or bool(adapted.get("synthetic_test_fixture")),
        )
        return adapted


def _dataset_path() -> Path:
    override = os.environ.get("JEONBUK_DATASET_PATH")
    return Path(override) if override else _DEFAULT_FIXTURE_PATH


@lru_cache(maxsize=8)
def _load_from_path(path_str: str) -> List[JeonbukPostingRecord]:
    path = Path(path_str)
    if not path.exists():
        return []
    records: List[JeonbukPostingRecord] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = JeonbukPostingRecord.model_validate(json.loads(line))
            # The integrated data file contains both members of each matched
            # pair.  This loader is intentionally Jeonbuk-only so a metro row
            # can never be returned as a local candidate through a default.
            if record.region.strip().lower() == "jeonbuk":
                records.append(record)
    return records


def load_jeonbuk_dataset() -> List[JeonbukPostingRecord]:
    return _load_from_path(str(_dataset_path()))


def dataset_is_available() -> bool:
    return len(load_jeonbuk_dataset()) > 0


def clear_dataset_cache() -> None:
    """Test-only escape hatch so JEONBUK_DATASET_PATH overrides take effect mid-suite."""
    _load_from_path.cache_clear()
