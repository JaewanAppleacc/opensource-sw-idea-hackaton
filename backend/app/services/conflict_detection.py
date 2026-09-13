"""Deterministic (regex-only, never LLM) detector for a structured-vs-text
salary conflict (TASK "Work24 Structured Data + sLLM Hybrid Audit Pipeline"
section 5).

This never asks an sLLM to compare the two sources -- CLAUDE.md forbids
using an LLM for this kind of comparison/threshold judgement, and the task
brief is explicit that a structured/free-text mismatch must be *detected*,
not silently resolved by trusting one source over the other. It only scans
the same `source_text` the sLLM was given (for salary-adjacent phrases the
structured registry does not capture), never touches `salary`'s own
AuditedField status (which comes entirely from
`app.services.structured_fields.build_salary_field`), and produces a
`ValidationWarning` rather than a new enum value -- exactly the "권장안" in
the task brief, to avoid changing the existing confirmed/vague/absent
contract.
"""
from __future__ import annotations

import re
from typing import Optional

from ..models.posting import ValidationWarning
from ..models.work24_structured import Work24StructuredPosting

# Phrases that describe salary as indeterminate/negotiable in free text --
# a real signal of "this doesn't match a specific registered figure",
# regardless of what number (if any) sits nearby.
_OVERRIDE_PHRASES = ("회사 내규", "면접 후 결정", "추후 협의", "추후 결정", "협의 후 결정")

# "연봉 3,000만원 ~ 4,000만원", "월급 250만원", "시급 12,000원" 등 -- 단위
# 앞의 숫자(콤마 포함)만 추출한다. sLLM이 아닌 순수 정규식이므로 표현이
# 크게 다르면(예: 완전히 다른 어순) 놓칠 수 있고, 그 경우 결과는 "충돌 없음"
# 쪽으로 치우친다 (과소 탐지가 과다 탐지보다 안전하다는 판단).
_SALARY_MENTION_PATTERN = re.compile(r"(연봉|월급|월급여|시급)\s*([\d,]+)\s*만?\s*원")

CONFLICT_MESSAGE = "고용24 등록 필드와 공고 본문의 조건이 다릅니다."


def _parse_krw_amount(digits: str, unit_is_man: bool) -> int:
    value = int(digits.replace(",", ""))
    return value * 10_000 if unit_is_man else value


def _extract_mentions(source_text: str) -> list[tuple[str, int]]:
    mentions: list[tuple[str, int]] = []
    for match in _SALARY_MENTION_PATTERN.finditer(source_text):
        salary_word, digits = match.group(1), match.group(2)
        # "만원" always precedes "원" in the matched span for this pattern,
        # so any match here is already a "만원" (10k KRW unit) figure.
        mentions.append((salary_word, _parse_krw_amount(digits, unit_is_man=True)))
    return mentions


def detect_salary_conflict(source_text: str, structured: Work24StructuredPosting) -> Optional[ValidationWarning]:
    """Returns a `structured_text_conflict` warning if the free posting text
    describes salary in a way that does not match the structured registry
    value -- either a differing figure, or an override phrase ("회사
    내규" 등) alongside a structured figure that claims to be specific.
    Returns None (no warning) whenever nothing in the text contradicts the
    structured value, including when the text simply doesn't mention
    salary at all -- silence is not a conflict.
    """
    if structured.salary_min is None and structured.salary_max is None:
        return None  # nothing structured to conflict with

    has_override_phrase = any(phrase in source_text for phrase in _OVERRIDE_PHRASES)
    if has_override_phrase:
        return ValidationWarning(code="structured_text_conflict", field="salary", message=CONFLICT_MESSAGE)

    mentions = _extract_mentions(source_text)
    structured_bounds = {v for v in (structured.salary_min, structured.salary_max) if v is not None}
    for _word, amount in mentions:
        if amount not in structured_bounds:
            return ValidationWarning(code="structured_text_conflict", field="salary", message=CONFLICT_MESSAGE)

    return None
