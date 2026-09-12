from __future__ import annotations

from app.providers.mock_provider import MockExtractionProvider
from app.providers.raw import RawExtraction
from sample_postings import FULLY_SPECIFIED_POSTING, MINIMAL_POSTING_MISSING_MOST_FIELDS


def test_mock_provider_is_deterministic():
    provider = MockExtractionProvider()
    first = provider.extract(FULLY_SPECIFIED_POSTING)
    second = provider.extract(FULLY_SPECIFIED_POSTING)
    assert first == second


def test_mock_provider_offsets_match_source_exactly():
    provider = MockExtractionProvider()
    raw = provider.extract(FULLY_SPECIFIED_POSTING)
    validated = RawExtraction.model_validate(raw)  # schema-valid, extra="forbid"
    for field_entry in validated.fields:
        if field_entry.evidence_text is None:
            continue
        actual = FULLY_SPECIFIED_POSTING[field_entry.start : field_entry.end]
        assert actual == field_entry.evidence_text


def test_mock_provider_reports_absent_when_no_anchor_found():
    provider = MockExtractionProvider()
    raw = provider.extract(MINIMAL_POSTING_MISSING_MOST_FIELDS)
    statuses = {f["field"]: f["status"] for f in raw["fields"]}
    assert statuses["salary"] == "absent"
    assert statuses["probation_terms"] == "absent"
    assert statuses["training_or_mentoring"] == "absent"
