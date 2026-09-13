from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.common import EvidenceSpan
from app.models.posting import AuditedField, PostingAnalysis, PostingInput


def test_evidence_span_requires_consistent_length():
    EvidenceSpan(text="급여: 3200만원", start=0, end=len("급여: 3200만원"))
    with pytest.raises(ValidationError):
        EvidenceSpan(text="급여: 3200만원", start=0, end=3)


def test_confirmed_field_requires_evidence():
    with pytest.raises(ValidationError):
        AuditedField(field="salary", status="confirmed", evidence=None, reason_code="x")


def test_vague_field_requires_evidence():
    with pytest.raises(ValidationError):
        AuditedField(field="salary", status="vague", evidence=None, reason_code="x")


def test_absent_field_must_not_carry_evidence():
    with pytest.raises(ValidationError):
        AuditedField(
            field="salary",
            status="absent",
            evidence={"text": "x", "start": 0, "end": 1},
            reason_code="x",
        )


def test_absent_field_with_no_evidence_is_valid():
    field = AuditedField(
        field="salary", status="absent", evidence=None, reason_code="no_relevant_keyword", provenance="SLM_EXTRACTED"
    )
    assert field.status == "absent"
    assert field.evidence is None


def test_audited_field_requires_provenance():
    with pytest.raises(ValidationError):
        AuditedField(field="salary", status="absent", evidence=None, reason_code="x")


def test_audited_field_rejects_unknown_provenance():
    with pytest.raises(ValidationError):
        AuditedField(field="salary", status="absent", evidence=None, reason_code="x", provenance="GUESSED")


def test_invalid_status_is_rejected():
    with pytest.raises(ValidationError):
        AuditedField(field="salary", status="external_verified", evidence=None, reason_code="x")


def test_audited_field_rejects_additional_properties():
    with pytest.raises(ValidationError):
        AuditedField(
            field="salary",
            status="absent",
            evidence=None,
            reason_code="x",
            company_stability_score=9,  # not a real field; must be rejected
        )


def test_posting_input_rejects_additional_properties():
    with pytest.raises(ValidationError):
        PostingInput(source_text="hello", unexpected_field="nope")


def test_posting_input_rejects_blank_text():
    with pytest.raises(ValidationError):
        PostingInput(source_text="   ")


def test_posting_analysis_requires_all_six_fields():
    partial_fields = {
        "salary": AuditedField(
            field="salary", status="absent", evidence=None, reason_code="no_relevant_keyword", provenance="SLM_EXTRACTED"
        ),
    }
    with pytest.raises(ValidationError):
        PostingAnalysis(fields=partial_fields)


def test_posting_analysis_rejects_unknown_field_key():
    with pytest.raises(ValidationError):
        PostingAnalysis(
            fields={
                "salary": {"field": "salary", "status": "absent", "evidence": None, "reason_code": "x", "provenance": "SLM_EXTRACTED"},
                "duties": {"field": "duties", "status": "absent", "evidence": None, "reason_code": "x", "provenance": "SLM_EXTRACTED"},
                "tools_or_skills": {"field": "tools_or_skills", "status": "absent", "evidence": None, "reason_code": "x", "provenance": "SLM_EXTRACTED"},
                "training_or_mentoring": {
                    "field": "training_or_mentoring",
                    "status": "absent",
                    "evidence": None,
                    "reason_code": "x",
                    "provenance": "SLM_EXTRACTED",
                },
                "probation_terms": {"field": "probation_terms", "status": "absent", "evidence": None, "reason_code": "x", "provenance": "SLM_EXTRACTED"},
                "not_a_real_field": {"field": "employment_type", "status": "absent", "evidence": None, "reason_code": "x", "provenance": "SLM_EXTRACTED"},
            }
        )
