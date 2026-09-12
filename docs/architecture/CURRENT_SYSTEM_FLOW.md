# 현재 시스템 흐름 (실제 코드 기준)

이 문서는 `docs/architecture/` 세트의 기준 문서입니다. 다른 세 문서(`EXPANSION_TECH_ASSESSMENT.md`,
`REGION_PACK_ONTOLOGY.md`, `AI_HARNESS.md`)는 이 문서에 기록된 "실제로 구현된 것"을 전제로 판정합니다.

조사 기준 브랜치: `origin/feature/home-visual-fidelity` (커밋 `7b8f3a6`).
조사 방법: 문서 서술이 아니라 `backend/app/**`, `contracts/*.json`, `tests/**`, `scripts/annotation_ops/**`
실제 코드를 읽고 검증. 문서와 코드가 불일치하는 지점은 아래에 명시적으로 표기했습니다.

---

## 1. 과제 지시서의 "제품 흐름"과 실제 구현의 차이

과제 지시서에 제시된 흐름:

```text
고용24 로그인 데모 → 관심 생활권 확인 → 수도권 AI추천 공고 열람
→ 관심 생활권의 유사 공고 자동 매칭 → 6개 채용정보 항목 실사
→ vague/absent 확인 질문 생성 → 주거비 포함 자금 축적 비교
```

실제 코드/문서 대조 결과, 이 흐름 중 **뒤 네 단계는 구현되어 있고, 앞 두 단계는 구현되어 있지 않습니다.**

| 단계 | 지시서 서술 | 실제 상태 | 근거 |
|---|---|---|---|
| 고용24 로그인 데모 | 로그인 후 시작 | **미구현.** 실제 로그인/세션/인증 플로우 없음. `<LogIn>` 아이콘은 `lucide-react`에서 가져온 장식용 UI일 뿐 (`MainHeader.tsx`, `MobileMenu.tsx`) | README.md §시연 순서(104-118행)는 `/ai-job-recommend`에서 "데모 모드" 배지로 바로 시작 |
| 관심 생활권 확인 | 사용자가 생활권(지역)을 선택/확인 | **미구현.** `home_region`, `comparison_regions`, `region_pack` 필드가 contracts/코드 어디에도 없음 | `contracts/schema.json`의 `region`은 자유 문자열(665-668, 784-787행), enum 아님 |
| 수도권 AI추천 공고 열람 | 수도권 공고를 AI가 추천 | 부분 구현. 큐레이션된 유한 데이터셋에서 규칙 기반 후보 산출 (아래 §3) | `backend/app/services/matching.py` |
| 유사 공고 자동 매칭 | 구현됨 | occupation 정확 일치 + employment_type 가산점, 최대 3건 | `matching.py:22-71` |
| 6개 항목 실사 | 구현됨 | 아래 §2, `AI_HARNESS.md` 참조 | `backend/app/services/audit_pipeline.py` |
| vague/absent 확인 질문 생성 | 구현됨 | `VerificationAction` 결정론적 템플릿 매핑 | `audit_pipeline.py:96-97`, `services/verification.py` |
| 주거비 포함 자금 축적 비교 | 부분 구현. 계산 자체는 구현됨. **단, "주거비"는 지역 기준값이 아니라 사용자가 직접 입력하는 값** | `FinancialOption.monthly_housing_cost`는 사용자 입력 숫자 필드 (schema.json:922-927), 지역별 baseline 조회 없음 | `backend/app/services/finance.py` |

**결론:** 이 문서 세트의 나머지 판정(특히 MCP의 `get_regional_housing_baseline`, Ontology의
`RegionPack`/`RegionalCostBaseline`)은 "이미 있는 것을 문서화"가 아니라 "지금 없는 것을 앞으로 어떻게
최소하게 추가할지"에 대한 설계입니다. 이 구분을 혼동하지 않도록 각 문서에서 반복 명시합니다.

---

## 2. 실제 API 표면 (5개 엔드포인트, 전부 동기 REST)

`contracts/openapi.json` 확인: 정확히 5개 경로. 세션/웹소켓/스트리밍/페이지네이션 커서 없음 —
멀티턴 상태를 암시하는 요소가 전혀 없습니다.

