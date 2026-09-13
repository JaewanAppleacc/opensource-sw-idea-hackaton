"""Deterministic (never LLM-touched) rule engine that turns a
`Work24StructuredPosting` record into `AuditedField` entries for `salary`
and `employment_type`, plus a `WorkHoursInfo` summary for 근로시간·교대제
(TASK "Work24 Structured Data + sLLM Hybrid Audit Pipeline" sections 2 & 6).

Every function here is pure and offline: no network call, no LLM, no
retries. `evaluate_confirmed`/the free-text rubric in
`app.rules.field_rules` is never used here -- this module has its own,
narrower rules because a structured registry field is either present
(confirmed) or it is not (absent); there is no "vague-but-present" free
text to classify. The one exception (an amount present without a unit/type)
is handled explicitly below, per TASK section 2: "값이 -, 빈 문자열,
관계없음인 경우 필드 의미에 따라 confirmed로 오판하지 않는다."
"""
from __future__ import annotations

from typing import Optional

from ..models.posting import AuditedField
from ..models.work24_structured import Work24StructuredPosting, WorkHoursInfo

# Placeholder values that mean "no real information", never treated as a
# confirmed answer for a field whose whole point is to report a positive
# fact (unlike e.g. licenses, where "관계없음" is parsed upstream, at
# fixture-build time, straight into an empty list -- a real, confirmed
# "no license required" fact, not a placeholder).
_BLANK_MARKERS = {"", "-", "관계없음", "해당없음", "미상"}


def _is_blank(value: Optional[str]) -> bool:
    return value is None or value.strip() in _BLANK_MARKERS


def build_salary_field(structured: Work24StructuredPosting) -> AuditedField:
    """`salary` is never sent to an sLLM in the hybrid pipeline -- this is
    the entire determination, from `Work24StructuredPosting.salary_min/max/type`
    alone. `evidence` is always None: this is not a free-text quote, it is a
    structured registry value, so there is no source span to cite (Evidence
    Harness's substring check is for sLLM/LLM-reported evidence only).
    """
    has_amount = structured.salary_min is not None or structured.salary_max is not None

    if not has_amount:
        return AuditedField(
            field="salary",
            status="absent",
            evidence=None,
            reason_code="work24_structured_salary_absent",
            provenance="WORK24_STRUCTURED",
        )

    if _is_blank(structured.salary_type):
        # An amount with no stated salary_type (연봉/월급/시급 등) is not
        # specific enough to act on -- e.g. is 3000 a monthly or annual
        # figure? Downgrade rather than assume.
        return AuditedField(
            field="salary",
            status="vague",
            evidence=None,
            reason_code="work24_structured_amount_without_salary_type",
            provenance="WORK24_STRUCTURED",
        )

    return AuditedField(
        field="salary",
        status="confirmed",
        evidence=None,
        reason_code="work24_structured_salary_range",
        provenance="WORK24_STRUCTURED",
    )


def build_employment_type_field(structured: Work24StructuredPosting) -> AuditedField:
    """`employment_type` is never sent to an sLLM in the hybrid pipeline --
    this is the entire determination, from
    `Work24StructuredPosting.employment_type` alone.
    """
    if _is_blank(structured.employment_type):
        return AuditedField(
            field="employment_type",
            status="absent",
            evidence=None,
            reason_code="work24_structured_employment_type_absent",
            provenance="WORK24_STRUCTURED",
        )

    return AuditedField(
        field="employment_type",
        status="confirmed",
        evidence=None,
        reason_code="work24_structured_employment_type_present",
        provenance="WORK24_STRUCTURED",
    )


def build_work_hours_info(structured: Optional[Work24StructuredPosting]) -> Optional[WorkHoursInfo]:
    """Returns None (meaning: keep the existing `not_evaluated` MVP-scope
    display, unchanged) when no structured record exists at all for this
    posting. Returns a `WorkHoursInfo` with `status="structured_absent"`
    (never `"확인 불가"`, never the free-text `absent` status) when a record
    exists but states none of weekly_hours/detailed_work_hours/shift_type.
    Never derived from, or cross-checked against, sLLM output -- this is a
    read of the registry record alone (TASK section 6: "현재 데이터가 없으면
    not_evaluated를 유지한다. 값을 추정하지 않는다.").
    """
    if structured is None:
        return None

    has_weekly_hours = structured.weekly_hours is not None
    has_detailed_hours = not _is_blank(structured.detailed_work_hours)
    has_shift_type = not _is_blank(structured.shift_type)

    if not (has_weekly_hours or has_detailed_hours or has_shift_type):
        return WorkHoursInfo(status="structured_absent")

    return WorkHoursInfo(
        weekly_hours=structured.weekly_hours,
        detailed_work_hours=structured.detailed_work_hours if has_detailed_hours else None,
        shift_type=structured.shift_type if has_shift_type else None,
        status="confirmed",
    )
