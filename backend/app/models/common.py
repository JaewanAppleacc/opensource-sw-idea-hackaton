"""Shared primitives for every domain model in the contract.

Per CLAUDE.md's grounding rules: structured output is Pydantic-enforced,
additional properties are rejected everywhere, and the audited-field status
enum is exactly {confirmed, vague, absent} -- no `external_verified`, no
free-text company judgement fields.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

FieldName = Literal[
    "salary",
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
    "employment_type",
]

FIELD_NAMES: tuple[FieldName, ...] = (
    "salary",
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
    "employment_type",
)

# Deliberately closed. Do not add "external_verified" -- external context is
# orthogonal and must never mutate a posting field's status.
FieldStatus = Literal["confirmed", "vague", "absent"]

# Where a given AuditedField's value actually came from (TASK "Work24
# Structured Data + sLLM Hybrid Audit Pipeline" section 1). Every
# AuditedField carries exactly one of these -- never inferred by the
# frontend, always set by the backend at the point the value was produced.
# USER_REPORTED exists in the enum for a future multi-turn "기업 응답 반영"
# feature; nothing in this codebase constructs it yet.
Provenance = Literal["WORK24_STRUCTURED", "SLM_EXTRACTED", "USER_REPORTED"]

ErrorCode = Literal[
    "invalid_input",
    "analysis_failed",
    "provider_unavailable",
    "no_match_found",
    "data_not_ready",
    # Additive (inline-jeonbuk-agent): the analyze-by-id path resolves a
    # posting's real text from private, rights-gated local storage
    # (data/private/intake_raw/**) at request time -- this is distinct from
    # "data_not_ready" (which means "no adjudicated human gold yet") and
    # from "no_match_found" (which is about Jeonbuk candidate matching).
    "private_data_unavailable",
]


class StrictModel(BaseModel):
    """Base model that rejects unknown fields, per grounding rules."""

    model_config = ConfigDict(extra="forbid")


class EvidenceSpan(StrictModel):
    """An exact, offset-verifiable quote from the source posting text."""

    text: str = Field(..., min_length=1)
    start: int = Field(..., ge=0)
    end: int = Field(..., gt=0)

    @model_validator(mode="after")
    def _check_span_consistency(self) -> "EvidenceSpan":
        if self.end <= self.start:
            raise ValueError("evidence span end must be greater than start")
        if self.end - self.start != len(self.text):
            raise ValueError("evidence span length must match evidence text length")
        return self


class APIError(StrictModel):
    code: ErrorCode
    message: str
    details: Optional[dict] = None
