from __future__ import annotations

from typing import Callable, List, Union

import pytest

from app.errors import AnalysisFailedError, ProviderUnavailableError
from app.models.common import FIELD_NAMES
from app.models.posting import PostingInput
from app.providers.mock_provider import MockExtractionProvider
from app.services.audit_pipeline import analyze_posting
from sample_postings import FULLY_SPECIFIED_POSTING, MINIMAL_POSTING_MISSING_MOST_FIELDS, VAGUE_SALARY_POSTING


def _absent_everything() -> dict:
    return {
        "occupation": None,
        "employment_type": None,
        "fields": [{"field": name, "status": "absent"} for name in FIELD_NAMES],
    }


class StubProvider:
    """Returns each payload in sequence (last one repeats), tracking call count."""

    name = "stub"

    def __init__(self, payloads: List[Union[dict, Callable[[], dict]]]):
        self._payloads = payloads
        self.calls = 0

    def extract(self, source_text: str, expected_occupation=None) -> dict:
        self.calls += 1
        payload = self._payloads[min(self.calls - 1, len(self._payloads) - 1)]
        return payload() if callable(payload) else payload


class RaisingProvider:
    name = "raising"

    def __init__(self, exc: Exception):
        self._exc = exc
        self.calls = 0

    def extract(self, source_text: str, expected_occupation=None) -> dict:
        self.calls += 1
        raise self._exc


def test_valid_confirmed_evidence_flows_through_all_six_fields():
    posting = PostingInput(source_text=FULLY_SPECIFIED_POSTING)
    result = analyze_posting(posting, MockExtractionProvider())

    assert set(result.fields.keys()) == set(FIELD_NAMES)
    for name, audited in result.fields.items():
        assert audited.status == "confirmed", name
        assert audited.evidence is not None
        span = audited.evidence
        assert FULLY_SPECIFIED_POSTING[span.start : span.end] == span.text
    assert result.validation_warnings == []
    assert result.verification_actions == []


def test_vague_salary_marker_downgrades_and_creates_action():
    posting = PostingInput(source_text=VAGUE_SALARY_POSTING)
    result = analyze_posting(posting, MockExtractionProvider())

    salary = result.fields["salary"]
    assert salary.status == "vague"
    assert salary.evidence is not None
    assert salary.reason_code == "vague_marker_matched"

    action = next(a for a in result.verification_actions if a.field == "salary")
    assert action.triggered_by_status == "vague"
    assert action.channel == "email"


def test_truly_absent_field_has_no_evidence_and_gets_action():
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)
    result = analyze_posting(posting, MockExtractionProvider())

    salary = result.fields["salary"]
    assert salary.status == "absent"
    assert salary.evidence is None

    action = next(a for a in result.verification_actions if a.field == "salary")
    assert action.triggered_by_status == "absent"
    assert action.channel == "email"


def test_fabricated_evidence_exhausts_retry_and_raises_typed_error():
    def fabricated():
        payload = _absent_everything()
        payload["fields"][0] = {
            "field": "salary",
            "status": "confirmed",
            "evidence_text": "연봉 9,999만원 (완전히 지어낸 문구)",
            "start": 0,
            "end": 15,
        }
        return payload

    provider = StubProvider([fabricated, fabricated])
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)

    with pytest.raises(AnalysisFailedError):
        analyze_posting(posting, provider)
    assert provider.calls == 2  # one initial attempt + exactly one retry


def test_correct_text_wrong_offsets_exhausts_retry_and_raises_typed_error():
    real_text = "서비스 운영 및 관리 업무를 담당합니다"
    wrong_start = 0  # not where real_text actually lives in the source

    def wrong_offsets():
        payload = _absent_everything()
        payload["fields"][1] = {
            "field": "duties",
            "status": "confirmed",
            "evidence_text": real_text,
            "start": wrong_start,
            "end": wrong_start + len(real_text),
        }
        return payload

    provider = StubProvider([wrong_offsets, wrong_offsets])
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)

    with pytest.raises(AnalysisFailedError):
        analyze_posting(posting, provider)
    assert provider.calls == 2


def test_invalid_status_schema_violation_is_never_silently_downgraded():
    def bad_status():
        payload = _absent_everything()
        payload["fields"][0] = {"field": "salary", "status": "external_verified"}
        return payload

    provider = StubProvider([bad_status, bad_status])
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)

    with pytest.raises(AnalysisFailedError):
        analyze_posting(posting, provider)
    assert provider.calls == 2


def test_additional_property_schema_violation_is_rejected():
    def extra_property():
        payload = _absent_everything()
        payload["company_stability_score"] = 5  # not part of the contract
        return payload

    provider = StubProvider([extra_property, extra_property])
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)

    with pytest.raises(AnalysisFailedError):
        analyze_posting(posting, provider)
    assert provider.calls == 2


def test_irrelevant_real_evidence_is_downgraded_to_absent_by_deterministic_rule():
    source = "우리 회사는 전북 전주시에 위치해 있습니다"
    evidence_text = source  # real substring of the source, but irrelevant to salary

    def irrelevant_salary():
        payload = _absent_everything()
        payload["fields"][0] = {
            "field": "salary",
            "status": "confirmed",
            "evidence_text": evidence_text,
            "start": 0,
            "end": len(evidence_text),
        }
        return payload

    provider = StubProvider([irrelevant_salary])
    posting = PostingInput(source_text=source)
    result = analyze_posting(posting, provider)

    salary = result.fields["salary"]
    assert salary.status == "absent"
    assert salary.evidence is None
    assert salary.reason_code == "no_relevant_keyword"
    assert any(w.code == "downgraded_to_absent" and w.field == "salary" for w in result.validation_warnings)


def test_provider_recovers_after_one_retry():
    def bad_status():
        payload = _absent_everything()
        payload["fields"][0] = {"field": "salary", "status": "external_verified"}
        return payload

    good_payload = _absent_everything()
    provider = StubProvider([bad_status, good_payload])
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)

    result = analyze_posting(posting, provider)
    assert provider.calls == 2
    assert result.fields["salary"].status == "absent"


def test_provider_unavailable_propagates_without_retrying():
    provider = RaisingProvider(ProviderUnavailableError("no api key configured"))
    posting = PostingInput(source_text=MINIMAL_POSTING_MISSING_MOST_FIELDS)

    with pytest.raises(ProviderUnavailableError):
        analyze_posting(posting, provider)
    assert provider.calls == 1  # provider unavailability is not a retryable extraction-quality issue
