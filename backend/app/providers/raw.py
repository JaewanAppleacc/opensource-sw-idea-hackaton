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
