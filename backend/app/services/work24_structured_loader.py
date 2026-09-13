"""Loads `data/intake/work24_structured.jsonl` -- the small, hand-built set
of `Work24StructuredPosting` fixtures for the postings currently reachable
through `/postings/home-region-listing` (TASK "Work24 Structured Data +
sLLM Hybrid Audit Pipeline" section 1).

Tracked in git (unlike `data/private/**`): every value in this file is a
short factual field (a number, a category label, a boolean flag) already
visible on the real, public 고용24 posting-detail page for that posting_id
-- never the posting's full free-text paragraphs, which stay private per
REAL_DATA_ACQUISITION_HANDOFF.md. This mirrors how `data/intake/
real_postings.jsonl` already tracks occupation/employment_type/municipality
publicly while `full_text` stays private and gitignored.

`jobs_cd`/`emp_tp_cd` are `None` for every record here: the official
numeric codes are not visible anywhere in the page text this project has
access to (no live Work24 API key), and TASK section 1 is explicit that
these must never be estimated or invented.

A posting_id with no entry in this file (every posting outside the current
tiny research-persona demo set) has no Work24StructuredPosting record at
all -- `load_work24_structured_posting()` returns None for it, and the
caller (`app.api.v1.postings.analyze_by_id`) falls back to the existing,
unchanged `app.services.audit_pipeline.analyze_posting` six-field path.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..models.work24_structured import Work24StructuredPosting

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _work24_structured_path() -> Path:
    override = os.environ.get("WORK24_STRUCTURED_PATH")
    return Path(override) if override else _REPO_ROOT / "data" / "intake" / "work24_structured.jsonl"


@lru_cache(maxsize=8)
def _load_all(path_str: str) -> dict[str, Work24StructuredPosting]:
    path = Path(path_str)
    if not path.exists():
        return {}
    records: dict[str, Work24StructuredPosting] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            posting = Work24StructuredPosting.model_validate(raw)
            records[posting.posting_id] = posting
    return records


def load_work24_structured_posting(posting_id: str) -> Optional[Work24StructuredPosting]:
    return _load_all(str(_work24_structured_path())).get(posting_id)


def clear_work24_structured_cache() -> None:
    """Test-only escape hatch so WORK24_STRUCTURED_PATH overrides take effect mid-suite."""
    _load_all.cache_clear()
