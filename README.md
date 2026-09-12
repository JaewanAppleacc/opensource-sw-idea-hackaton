# 전북 커리어 실사 에이전트 MVP

수도권 채용공고를 검토하는 청년에게 같은 직종·고용형태의 전북 공고를 함께 보여주고, 공고에 적혀 있지 않거나 모호한 조건을 질문으로 바꾸며, 사용자가 입력한 소득·주거비로 현금 축적 시나리오를 비교하는 오픈소스 MVP입니다.

이 서비스는 기업을 평가하거나 전북 취업을 권고하지 않습니다. 목표는 전북 일자리가 비교 대상에조차 오르지 않는 `회피 가능한 미검토`를 줄이는 것입니다.

## 현재 구현됨

- 6개 항목 공고 실사: 급여, 업무, 도구·기술, 교육·멘토링, 수습조건, 고용형태
- 원문 substring/offset 검증과 `confirmed | vague | absent` 폐쇄형 판정
- vague/absent 항목별 확인 질문 생성
- 같은 직종·고용형태의 전북 공고 최대 3건 탐색
- 사용자가 입력한 값만 사용하는 월 잉여금·1년·3년·주거비 교차점 계산
- 사람 gold가 없으면 통계를 내지 않는 지역 결손 통계 API
- FastAPI/OpenAPI 계약, 로컬 프론트엔드 CORS, 오프라인 mock 실행

## 캐시된 데모

`demo/anchors.json`의 정확히 3개 공고를 사용합니다. 전부 가상 기업의 합성 데이터이며 실제 기업이나 전북 노동시장에 대한 근거가 아닙니다.

- `MET-001`: 급여가 명확한 수도권 공고
- `JB-001`: 급여가 명확한 전북 비교 공고
- `JB-003`: 여러 정보 결손을 질문으로 전환하는 전북 공고

데이터 파이프라인 결과도 현재는 합성 fixture 검증 결과입니다. `data/reports/demo_*` 수치를 실제 지역 통계나 모델 성능으로 발표하면 안 됩니다.

## 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

API 문서: `http://127.0.0.1:8000/docs`  
프론트 연동 문서: `FRONTEND_API_HANDOFF.md`

```bash
source .venv/bin/activate
python -m pytest tests/backend tests/data -q
```

기본값은 API 키와 네트워크가 필요 없는 deterministic mock입니다. 실제 Anthropic 호출은 `.env.example`을 참고하되 키를 저장소에 커밋하지 마십시오.

## 아직 구현·검증되지 않음

- 실제 고용24/워크넷 공고 수집 및 재배포 허가 확인
- 실제 전북 20건·수도권 20건의 동직종 매칭 표본
- 2명 독립 라벨링, 조정 완료 human gold, 사람 간 일치도
- 고정된 holdout에서의 실제 LLM 평가
- 실제 사용자 대상 전북 공고 검토율 A/B 실험
- 전북 청년 순유출 감소라는 장기 인과효과
- 브라우저 확장프로그램, 라이브 채용사이트 연동, 운영 배포

따라서 현 단계는 “제품 흐름과 안전장치가 동작하는 MVP”이지 “전북 청년 유출 감소 효과가 입증된 서비스”가 아닙니다. 실제 데이터 작업 순서는 `DATA_HANDOFF.md`에 있습니다.
