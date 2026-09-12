"""Deterministic mapping from a gap (vague/absent field) to a concrete
verification action. Prompts are fixed, typed templates -- never LLM
free text -- so they can never drift into a company judgement.
"""
from __future__ import annotations

from ..models.posting import VerificationAction

_CHANNEL_MAP: dict[str, str] = {
    "salary": "email",
    "duties": "interview",
    "tools_or_skills": "interview",
    "training_or_mentoring": "email",
    "probation_terms": "pre_contract",
    "employment_type": "document_review",
}

_PROMPT_TEMPLATES: dict[str, dict[str, str]] = {
    "salary": {
        "vague": "채용 담당자에게 급여 범위(세전/세후, 연봉 또는 월급 단위)를 명확히 요청하세요.",
        "absent": "공고에 급여 정보가 없습니다. 이메일 또는 전화로 급여 조건을 문의하세요.",
    },
    "duties": {
        "vague": "실제 담당 업무의 구체적 예시(일간 업무, 주요 산출물 등)를 면접에서 질문하세요.",
        "absent": "담당 업무 설명이 없습니다. 면접에서 구체적인 업무 범위를 확인하세요.",
    },
    "tools_or_skills": {
        "vague": "실제 사용하는 도구/기술 스택을 면접에서 구체적으로 질문하세요.",
        "absent": "필요 기술/도구 정보가 없습니다. 면접에서 확인하세요.",
    },
    "training_or_mentoring": {
        "vague": "교육/멘토링 프로그램의 기간, 방식, 담당자를 이메일로 문의하세요.",
        "absent": "교육/멘토링 관련 정보가 없습니다. 이메일로 온보딩 절차를 문의하세요.",
    },
    "probation_terms": {
        "vague": "수습 기간의 정확한 개월 수와 수습 중 급여 조건을 근로계약서(사전 계약서) 검토 시 확인하세요.",
        "absent": "수습 조건이 명시되어 있지 않습니다. 근로계약서 검토 시 수습 기간과 급여를 확인하세요.",
    },
    "employment_type": {
        "vague": "정확한 고용형태(정규직/계약직/인턴 등)와 전환 조건을 서류 검토 시 확인하세요.",
        "absent": "고용형태 정보가 없습니다. 서류 검토 또는 문의를 통해 확인하세요.",
    },
}


def build_verification_action(field: str, status: str) -> VerificationAction:
    return VerificationAction(
        field=field,  # type: ignore[arg-type]
        channel=_CHANNEL_MAP[field],  # type: ignore[arg-type]
        prompt=_PROMPT_TEMPLATES[field][status],
        triggered_by_status=status,  # type: ignore[arg-type]
    )
