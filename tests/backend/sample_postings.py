"""Shared synthetic posting texts used across the backend test suite.

All Korean text here is written for these tests -- not scraped, not real
postings -- matching the anchors/keywords in
backend/app/rules/field_rules.yaml.
"""
from __future__ import annotations

FULLY_SPECIFIED_POSTING = (
    "직무: 백엔드 개발자\n"
    "고용형태: 정규직으로 채용합니다\n"
    "담당업무: 결제 시스템 API 설계 및 개발, 서버 배포 자동화 구축\n"
    "사용언어: Python과 SQL을 사용하며 AWS 인프라를 운영합니다\n"
    "급여: 연봉 3,200만원 (세전)\n"
    "수습기간: 입사 후 3개월이며 수습 중에도 급여의 100%를 동일하게 지급합니다\n"
    "멘토링: 입사 후 1개월간 사수가 1:1로 정기 교육을 진행합니다\n"
)

VAGUE_SALARY_POSTING = (
    "직무: 백엔드 개발자\n"
    "급여: 회사 내규에 따름\n"
    "고용형태: 정규직\n"
)

MINIMAL_POSTING_MISSING_MOST_FIELDS = "직무: 백엔드 개발자\n담당업무: 서비스 운영 및 관리 업무를 담당합니다\n"
