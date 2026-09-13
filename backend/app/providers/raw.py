"""Internal wire schema for a raw provider extraction, prior to deterministic
rule application. Not part of the public API contract in contracts/ -- this
is what a provider (mock or real) must produce so the audit pipeline can
validate it.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from ..models.common import FIELD_NAMES, FieldName, FieldStatus


class RawAuditedField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: FieldName
    status: FieldStatus
    evidence_text: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None

    @model_validator(mode="after")
    def _check_evidence_shape(self) -> "RawAuditedField":
        has_any = any(v is not None for v in (self.evidence_text, self.start, self.end))
        has_all = all(v is not None for v in (self.evidence_text, self.start, self.end))
        if self.status == "absent":
            if has_any:
                raise ValueError("absent status must not include evidence_text/start/end")
        elif not has_all:
            raise ValueError(f"{self.status} status requires evidence_text, start, and end")
        return self


class RawExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occupation: Optional[str] = None
    employment_type: Optional[str] = None
    fields: List[RawAuditedField]

    @model_validator(mode="after")
    def _check_six_unique_fields(self) -> "RawExtraction":
        names = [f.field for f in self.fields]
        if sorted(names) != sorted(FIELD_NAMES):
            raise ValueError("extraction must contain exactly the six audited fields, each exactly once")
        return self


# The four free-text fields an sLLM provider is ever allowed to see in the
# hybrid pipeline (TASK "Work24 Structured Data + sLLM Hybrid Audit
# Pipeline" section 3) -- salary and employment_type are handled
# deterministically from Work24StructuredPosting and are never sent to any
# provider on this path.
FREE_TEXT_FIELD_NAMES: tuple[FieldName, ...] = (
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
)


class RawFreeTextExtraction(BaseModel):
    """Restricted extraction schema for the hybrid pipeline's sLLM call.

    Harness rule #8 ("외부 모델이 생성한 추가 필드 차단"): `extra="forbid"`
    on `RawAuditedField` already blocks unknown keys per field, and this
    validator additionally rejects `salary`/`employment_type` (or any field
    outside the four free-text ones) appearing at all -- a provider that
    tries to also report structured fields is a schema violation, not a
    silently-ignored extra.
    """

    model_config = ConfigDict(extra="forbid")

    fields: List[RawAuditedField]

    @model_validator(mode="after")
    def _check_four_free_text_fields_only(self) -> "RawFreeTextExtraction":
        names = [f.field for f in self.fields]
        if sorted(names) != sorted(FREE_TEXT_FIELD_NAMES):
            raise ValueError(
                "hybrid free-text extraction must contain exactly the four free-text "
                f"fields {FREE_TEXT_FIELD_NAMES}, each exactly once -- never salary or employment_type"
            )
        return self
