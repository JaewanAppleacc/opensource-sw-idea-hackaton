from __future__ import annotations

import pytest

from app.services.evidence import EvidenceMismatchError, validate_evidence_span

SOURCE = "급여: 연봉 3,200만원 (세전)\n수습기간: 3개월"


def test_valid_span_passes():
    start = SOURCE.find("연봉 3,200만원")
    end = start + len("연봉 3,200만원")
    validate_evidence_span(SOURCE, "연봉 3,200만원", start, end)  # should not raise


def test_fabricated_evidence_not_in_source_is_rejected():
    with pytest.raises(EvidenceMismatchError):
        validate_evidence_span(SOURCE, "연봉 5,000만원", 4, 15)


def test_correct_text_at_wrong_offsets_is_rejected():
    correct_text = "3개월"
    wrong_start = SOURCE.find("연봉")  # a valid index into SOURCE, but not where "3개월" lives
    with pytest.raises(EvidenceMismatchError):
        validate_evidence_span(SOURCE, correct_text, wrong_start, wrong_start + len(correct_text))


def test_out_of_bounds_offsets_are_rejected():
    with pytest.raises(EvidenceMismatchError):
        validate_evidence_span(SOURCE, "x", len(SOURCE) - 1, len(SOURCE) + 10)


def test_end_not_greater_than_start_is_rejected():
    with pytest.raises(EvidenceMismatchError):
        validate_evidence_span(SOURCE, "", 5, 5)
