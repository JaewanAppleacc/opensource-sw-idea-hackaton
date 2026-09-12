from __future__ import annotations

import pytest

from app.errors import NoMatchFoundError
from app.services.matching import find_matches


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
