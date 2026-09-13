from __future__ import annotations

from app.models.work24_structured import Work24StructuredPosting
from app.services.structured_fields import build_employment_type_field, build_salary_field, build_work_hours_info


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
        shift_type=None,
    )
    base.update(overrides)
    return Work24StructuredPosting(**base)


# --- salary: never LLM, purely from the structured record ---


def test_salary_with_amount_and_type_is_confirmed_with_no_evidence():
    field = build_salary_field(_structured())
    assert field.status == "confirmed"
    assert field.evidence is None
    assert field.provenance == "WORK24_STRUCTURED"
    assert field.reason_code == "work24_structured_salary_range"


def test_salary_with_no_amount_at_all_is_absent():
    field = build_salary_field(_structured(salary_min=None, salary_max=None))
    assert field.status == "absent"
    assert field.evidence is None


def test_salary_with_open_ended_minimum_only_is_still_confirmed():
    # "연봉 4,000만원 이상" -- a real pattern in the JB-00 fixture.
    field = build_salary_field(_structured(salary_min=40_000_000, salary_max=None))
    assert field.status == "confirmed"


def test_salary_amount_without_salary_type_is_vague_not_confirmed():
    # TASK section 2: "값이 -, 빈 문자열, 관계없음인 경우 필드 의미에 따라
    # confirmed로 오판하지 않는다" -- an amount with no stated unit/type is
    # not specific enough to blindly confirm.
    for blank in (None, "", "-", "관계없음"):
        field = build_salary_field(_structured(salary_type=blank))
        assert field.status == "vague", blank
        assert field.reason_code == "work24_structured_amount_without_salary_type"


# --- employment_type: never LLM, purely from the structured record ---


def test_employment_type_present_is_confirmed():
    field = build_employment_type_field(_structured(employment_type="정규직"))
    assert field.status == "confirmed"
    assert field.evidence is None
    assert field.provenance == "WORK24_STRUCTURED"


def test_employment_type_blank_marker_is_absent_not_confirmed():
    for blank in ("", "-", "관계없음"):
        field = build_employment_type_field(_structured(employment_type=blank))
        assert field.status == "absent", blank


# --- work_hours: presentation-only, never mixed with the sLLM path ---


def test_work_hours_none_when_no_structured_record_at_all():
    assert build_work_hours_info(None) is None


def test_work_hours_confirmed_when_any_subfield_present():
    info = build_work_hours_info(_structured(weekly_hours=40.0, detailed_work_hours=None, shift_type=None))
    assert info is not None
    assert info.status == "confirmed"
    assert info.weekly_hours == 40.0
    assert info.provenance == "WORK24_STRUCTURED"


def test_work_hours_structured_absent_when_record_exists_but_hours_blank():
    info = build_work_hours_info(
        _structured(weekly_hours=None, detailed_work_hours=None, shift_type=None)
    )
    assert info is not None
    assert info.status == "structured_absent"
    assert info.weekly_hours is None


def test_work_hours_treats_blank_markers_as_absent_not_confirmed():
    info = build_work_hours_info(_structured(weekly_hours=None, detailed_work_hours="-", shift_type="관계없음"))
    assert info is not None
    assert info.status == "structured_absent"
