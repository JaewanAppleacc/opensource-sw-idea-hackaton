from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import Field, field_validator, model_validator

from .common import FIELD_NAMES, EvidenceSpan, FieldName, FieldStatus, Provenance, StrictModel
from .external import ExternalContext
from .work24_structured import WorkHoursInfo


class PostingInput(StrictModel):
    posting_id: Optional[str] = None
    source_text: str = Field(..., min_length=1)
    source_url: Optional[str] = None
    expected_occupation: Optional[str] = None

    @field_validator("source_text")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_text must not be blank")
        return value


class AuditedField(StrictModel):
    field: FieldName
    status: FieldStatus
    evidence: Optional[EvidenceSpan] = None
    reason_code: str = Field(..., min_length=1, description="Deterministic rule code explaining the status decision.")
    provenance: Provenance = Field(
        ...,
        description=(
            "Where this field's value actually came from: WORK24_STRUCTURED "
            "(고용24 등록 정보, deterministic, never LLM-touched), SLM_EXTRACTED "
            "(공고 본문 자유서술을 분석), or USER_REPORTED (not produced anywhere yet)."
        ),
    )

    @model_validator(mode="after")
    def _check_evidence_matches_status(self) -> "AuditedField":
        if self.status == "absent":
            if self.evidence is not None:
                raise ValueError("absent fields must not carry evidence")
        elif self.provenance == "WORK24_STRUCTURED":
            # A structured registry read has no free-text quote to cite --
            # requiring one here would force a fabricated evidence span.
            if self.evidence is not None:
                raise ValueError("WORK24_STRUCTURED fields must not carry a free-text evidence span")
        elif self.evidence is None:
            raise ValueError(f"{self.status} fields require evidence")
        return self


class VerificationAction(StrictModel):
    field: FieldName
    channel: Literal["email", "phone", "interview", "document_review", "pre_contract"]
    prompt: str = Field(..., min_length=1)
    triggered_by_status: Literal["vague", "absent"]


class ValidationWarning(StrictModel):
    code: str
    field: Optional[FieldName] = None
    message: str


class PostingAnalysis(StrictModel):
    posting_id: Optional[str] = None
    occupation: Optional[str] = None
    employment_type: Optional[str] = None
    fields: Dict[FieldName, AuditedField]
    verification_actions: List[VerificationAction] = Field(default_factory=list)
    validation_warnings: List[ValidationWarning] = Field(default_factory=list)
    external_context: List[ExternalContext] = Field(default_factory=list)
    work_hours: Optional[WorkHoursInfo] = Field(
        default=None,
        description=(
            "근로시간·교대제, sourced only from a Work24StructuredPosting record -- "
            "never from an LLM. None means no such record exists for this posting "
            "(unchanged 'not_evaluated' MVP-scope behavior); see WorkHoursInfo.status "
            "for the distinction between 'confirmed' and 'structured_absent'."
        ),
    )

    @model_validator(mode="after")
    def _check_all_six_fields_present(self) -> "PostingAnalysis":
        missing = set(FIELD_NAMES) - set(self.fields.keys())
        if missing:
            raise ValueError(f"missing audited fields: {sorted(missing)}")
        for key, audited in self.fields.items():
            if key != audited.field:
                raise ValueError("fields dict key must match AuditedField.field")
        return self
