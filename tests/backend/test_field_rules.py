from __future__ import annotations

from app.models.common import FIELD_NAMES
from app.rules.field_rules import evaluate_confirmed, get_field_rules, rules_version


def test_runtime_profile_is_version_aligned_and_covers_the_six_field_rubric():
    assert rules_version() == "1.0.0-draft"
    assert {get_field_rules(field).field for field in FIELD_NAMES} == set(FIELD_NAMES)


def test_salary_confirmed_requires_amount_and_unit():
    is_relevant, meets_confirmed, reason = evaluate_confirmed("salary", "급여: 연봉 3,200만원 (세전)")
    assert is_relevant is True
    assert meets_confirmed is True
    assert reason == "amount_with_unit"


def test_salary_without_amount_is_not_confirmed():
    is_relevant, meets_confirmed, reason = evaluate_confirmed("salary", "급여는 면접 시 별도로 안내드립니다")
    assert is_relevant is True
    assert meets_confirmed is False
    assert reason == "missing_amount_or_unit"


def test_salary_vague_marker_wins_over_amount_check():
    is_relevant, meets_confirmed, reason = evaluate_confirmed("salary", "급여는 회사 내규에 따름")
    assert is_relevant is True
    assert meets_confirmed is False
    assert reason == "vague_marker_matched"


def test_probation_confirmed_requires_duration_and_condition():
    is_relevant, meets_confirmed, reason = evaluate_confirmed(
        "probation_terms", "수습기간은 3개월이며 수습 중 급여의 100%를 동일하게 지급합니다"
    )
    assert is_relevant is True
    assert meets_confirmed is True
    assert reason == "duration_with_condition"


def test_probation_duration_without_condition_is_not_confirmed():
    is_relevant, meets_confirmed, reason = evaluate_confirmed("probation_terms", "수습기간은 3개월입니다")
    assert is_relevant is True
    assert meets_confirmed is False
    assert reason == "missing_duration_or_condition"


def test_irrelevant_real_text_is_rejected_by_deterministic_rule():
    # Plausible line from a real posting, but has nothing to do with salary.
    is_relevant, meets_confirmed, reason = evaluate_confirmed("salary", "우리 회사는 전북 전주시에 위치해 있습니다")
    assert is_relevant is False
    assert meets_confirmed is False
    assert reason == "no_relevant_keyword"


def test_common_vague_marker_for_employment_type():
    is_relevant, meets_confirmed, reason = evaluate_confirmed("employment_type", "고용형태는 추후 결정됩니다")
    assert is_relevant is True
    assert meets_confirmed is False
    assert reason == "vague_marker_matched"
