"""고용24 공통 스키마에 이미 존재하는 구조화 필드 (TASK "Work24 Structured Data
+ sLLM Hybrid Audit Pipeline" section 1).

`Work24StructuredPosting` is deliberately **not** part of the public API
contract in `contracts/`: it is an internal, server-side fixture record --
the frontend never receives this whole object, only the deterministic
`AuditedField` values and the `WorkHoursInfo` summary derived from it (see
`app.services.structured_fields`). `WorkHoursInfo` itself *is* part of the
public contract (`PostingAnalysis.work_hours`).

Every field here must come from something actually visible on the real
고용24 posting-detail page for that posting_id. `jobs_cd`/`emp_tp_cd` (the
official numeric codes) are not visible on the rendered page text this
project has access to (no live API key -- see REAL_DATA_ACQUISITION_HANDOFF.md)
and are therefore always `None` in every fixture in this repository. Never
estimate or invent a value for any field here -- `None` (or an empty
collection) is the correct, honest value when a posting's detail page does
not state something.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import Field

from .common import StrictModel


class Work24StructuredPosting(StrictModel):
    posting_id: str
    jobs_cd: Optional[str] = None
    occupation_name: str
    emp_tp_cd: Optional[str] = None
    employment_type: str
    salary_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    contract_months: Optional[int] = None
    weekly_hours: Optional[float] = None
    detailed_work_hours: Optional[str] = None
    shift_type: Optional[str] = None
    region_code: Optional[str] = None
    municipality: Optional[str] = None
    career_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    licenses: List[str] = Field(default_factory=list)
    welfare_flags: Dict[str, Optional[bool]] = Field(default_factory=dict)


class WorkHoursInfo(StrictModel):
    """Presentation-ready 근로시간·교대제 info, sourced *only* from
    `Work24StructuredPosting` -- never from an LLM/sLLM, never estimated.

    `status`:
      - "confirmed": at least one of weekly_hours/detailed_work_hours/
        shift_type is present on the structured record.
      - "structured_absent": a Work24StructuredPosting record exists for
        this posting_id, but none of those three sub-fields are stated on
        it. Frontend must render this as "고용24 등록 정보에서 확인되지
        않음" -- never "확인 불가" (that phrase is reserved for the
        evidence-harness vague/absent flow, which this is not).

    `PostingAnalysis.work_hours is None` (the field is simply absent from
    the response) is the *third*, different case: no Work24StructuredPosting
    record exists for this posting_id at all. The frontend keeps showing
    `not_evaluated` for that case, unchanged from before this feature.
    """

    weekly_hours: Optional[float] = None
    detailed_work_hours: Optional[str] = None
    shift_type: Optional[str] = None
    status: Literal["confirmed", "structured_absent"]
    provenance: Literal["WORK24_STRUCTURED"] = "WORK24_STRUCTURED"