| 메서드/경로 | 역할 | 비고 |
|---|---|---|
| `GET /api/v1/health` | provider_mode(`mock`/`anthropic`/`nvidia`) 등 헬스 체크 | mock으로 조용히 폴백하지 않았음을 증명하는 용도로도 사용됨 (`docs/validation/LIVE_LLM_SMOKE.md`) |
| `POST /api/v1/postings/analyze` | 공고 1건 → 6개 필드 실사 결과 | 요청 1건 = 응답 1건, 상태 없음 |
| `POST /api/v1/postings/match` | 관심 공고 ↔ 전북 후보 매칭 | 결정론적 규칙, 최대 3건 |
| `POST /api/v1/finance/compare` | 자금 축적 비교 계산 | 순수 결정론적 산술, LLM 미호출 |
| `GET /api/v1/data/gap-stats` | 사람이 감수(adjudicate)한 gold 라벨 통계 | gold 없으면 `ready:false`, AI 라벨로 대체 폴백하지 않음 |

루트 API 설명(openapi.json:5행): "수도권 공고를 큐레이션된 전북 공고와 대조하여 근거 기반으로
항목을 추출하고, 미해결 항목을 확인 액션으로 변환하며, 결정론적 가상 현금흐름 비교를 수행한다.
기업 평가나 미래 예측 서비스가 아니다."

---

## 3. 공고 실사(Audit) 파이프라인 — 단계별 실행 순서

`backend/app/services/audit_pipeline.py`의 `analyze_posting()` (26-107행)을 그대로 따름:

1. **추출 호출**: `provider.extract(source_text, expected_occupation)` (31행) — Provider는
   `Protocol` 인터페이스 (`providers/base.py:6-24`), 구현체는 Mock/Anthropic/NVIDIA 3종.
2. **스키마 검증**: `RawExtraction.model_validate()` (33행) — `extra="forbid"` 강제 (`models/common.py:45-48`).
3. **근거 검증**: 필드별 `validate_evidence_span()` (34-38행, `services/evidence.py:15-24`) —
   `source_text[start:end] == evidence_text` 정확 일치. 실패 시 `EvidenceMismatchError`.
4. **재시도(최대 1회)**: `MAX_ATTEMPTS = 2` (23행), `ValidationError`/`EvidenceMismatchError`에서만 재시도 (30-43행).
   둘 다 실패하면 타입화된 `AnalysisFailedError` (45-49행) — LLM이 틀렸다고 추측해서 수치를 지어내지 않음.
5. **결정론적 강등**: `evaluate_confirmed()` (`rules/field_rules.py:71-104`) — 관련 없음 → `absent`(63-72행),
   관련은 있으나 기준 미달 → `vague`(80-88행). 모듈 docstring(audit_pipeline.py:4-7): "상태는 절대
   상향되지 않으며, 절대 지어내지 않는다."
6. **확인 액션 생성**: `vague`/`absent` 필드마다 고정 템플릿으로 `VerificationAction` 매핑 (96-97행,
   `services/verification.py`).
7. **응답 조립**: `PostingAnalysis` 조립 후 6개 필드 전부 존재를 다시 스키마로 검증 (`models/posting.py:63-71`).

**병렬성/비동기**: `backend/app/` 전체에서 `asyncio` grep 결과 0건, `async def` 0건. 공고당 요청 1건
= 동기 처리 1회 (`api/v1/postings.py:14-28`). 여러 공고 병렬 분석 기능 자체가 없음.

**멀티턴 상태**: `session`/`resume`/`previous_state`/`conversation` grep 결과 0건. 이전 실사 결과를
불러와 특정 필드만 재검증하는 기능 없음. → `AI_HARNESS.md`와 `EXPANSION_TECH_ASSESSMENT.md`(LangGraph
섹션)의 핵심 판단 근거.

---

## 4. 매칭(Matching) — 결정론적 규칙, 벡터 검색 없음

