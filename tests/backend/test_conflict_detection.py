from __future__ import annotations

from app.models.work24_structured import Work24StructuredPosting
from app.services.conflict_detection import CONFLICT_MESSAGE, detect_salary_conflict


def _structured(**overrides) -> Work24StructuredPosting:
    base = dict(
        posting_id="TEST-01",
        occupation_name="테스트 직종",
        employment_type="정규직",
        salary_type="월급",
        salary_min=2_500_000,
        salary_max=3_000_000,
    )
    base.update(overrides)
    return Work24StructuredPosting(**base)


def test_no_conflict_when_text_never_mentions_salary():
    structured = _structured()
    source = "담당업무: 서비스 운영 및 관리 업무를 담당합니다\n"
    assert detect_salary_conflict(source, structured) is None


def test_no_conflict_when_text_matches_structured_amount():
    structured = _structured(salary_min=2_500_000, salary_max=3_000_000)
    source = "급여: 월급 250만원~300만원\n"
    assert detect_salary_conflict(source, structured) is None


def test_conflict_when_text_states_a_different_amount():
    # TASK section 5's own example: 고용24 구조화 월급 250만~300만 원, but
    # the same posting's free text quotes an unrelated figure.
    structured = _structured(salary_min=2_500_000, salary_max=3_000_000)
    source = "복리후생 안내에는 별도로 월급 500만원이라고 잘못 적혀 있습니다.\n"
    warning = detect_salary_conflict(source, structured)
    assert warning is not None
    assert warning.code == "structured_text_conflict"
    assert warning.field == "salary"
    assert warning.message == CONFLICT_MESSAGE


def test_conflict_when_text_describes_salary_as_company_policy():
    # TASK section 5's own example: 자유서술 "연봉 회사 내규".
    structured = _structured(salary_min=25_000_000, salary_max=None)
    source = "급여: 연봉 회사 내규에 따름\n"
    warning = detect_salary_conflict(source, structured)
    assert warning is not None
    assert warning.code == "structured_text_conflict"


def test_no_conflict_when_structured_has_no_salary_at_all():
    structured = _structured(salary_min=None, salary_max=None)
    source = "급여: 회사 내규에 따름\n"
    assert detect_salary_conflict(source, structured) is None
