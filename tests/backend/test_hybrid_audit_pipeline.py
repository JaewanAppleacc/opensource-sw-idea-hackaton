from __future__ import annotations

from typing import Callable, List, Union

import pytest

from app.errors import AnalysisFailedError
from app.models.posting import PostingInput
from app.models.work24_structured import Work24StructuredPosting
from app.services.hybrid_audit_pipeline import analyze_posting_hybrid


def _structured(**overrides) -> Work24StructuredPosting:
    base = dict(
        posting_id="TEST-01",
        occupation_name="테스트 직종",
        employment_type="정규직",
        salary_type="연봉",
        salary_min=30_000_000,
        salary_max=40_000_000,
        weekly_hours=40.0,
        detailed_work_hours="주 5일 근무",
    )
    base.update(overrides)
    return Work24StructuredPosting(**base)


def _absent_four() -> dict:
    return {
        "fields": [
            {"field": name, "status": "absent"}
            for name in ("duties", "tools_or_skills", "training_or_mentoring", "probation_terms")
        ]
    }


class StubFreeTextProvider:
    """Same call-count/sequence pattern as test_audit_pipeline.py's StubProvider,
    but implementing `extract_free_text` (the hybrid pipeline's provider
    interface) instead of `extract`."""

    name = "stub_free_text"

    def __init__(self, payloads: List[Union[dict, Callable[[], dict]]]):
        self._payloads = payloads
        self.calls = 0
        self.last_source_text: str | None = None

    def extract_free_text(self, source_text: str, expected_occupation=None) -> dict:
        self.calls += 1
        self.last_source_text = source_text
        payload = self._payloads[min(self.calls - 1, len(self._payloads) - 1)]
        return payload() if callable(payload) else payload


def _with_field(base: dict, field: str, status: str, evidence_text: str | None, source: str) -> dict:
    payload = {"fields": [dict(f) for f in base["fields"]]}
    for f in payload["fields"]:
        if f["field"] == field:
            f["status"] = status
            if evidence_text is not None:
                start = source.index(evidence_text)
                f.update({"evidence_text": evidence_text, "start": start, "end": start + len(evidence_text)})
    return payload


# --- 1/2. structured salary/employment_type never touch the provider ---


def test_structured_salary_and_employment_type_never_call_the_provider_for_those_fields():
    structured = _structured()
    provider = StubFreeTextProvider([_absent_four()])
    posting = PostingInput(source_text="담당업무: 아무 내용 없음\n")

    result = analyze_posting_hybrid(posting, structured, provider)

    salary = result.fields["salary"]
    employment_type = result.fields["employment_type"]
    assert salary.provenance == "WORK24_STRUCTURED"
    assert salary.status == "confirmed"
    assert employment_type.provenance == "WORK24_STRUCTURED"
    assert employment_type.status == "confirmed"
    # The provider was only ever asked for the four free-text fields --
    # RawFreeTextExtraction would itself reject salary/employment_type if
    # the provider tried to report them (see test below).
    assert provider.calls == 1


def test_provider_returning_salary_field_is_a_schema_violation():
    structured = _structured()
    bad_payload = {
        "fields": [
            {"field": "duties", "status": "absent"},
            {"field": "tools_or_skills", "status": "absent"},
            {"field": "training_or_mentoring", "status": "absent"},
            {"field": "probation_terms", "status": "absent"},
            {"field": "salary", "status": "confirmed", "evidence_text": "x", "start": 0, "end": 1},
        ]
    }
    provider = StubFreeTextProvider([bad_payload, bad_payload])
    posting = PostingInput(source_text="x" * 10)

    with pytest.raises(AnalysisFailedError):
        analyze_posting_hybrid(posting, structured, provider)
    assert provider.calls == 2  # one initial attempt + exactly one retry


# --- 3. only the four free-text fields are ever requested/accepted ---


def test_only_four_free_text_fields_accepted_from_provider():
    structured = _structured()
    provider = StubFreeTextProvider([_absent_four()])
    posting = PostingInput(source_text="아무 내용")

    result = analyze_posting_hybrid(posting, structured, provider)
    assert set(result.fields.keys()) == {
        "salary",
        "employment_type",
        "duties",
        "tools_or_skills",
        "training_or_mentoring",
        "probation_terms",
    }
    for name in ("duties", "tools_or_skills", "training_or_mentoring", "probation_terms"):
        assert result.fields[name].provenance == "SLM_EXTRACTED"