`backend/app/services/matching.py:22-71`:
- occupation **정확 일치**(필수, 대소문자 정규화), employment_type 일치 시 가산점 +1 (41행).
- 동점 시 `posting_id`로 타이브레이크.
- 데이터 소스는 `backend/app/datasets/loader.py`가 읽는 큐레이션된 유한 데이터셋 — 실시간 크롤링/외부 API 없음.
- 모듈 docstring(1-7행): "벡터 데이터베이스 없음, 실시간 크롤링 없음." 최선 매칭(best-match)이라 주장하지
  않음(`DATASET_DESCRIPTION`, 16-19행).
- `region`은 `datasets/loader.py:35,51,82`, `services/finance.py:67-71`에 하드코딩된 리터럴 문자열
  `"jeonbuk"` / `"metropolitan"` 2개뿐 — 코드 곳곳에 흩어져 있고 별도 region 설정 파일/enum이 없음
  (→ `REGION_PACK_ONTOLOGY.md`의 최소 구현안 근거).

---

## 5. 자금 축적 비교(Finance) — 순수 결정론적 산술

`backend/app/services/finance.py` (모듈 docstring 1행: "No LLM involvement"):
- `_monthly_surplus` (30-31행), `_three_year_liquid_cash` (34-42행): 단순 산술.
- `_compute_crossover` (64-103행): 교차 시점을 구하는 폐형(closed-form) 대수 계산.
- 입력은 100% 사용자 입력(`monthly_income_after_tax`, `monthly_housing_cost`,
  `monthly_other_living_cost`, `deposit`) — 지역별 baseline 자동 조회 없음(§1 참조).

---

## 6. 실제 데이터 규모

`REAL_DATA_ACQUISITION_HANDOFF.md:48` 기준:

- 실공고 **20건** (전북 10 + 수도권 10), **매칭 쌍 10개**, 미매칭 0건.
- 상태는 `MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW` — `READY_FOR_HUMAN_ANNOTATION`도 gold도 아님.
- 목표치(20:20) 미달성(`meets_target_20_20: false`).
- 수집 방법: 고용24 공개 검색 UI 수동 전사 (Open API는 `blocked_no_credentials`로 미사용).
- 수도권 10건 전부 인천/경기, 서울 소재 공고는 0건 — "수도권 = 서울"이 아님에 유의.
- 게시물별 재배포 권리 미확인 → 공개 JSONL의 `full_text`는 `null`.
- 페어링(`pair_postings.py`)은 (occupation, employment_type) 정확 일치 + 파일 순서로만 수행 — 의미
  기반/임베딩 매칭 없음.

AI 합의 검수(`docs/data/AI_CONSENSUS_REVIEW.md`): 20건×6필드 = 120셀, 독립 AI 2패스(A/B) 간
113/120(94.2%) 일치, 7건 사람 감수. 최종 분포: confirmed 60 / vague 17 / absent 43. 문서 자체가
"이는 모델 정확도 지표가 아니라 두 AI 리뷰 패스 간 일치율일 뿐"이라고 명시(21-23행), "상태값만
비교했으므로 실제 독립 합의를 과대평가한다"는 한계도 자체 공개(91-97행).

---

## 7. 프론트엔드 데모 흐름

README.md §시연 순서(104-118행) + `demo/anchors.json`:
- `/ai-job-recommend`에서 "데모 모드" 배지로 시작 (로그인 없음).
- 캐시된 데모는 정확히 3건의 공고(`MET-001`, `JB-001`, `JB-003`)로 고정.
- 전북 후보는 동일 occupation/employment_type 기준 최대 3건까지만 노출(README.md:14, 108행).

---

## 8. 미구현 항목 명시 (README.md 135-144행 자체 공개)

- 실제 Work24 재배포 권리 미확인.
- 사람 gold 라벨 아직 없음(`/data/gap-stats`는 `ready:false`).
- 고정 holdout 기반 LLM 평가 없음.
- A/B 실험 없음.
- 장기 인구 유출 인과 주장 없음(상관 수준 서술만 허용).
- 브라우저 확장/실 사이트 연동 없음.

이 목록은 `EXPANSION_TECH_ASSESSMENT.md`의 "도입을 재검토할 조건"을 판단할 때 반복 참조됩니다.
