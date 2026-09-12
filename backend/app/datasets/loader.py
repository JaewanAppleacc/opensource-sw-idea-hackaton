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

from pydantic import BaseModel, ConfigDict

_DEFAULT_FIXTURE_PATH = Path(__file__).with_name("jeonbuk_fixture.jsonl")


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
            records.append(JeonbukPostingRecord.model_validate(json.loads(line)))
    return records


def load_jeonbuk_dataset() -> List[JeonbukPostingRecord]:
    return _load_from_path(str(_dataset_path()))


def dataset_is_available() -> bool:
    return len(load_jeonbuk_dataset()) > 0


def clear_dataset_cache() -> None:
    """Test-only escape hatch so JEONBUK_DATASET_PATH overrides take effect mid-suite."""
    _load_from_path.cache_clear()