# --- 4. "OJT 실시" confirmed -> downgraded to vague ---


def test_ojt_short_phrase_confirmed_by_slm_is_downgraded_to_vague():
    structured = _structured()
    source = "교육: OJT 실시\n"
    payload = _with_field(_absent_four(), "training_or_mentoring", "confirmed", "OJT 실시", source)
    provider = StubFreeTextProvider([payload])
    posting = PostingInput(source_text=source)

    result = analyze_posting_hybrid(posting, structured, provider)
    field = result.fields["training_or_mentoring"]
    assert field.status == "vague"
    assert field.provenance == "SLM_EXTRACTED"
    assert any(w.code == "downgraded_to_vague" and w.field == "training_or_mentoring" for w in result.validation_warnings)


# --- 5. "회사 내규에 따름" for probation -> vague ---


def test_probation_company_policy_phrase_is_vague():
    structured = _structured()
    source = "수습: 수습기간 중 급여는 회사 내규에 따름\n"
    payload = _with_field(_absent_four(), "probation_terms", "confirmed", "수습기간 중 급여는 회사 내규에 따름", source)
    provider = StubFreeTextProvider([payload])
    posting = PostingInput(source_text=source)

    result = analyze_posting_hybrid(posting, structured, provider)
    field = result.fields["probation_terms"]
    assert field.status == "vague"
    assert field.reason_code == "vague_marker_matched"


# --- 6. evidence substring verification still applies ---


def test_fabricated_evidence_exhausts_retry_and_raises_typed_error():
    structured = _structured()
    source = "담당업무: 실제 업무 내용\n"

    def fabricated():
        return _with_field(_absent_four(), "duties", "confirmed", "완전히 지어낸 문구", "완전히 지어낸 문구")

    provider = StubFreeTextProvider([fabricated, fabricated])
    posting = PostingInput(source_text=source)

    with pytest.raises(AnalysisFailedError):
        analyze_posting_hybrid(posting, structured, provider)
    assert provider.calls == 2


# --- 7. structured/text salary conflict surfaces as a validation warning ---


def test_structured_text_salary_conflict_is_reported_as_a_warning_not_a_new_status():
    structured = _structured(salary_min=25_000_000, salary_max=30_000_000)
    source = "급여: 연봉 회사 내규에 따름\n"
    provider = StubFreeTextProvider([_absent_four()])
    posting = PostingInput(source_text=source)

    result = analyze_posting_hybrid(posting, structured, provider)
    # The existing three-value status contract is untouched -- salary is
    # still exactly "confirmed" (from the structured registry).
    assert result.fields["salary"].status == "confirmed"
    conflict = next(w for w in result.validation_warnings if w.code == "structured_text_conflict")
    assert conflict.field == "salary"


def test_no_conflict_warning_when_text_and_structured_salary_agree():
    structured = _structured(salary_type="연봉", salary_min=30_000_000, salary_max=40_000_000)
    source = "급여: 연봉 3,000만원 ~ 4,000만원\n"
    provider = StubFreeTextProvider([_absent_four()])
    posting = PostingInput(source_text=source)

    result = analyze_posting_hybrid(posting, structured, provider)
    assert not any(w.code == "structured_text_conflict" for w in result.validation_warnings)


# --- 8. work_hours only ever comes from the structured record ---


def test_work_hours_present_when_structured_states_it():
    structured = _structured(weekly_hours=40.0)
    provider = StubFreeTextProvider([_absent_four()])
    result = analyze_posting_hybrid(PostingInput(source_text="x"), structured, provider)
    assert result.work_hours is not None
    assert result.work_hours.status == "confirmed"
    assert result.work_hours.weekly_hours == 40.0


def test_work_hours_structured_absent_when_structured_omits_it():
    structured = _structured(weekly_hours=None, detailed_work_hours=None, shift_type=None)
    provider = StubFreeTextProvider([_absent_four()])
    result = analyze_posting_hybrid(PostingInput(source_text="x"), structured, provider)
    assert result.work_hours is not None
    assert result.work_hours.status == "structured_absent"
