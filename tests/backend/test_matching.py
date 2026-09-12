from __future__ import annotations

from pathlib import Path

import pytest

from app.datasets.loader import clear_dataset_cache
from app.errors import NoMatchFoundError
from app.services.matching import find_matches

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_match_by_occupation_and_employment_type_ranks_exact_matches_first():
    candidates = find_matches("백엔드 개발자", "정규직")
    assert len(candidates) >= 1
    assert candidates[0].matching_fields == ["occupation", "employment_type"]
    assert all("finite curated" in c.description for c in candidates)


def test_match_returns_at_most_three_candidates():
    candidates = find_matches("백엔드 개발자")
    assert len(candidates) <= 3


def test_mismatched_employment_type_is_reported_not_hidden():
    candidates = find_matches("백엔드 개발자", "계약직")
    mismatch_candidate = next(c for c in candidates if c.posting_id == "jb-001")
    assert "employment_type" in mismatch_candidate.mismatch_fields


def test_no_jeonbuk_match_raises_typed_error():
    with pytest.raises(NoMatchFoundError):
        find_matches("존재하지-않는-직업")


def test_merged_data_track_schema_is_adapted_and_metro_rows_are_excluded(monkeypatch):
    merged_dataset = REPO_ROOT / "data" / "postings" / "postings.jsonl"
    monkeypatch.setenv("JEONBUK_DATASET_PATH", str(merged_dataset))
    clear_dataset_cache()

    candidates = find_matches("생산직(제조 조립원)", "정규직")

    assert candidates
    assert all(candidate.region == "jeonbuk" for candidate in candidates)
    assert all(candidate.posting_id.startswith("JB-") for candidate in candidates)
    assert all(candidate.company_name for candidate in candidates)
    assert all(candidate.source_text for candidate in candidates)
    assert all(candidate.is_synthetic is True for candidate in candidates)
