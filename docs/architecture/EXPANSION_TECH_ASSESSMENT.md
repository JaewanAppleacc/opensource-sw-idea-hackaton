# 확장 기술 타당성 평가

## 조사 방법

본 평가는 `origin/feature/home-visual-fidelity` 브랜치의 실제 코드(`backend/app/**`,
`contracts/*.json`, `tests/backend/**`, `tests/annotation_ops/**`, `scripts/annotation_ops/**`)와
프로젝트 자체 문서(`CLAUDE.md`, `README.md`, `BACKEND_HANDOFF.md`, `REAL_DATA_ACQUISITION_HANDOFF.md`,
`docs/data/AI_CONSENSUS_REVIEW.md`, `docs/validation/LIVE_LLM_SMOKE.md`)를 직접 읽고 검증한 결과를
근거로 합니다. 코드/테스트로 확인되지 않은 주장은 하지 않았습니다. 상세 근거는
`CURRENT_SYSTEM_FLOW.md`, `AI_HARNESS.md`, `REGION_PACK_ONTOLOGY.md`에 있으며 본 문서는 그 근거를
바탕으로 기술 도입 여부만 판정합니다.

참고: `CLAUDE.md:82-90`에는 이미 이 프로젝트 자체의 아키텍처 원칙("LangGraph는 진짜 멀티턴 상태
루프가 생기기 전에는 추가하지 않는다", "RAG는 단일 직군 MVP에는 추가하지 않는다" 등)이 명시되어
있습니다. 이는 참고 자료로만 취급했고, 판정 근거는 어디까지나 실제 코드 확인 결과입니다 — 결과적으로
`CLAUDE.md`의 방침과 본 평가의 결론이 대부분 일치하지만, 이는 독립적으로 재확인된 것이지 `CLAUDE.md`를
그대로 옮겨 적은 것이 아닙니다.

---

## LangGraph

**현재 제품에서 해결하려는 문제:** 공고 실사 파이프라인의 단계(추출→검증→강등→확인질문 생성)를
상태 그래프로 표현하여 실패 지점 재시도, 단계 간 상태 전이를 관리하고자 하는 수요가 있는지 평가.

**현재 코드만으로 해결 가능한가:** 그렇다. 실제 파이프라인(`audit_pipeline.py:26-107`)은 순차 함수
호출 7단계이며, 조건 분기와 재시도(`MAX_ATTEMPTS=2`)는 `for` 루프와 `if`문으로 완전히 표현되어
있다. `asyncio` 사용 0건(전체 `backend/app/` grep 결과), 공고당 요청 1건 = 동기 처리 1회
(`api/v1/postings.py:14-28`). 과제 지시서 §5가 "일반 함수·asyncio로 처리 가능한지 먼저 평가"하라고
지시한 5개 항목(공고 여러 건 병렬 분석/실패 항목 재시도/finance 입력 없으면 skip/진행 상태 표시/후보
결과 합치기) 중, **재시도만 이미 구현되어 있고**(그리고 일반 함수로 충분히 구현됨), 나머지 4개는
아직 구현 자체가 없다 — 즉 "LangGraph가 필요한데 안 썼다"가 아니라 "아직 그 기능들이 없다."

**도입 시 실질적인 이점:** 현재 없음. 여러 공고 병렬 분석이 실제로 요구사항이 되더라도 이는
`asyncio.gather`로 해결되는 fan-out이지 상태 그래프가 아니다.

**추가되는 복잡성:** 상태 그래프 정의, 체크포인터 설정, 신규 의존성, 디버깅 난이도 상승 — 현재
7단계 순차 파이프라인에는 전부 불필요한 오버헤드.

**현재 판정:** `NOT_JUSTIFIED`

**도입을 재검토할 조건:** 과제 지시서 §5가 명시한 실제 멀티턴 상태 루프 — "공고 분석 → 누락 정보
질문 생성 → 사용자가 기업 답변·계약서·추가 자료 입력 → 이전 상태 복원 → 해당 필드만 재검증 →
비교 결과 갱신" — 가 실제 기능으로 요구될 때. 현재 코드에 `session`/`resume`/`conversation` 관련
코드가 전혀 없음을 확인했으므로(grep 0건), 이 조건은 아직 발생하지 않았다.

**최소 구현안:** 해당 루프가 실제 요구사항이 되는 시점에, `VerificationAction`에 이미 존재하는
필드 단위 구조(`services/verification.py`)를 그대로 상태 노드의 단위로 재사용하는 얕은 LangGraph
그래프(필드당 1노드) — 이 문서에서는 설계만 하고 구현하지 않는다.

**평가 방법:** 새 멀티턴 루프가 구현된 시점에, 동일 시나리오를 (a) 현재 방식의 순차 함수 확장,
(b) LangGraph 그래프 두 가지로 각각 프로토타입하여 코드 라인 수·디버깅 로그 가독성·재현 가능한
실패 케이스 수를 비교.

**심사위원 설명 한 문장:** "지금은 요청 1건에 응답 1건인 무상태 API이므로, 상태를 관리해 줄
그래프 엔진 자체가 할 일이 없다."

---

## LangChain

**현재 제품에서 해결하려는 문제:** LLM 호출·구조화 출력·문서 로딩을 표준화된 래퍼로 대체할
필요가 있는지 평가.

**현재 코드만으로 해결 가능한가:** 그렇다. `ExtractionProvider`는 `typing.Protocol`(`providers/base.py:6-24`)
로 정의된 3줄짜리 인터페이스이고, Mock/Anthropic/NVIDIA 3개 구현체가 `factory.py:8,11-29`에서
환경변수로 선택된다. 구조화 출력은 Pydantic `StrictModel`(`extra="forbid"`)로 이미 처리되며
(`AI_HARNESS.md` §1), 이는 LangChain의 output parser보다 검증이 엄격하다(닫힌 스키마 + 근거 오프셋
검증까지 겸함, LangChain parser는 이 두 번째 계층을 제공하지 않음). 문서 로더는 필요 없음 — 원문은
이미 구조화된 JSON(`source_text` 필드)으로 들어온다(`datasets/loader.py`).

**도입 시 실질적인 이점:** 현재 없음. RAG가 도입되지 않은 상태(아래 §RAG)에서 LangChain의 핵심
가치(문서 로더 체인, 벡터스토어 추상화, retriever 체인)는 활용할 대상이 없다.

**추가되는 복잡성:** 신규 의존성, 버전 호환성 관리, 기존 `Protocol` 기반 provider 인터페이스와
LangChain의 `Runnable` 추상화 사이 이중 계층 발생 위험.

**현재 판정:** `NOT_JUSTIFIED`

**도입을 재검토할 조건:** RAG(문서 로더+retriever 체인)가 실제로 정당화되는 시점(§RAG 참조)이거나,
provider가 5종 이상으로 늘어나 공통 재시도/스트리밍/캐싱 로직 중복이 실측 가능한 유지보수 비용으로
드러날 때.

**최소 구현안:** 해당되지 않음(현재 추가 근거 없음).

**평가 방법:** provider 인터페이스 코드 중복 라인 수를 분기마다 측정, LangChain 도입 전후 provider
1종 추가에 걸리는 코드 변경 라인 수 비교.

**심사위원 설명 한 문장:** "지금 있는 3줄짜리 Protocol 인터페이스보다 LangChain 래퍼가 더 단순해지는
지점이 아직 없다."

---

## RAG

**현재 제품에서 해결하려는 문제:** 관심 생활권과 유사한 공고를 대규모 후보군에서 찾아내는 검색
문제가 있는지 평가.

**현재 코드만으로 해결 가능한가:** 그렇다. 현재 규모는 실공고 20건(전북 10 + 수도권 10), 매칭
쌍 10개(`REAL_DATA_ACQUISITION_HANDOFF.md:48`). `matching.py:22-71`은 occupation 정확 일치 +
employment_type 가산점 + `posting_id` 타이브레이크로 최대 3건을 반환하는 결정론적 필터이며,
전체 데이터셋이 벡터 검색 없이 선형 스캔으로 처리 가능한 규모다(모듈 docstring이 명시: "No vector
database, no live scraping"). 검색 대상 자체가 20건뿐이므로 recall/precision을 논할 표본조차
통계적으로 유의하지 않다.

**도입 시 실질적인 이점:** 현재 규모에서는 없음. 오히려 벡터 인덱스 구축·임베딩 API 호출 비용·
인덱스 동기화라는 새 실패 지점만 추가된다.

**추가되는 복잡성:** 벡터 DB 인프라, 임베딩 모델 선택/버저닝, 인덱스-원본 데이터 정합성 유지,
근거(evidence) 오프셋 검증과 벡터 검색 결과의 정합성 재확인 필요(현재 harness의 exact-substring
검증 원칙과 충돌 가능).

**현재 판정:** `NOT_JUSTIFIED`

**도입을 재검토할 조건:** 공고 수가 수백~수천 건 규모로 증가하여 (occupation, employment_type)
정확 일치 필터만으로 후보가 과도하게 많아지거나(또는 0건이 되어) 사람이 감당할 수 없는 시점.

**최소 구현안 (향후 수천 건 규모, 설계만 — 코드/의존성 미추가):**

```
전체 공고
  → 사용자 region pack 필터 (REGION_PACK_ONTOLOGY.md 참조)
  → 직무·고용형태 필터 (현재 matching.py 로직 그대로 재사용)
  → lexical 또는 semantic retrieval (신규)
  → reranking (신규)
  → 상위 후보
```

기존 결정론적 필터(region, occupation, employment_type)를 **먼저** 적용해 후보군을 좁힌 뒤에만
retrieval을 추가한다 — 처음부터 임베딩 검색으로 시작하지 않는다. 이는 현재 필터 로직을 폐기하지
않고 앞단 가지치기로 재사용하는 설계다.

**향후 평가 지표(§7 그대로):**
- Recall@3, Precision@3
- 직무 일치율, 지역 일치율, 고용형태 일치율
- 다른 직군 오매칭률

이 지표들을 계산하려면 최소 수십 건 이상의 사람 gold 라벨이 선행되어야 하며, 현재
`docs/data/AI_CONSENSUS_REVIEW.md`가 명시하듯 gold 라벨은 아직 없다(`/data/gap-stats`가
`ready:false`). 즉 RAG 도입은 데이터 규모뿐 아니라 **평가 라벨 부재**로도 아직 시기상조다.

**심사위원 설명 한 문장:** "검색 대상이 20건일 때 벡터 검색은 해결책이 아니라 새로운 문제이며,
지표를 잴 gold 라벨조차 아직 없다."

---

## MCP

**현재 제품에서 해결하려는 문제:** 외부 데이터 소스(고용24 공고, 지역 주거비, 지역 청년정책, 기업
공식 출처)에 LLM이 도구 호출로 접근해야 하는 경계가 있는지 평가.

**현재 코드만으로 해결 가능한가:** 그렇다. 현재는 로컬 파일과 내부 API만 사용한다.
`ExternalContext` 파이프라인은 항상 빈 리스트를 반환하도록 구현되어 있다(`BACKEND_HANDOFF.md:130-133`
확인, 즉 외부 조회 자체가 아직 배선되지 않음). 지역 주거비는 baseline 조회가 아니라 사용자
직접 입력(`REGION_PACK_ONTOLOGY.md` 참조)이므로 지금 이 순간 MCP로 감쌀 실제 외부 도구가 없다 —
**가짜 MCP 서버를 만들지 말라는 지시를 따라 서버를 만들지 않았다.**

**도입 시 실질적인 이점:** 향후 외부 데이터 소스가 실제로 연결되는 시점에는, provider가 이미
갖춘 fail-closed 경계(`AI_HARNESS.md` §6)와 동일한 원칙(타임아웃, 실패 시 명확한 오류, 비밀정보
비노출)을 외부 데이터 조회에도 일관되게 적용할 수 있다.

**추가되는 복잡성:** MCP 서버 프로세스 관리, 인증, 캐싱, 응답 스키마 검증 계층 이중화.

**현재 판정:** `NOT_JUSTIFIED`

**도입을 재검토할 조건:** 아래 5개 도구 중 하나라도 실제 외부 데이터 소스에 연결해야 하는 시점
(현재는 전부 로컬 큐레이션 데이터 또는 사용자 입력으로 대체 중).

**최소 구현안 (인터페이스만 설계, 서버 미구현):**

| 도구 | 목적 | 대체 중인 현재 구현 |
|---|---|---|
| `get_local_postings(region_code, occupation)` | 전북 후보 조회 | `datasets/loader.py` 로컬 파일 읽기 |
| `get_posting_detail(posting_id)` | 공고 상세 조회 | 동일 |
| `get_regional_housing_baseline(region_code)` | 지역 주거비 기준값 | 사용자 직접 입력(`FinancialOption.monthly_housing_cost`) |
| `get_regional_youth_policies(region_code)` | 지역 청년정책 조회 | 미구현(존재하지 않음) |
| `verify_company_official_source(company_id)` | 기업 공식 출처 확인 | 미구현 |

도구 설계 시 반드시 지킬 경계 (harness의 fail-closed/스키마 원칙을 그대로 계승):
- **read-only 원칙**: 위 5개 도구는 전부 조회 전용, 쓰기 도구 없음.
- **응답 출처와 조회 시각**: 모든 응답에 `source`, `as_of`(또는 `retrieved_at`) 필드 필수 —
  `REGION_PACK_ONTOLOGY.md`의 `RegionalCostBaseline.source/as_of` 설계와 동일 원칙.
- **timeout**: `AnthropicExtractionProvider`가 이미 채택한 즉시-실패 원칙(`AI_HARNESS.md` §6)을
  동일하게 적용 — 타임아웃 시 재시도하지 않고 `ProviderUnavailableError` 계열 타입화된 오류 반환.
- **provider unavailable**: 외부 소스 접근 불가 시 조용히 빈 결과를 반환하지 않고 명시적 오류
  반환(현재 `ExternalContext`가 빈 리스트를 반환하는 방식은 도구화 이후에는 지양 — "데이터 없음"과
  "조회 실패"를 구분해야 함).
- **개인정보 제거**: `scripts/annotation_ops/`가 이미 채택한 PII 정규식 스크리닝 패턴(전화번호/이메일)을
  외부 조회 응답에도 적용.
- **데이터 라이선스**: `REAL_DATA_ACQUISITION_HANDOFF.md:124-127`이 명시하듯 고용24 게시물 재배포
  권리가 미확인 상태 — `get_posting_detail`이 원문 재배포 권리 확인 전에는 `full_text`를 반환하지
  않도록 스키마 레벨에서 강제해야 함(현재 공개 JSONL도 동일 원칙으로 `full_text: null` 유지 중).
- **MCP 결과를 LLM이 임의 수정하지 못하게 하는 경계**: harness의 exact-substring 검증(`AI_HARNESS.md`
  §3)과 동일한 패턴 — MCP 도구 응답 텍스트도 evidence로 인용될 경우 원문 대비 정확 일치 검증을
  거치게 한다. 즉 MCP 계층이 추가되어도 harness의 검증 관문은 우회되지 않는다.

**평가 방법:** 실제 외부 소스 1개(예: 지역 주거비 공공데이터)가 연결되는 시점에, 위 표의 해당 도구
1개만 최소 구현하여 harness 검증 관문(스키마+출처+timeout+fail-closed)을 통과하는지 통합 테스트로
확인.

**심사위원 설명 한 문장:** "지금은 감쌀 외부 도구가 없어 MCP 서버를 만들지 않았고, 대신 나중에
만들 도구가 지켜야 할 경계만 문서화했다."

---

## Harness

상세 문서: `AI_HARNESS.md`.

**현재 제품에서 해결하려는 문제:** LLM 추출 결과를 신뢰 가능한 상태로 만드는 검증 계층이 실제로
존재하는지, 아니면 이름만 붙이면 되는지 평가.

**현재 코드만으로 해결 가능한가:** 그렇다 — 그리고 이미 해결되어 있다. 닫힌 스키마, 근거 오프셋+
부분문자열 이중 검증, 결정론적 강등, 재시도 1회 제한, provider fail-closed, 비밀정보 스크러빙,
mock/real 분리, AI 합의 평가, API 계약, 단위·통합 테스트 — 10개 항목 전부를 코드/테스트에서
file:line 단위로 확인했다(`AI_HARNESS.md` 참조).

**도입 시 실질적인 이점:** 새 프레임워크를 설치하는 것이 아니라, 이미 흩어져 있는 이 관행들을
"Evidence-Grounded Job Audit Harness"라는 하나의 이름으로 묶어 문서화함으로써, 신규 기여자가
"이 프로젝트가 왜 안전한가"를 하나의 문서에서 확인할 수 있게 된다.

**추가되는 복잡성:** 없음 — 코드 변경이 수반되지 않는 순수 문서화 작업이다.

**현재 판정:** `IMPLEMENT_NOW` (단, "구현"은 "새로 만든다"가 아니라 "이미 있는 것을 공식 정의하고
문서화한다"는 의미)

**도입을 재검토할 조건:** 해당 없음 — 이미 코드로 구현되어 있고 테스트로 검증되어 있음.

**최소 구현안:** `AI_HARNESS.md` 자체가 최소 구현안이다. 추가 코드 없음.

**평가 방법:** `pytest tests/backend/` 실행 결과(전 항목 pass)를 문서의 신뢰 근거로 사용.

**심사위원 설명 한 문장:** "Harness는 새로 설치한 프레임워크가 아니라, 이미 통과하고 있는 테스트
스위트에 붙인 이름이다."

---

## Ontology

상세 문서: `REGION_PACK_ONTOLOGY.md`.

**현재 제품에서 해결하려는 문제:** `PostingField`(6개 항목 + confirmed/vague/absent + evidence +
verification action)와, 아직 없는 `RegionPack`(지역별 데이터/기준값 묶음) 구조를 표현할 최소
타입 체계가 필요한지 평가.

**현재 코드만으로 해결 가능한가:** `PostingField` 서브그래프는 그렇다 — 이미 Pydantic 모델 +
YAML 룹릭(`field_rules.yaml`)으로 완전히 표현됨. `RegionPack` 서브그래프는 아니다 — 해당 타입이
아직 존재하지 않고, region이 3곳에 흩어진 문자열 리터럴로만 존재한다(`REGION_PACK_ONTOLOGY.md`
대응표 참조).

**도입 시 실질적인 이점:** `PostingField` 부분은 이미 확보됨(추가 이점 없음, 이미 있음). `RegionPack`
부분은 enum 하나 + Pydantic 모델 하나로 지역 코드 오타/불일치를 컴파일/검증 시점에 차단하고,
전국 확장 시 "엔진 유지, region pack만 교체"라는 과제 목표를 코드 구조로 강제할 수 있게 된다.

**추가되는 복잡성:** `RegionCode` enum 추가 자체는 낮은 복잡성이나, 기존 3개 하드코딩 지점을
전부 교체하는 리팩터링이 수반됨(회귀 테스트 필요).

**현재 판정:** `PostingField` 서브그래프는 `IMPLEMENT_NOW`(이미 구현되어 있으므로 문서화만),
`RegionPack` 서브그래프는 `NEXT_STAGE`(아직 없으므로 최소 설계만 제시, 코드 미작성).

**도입을 재검토할 조건 (RegionPack 그래프 확장 관련):** 지역이 3개 이상, 또는 지역 간 관계에
조건부 로직(통근권/생활권 인접성 등)이 붙기 시작할 때 — 현재는 지역 2개, 단방향 비교 관계 1개뿐.

**최소 구현안:** `REGION_PACK_ONTOLOGY.md`의 `RegionCode`/`RegionalCostBaseline`/`RegionPack`
Pydantic 설계 참조. 그래프 DB/RDF 엔진 불필요.

**평가 방법:** `RegionCode` 도입 전후로 기존 20건 데이터셋에 대한 `matching.py`/`finance.py` 출력이
동일한지 golden test로 검증.

**심사위원 설명 한 문장:** "채용정보 온톨로지는 이미 Pydantic으로 구현되어 있고, 지역 온톨로지는
아직 없어서 enum 하나짜리 최소 설계만 제시했다."

---

## 멀티 에이전트

**현재 제품에서 해결하려는 문제:** 추출/매칭/재정/검증/비평 역할을 별도 LLM 에이전트로 분리했을 때
정확도가 개선되는지 평가.

**현재 코드만으로 해결 가능한가:** 그렇다, 그리고 현재 구조가 더 낫다.
- **재정 계산**은 결정론적 순수 함수(`finance.py`, "No LLM involvement" — LLM으로 대체할 이유가 없음,
  오히려 대체하면 정확도가 낮아짐).
- **매칭**은 소규모 데이터(20건)와 명시적 규칙(occupation 정확 일치 + employment_type 가산점)이며,
  LLM 에이전트를 세워도 이 규칙보다 정확하거나 일관될 근거가 없다.
- **검증**은 이미 Harness가 담당(`AI_HARNESS.md`) — 결정론적 강등 규칙이 "비평 에이전트" 역할을
  대체하고 있으며, 이는 LLM 기반 비평보다 재현 가능하고(같은 입력 → 같은 출력) 감사 가능하다.
- **추출**만 LLM(provider)이 담당하며, 이는 이미 그 자체로 1개 역할 = 1개 provider 호출로 최소화되어
  있다.

**도입 시 실질적인 이점:** 증명되지 않음. 정확도 개선을 증명할 평가 설계(예: 단일 provider 파이프라인
vs 멀티 에이전트 파이프라인을 동일 20건 데이터셋 + gold 라벨로 A/B 비교)가 현재 존재하지 않고,
gold 라벨 자체도 아직 없다(`/data/gap-stats` `ready:false`).

**추가되는 복잡성:** 에이전트 간 전달 과정에서 근거(evidence span)가 손실될 위험 — 현재 harness의
핵심 원칙(원문 대비 exact-substring 검증)은 정보가 에이전트를 거칠 때마다 재검증되어야 안전한데,
에이전트 홉이 늘어날수록 근거 유실 지점이 늘어난다. 비용도 provider 호출 횟수에 비례해 증가하고,
디버깅 시 "어느 에이전트에서 틀렸는가"를 추적하는 난이도가 상승한다.

**현재 판정:** `NOT_JUSTIFIED`

**도입을 재검토할 조건:** (1) 사람 gold 라벨이 확보되어 정확도 비교가 가능해지고, (2) 단일
provider 파이프라인의 오류 사례를 분석한 결과 "역할 분리로만 해결 가능한" 오류 패턴이 실제로
발견될 때. 현재는 두 조건 다 충족되지 않음.

**최소 구현안:** 해당 없음(정확도 개선이 증명되기 전까지 구현 자체를 보류).

**평가 방법:** gold 라벨 확보 후, 동일 20건(또는 확장된 데이터셋)에 대해 단일 provider 파이프라인과
역할 분리 파이프라인의 필드별 정확도·evidence 정확 일치율·비용(호출 횟수)·지연시간을 나란히 측정.

**심사위원 설명 한 문장:** "결정론적으로 풀리는 문제(재정, 매칭, 검증)에 LLM 에이전트를 추가로
세우는 것은 정확도를 높이지 않고 근거 손실 위험과 비용만 늘린다."

---

## 판정 비교표: 예상치 대비 실제 판정

| 기술 | 과제 지시서 §12 예상치 | 본 평가 최종 판정 | 달라진 부분 |
|---|---|---|---|
| Harness | IMPLEMENT_NOW | IMPLEMENT_NOW | 동일. 단, 10개 체크리스트 전항목을 file:line 단위로 실제 확인함 |
| Ontology | IMPLEMENT_NOW 또는 NEXT_STAGE | **분리 판정**: PostingField=IMPLEMENT_NOW, RegionPack=NEXT_STAGE | 예상치는 Ontology를 하나로 뭉뚱그렸으나, 실제로는 하위 두 서브그래프의 구현 상태가 완전히 다름(하나는 이미 완성, 하나는 존재 자체가 없음) — 이를 코드로 확인 후 분리 판정함 |
| LangGraph | NEXT_STAGE | NOT_JUSTIFIED | 예상치보다 한 단계 낮춤. 재검토 조건(멀티턴 상태 루프)이 코드에 전혀 없음을 grep으로 확인(0건) — "다음 단계 대비"보다 "아직 필요성 자체가 없음"이 정확한 서술 |
| RAG | NEXT_STAGE | NOT_JUSTIFIED | 예상치보다 한 단계 낮춤. 이유는 데이터 규모(20건)뿐 아니라 **평가 지표를 계산할 gold 라벨이 아직 없다**는 점까지 확인했기 때문 — gold 없이는 "다음 단계"조차 착수할 수 없음 |
| MCP | NEXT_STAGE | NOT_JUSTIFIED | 예상치보다 한 단계 낮춤. `ExternalContext`가 이미 빈 리스트를 반환하는 자리로 배선되어 있음을 확인했으나, 감쌀 실제 외부 도구가 0개이므로 "다음 단계"라기보다 "아직 대상이 없음"이 정확 |
| LangChain | NEXT_STAGE 또는 NOT_JUSTIFIED | NOT_JUSTIFIED | 예상치 범위 내 하단으로 확정. RAG가 정당화되지 않으므로 LangChain의 핵심 가치(retriever 체인)도 정당화 근거가 없음 |
| 멀티 에이전트 | NOT_JUSTIFIED | NOT_JUSTIFIED | 동일. 근거를 "비용 증가" 수준의 일반론이 아니라 재정/매칭이 이미 결정론적 함수임을 코드로 확인한 구체적 근거로 대체함 |

전반적으로 본 평가는 예상치보다 **더 보수적**입니다. LangGraph/RAG/MCP를 예상치(NEXT_STAGE)보다
낮춰 NOT_JUSTIFIED로 판정한 이유는, "다음 단계"라는 표현이 암시하는 "곧 도입할 준비 단계"가 아니라
"도입을 정당화할 조건 자체가 아직 발생하지 않았다"는 것이 코드 확인 결과와 더 정확히 일치하기
때문입니다.

---

## 심사 대응

**1. 왜 LangGraph를 쓰지 않았나요?**
현재 API는 요청 1건에 응답 1건인 무상태 파이프라인이다(`contracts/openapi.json` 5개 엔드포인트
전부 동기 REST, 세션/웹소켓 없음). LangGraph가 값어치를 내는 지점은 여러 턴에 걸쳐 상태를 복원·
갱신하는 루프인데, 그런 루프(기업 추가 답변 입력 → 이전 상태 복원 → 해당 필드만 재검증)가 코드에
전혀 존재하지 않는다(`session`/`resume`/`conversation` grep 0건). 없는 문제에 도구를 먼저 들이지
않았다.

**2. 왜 RAG를 쓰지 않았나요?**
검색 대상이 실공고 20건뿐이다(`REAL_DATA_ACQUISITION_HANDOFF.md:48`). 이 규모에서 (occupation,
employment_type) 정확 일치 필터가 이미 최대 3건의 후보를 정확하게 반환하고 있고, Recall@3 같은
지표를 계산할 사람 gold 라벨조차 아직 없다. 벡터 검색을 추가해도 검증할 방법이 없는 상태에서
인프라만 늘리는 것은 정당화되지 않는다.

**3. 이것을 왜 에이전트라고 부를 수 있나요?**
"에이전트"라는 단일 LLM 대화 세션이 아니라, LLM 호출(추출) → 결정론적 검증(스키마/근거/강등) →
결정론적 행동 생성(확인 질문/재정 비교)으로 이어지는 **관찰-검증-행동 루프**로서 그렇게 부를 수
있다. 다만 오늘 이 루프는 1회성이며(요청당 1회 실행, 상태 유지 없음), "멀티턴 자율 에이전트"라는
강한 의미로는 아니다 — 이 구분을 본 문서가 의도적으로 명확히 했다.

**4. 단순 LLM API 호출과 무엇이 다른가요?**
단순 API 호출은 LLM의 출력을 그대로 신뢰한다. 이 시스템은 LLM 출력을 6단 관문(`AI_HARNESS.md`)에
통과시킨다: 닫힌 스키마 거부, 원문 대비 정확 일치 근거 검증, 결정론적 강등(LLM이 confirmed라고
말해도 규칙 미달이면 무조건 강등), 재시도 1회 제한, 실패 시 값을 지어내지 않고 타입화된 오류 반환,
비밀정보 스크러빙. 이 중 어느 하나라도 실패하면 LLM의 응답은 최종 결과에 반영되지 않는다.

**5. Harness는 실제로 어디에 구현돼 있나요?**
`backend/app/services/audit_pipeline.py`(오케스트레이션), `services/evidence.py`(근거 검증),
`rules/field_rules.py` + `field_rules.yaml`(결정론적 강등 규칙), `models/common.py`(닫힌 스키마),
`providers/*.py`(fail-closed + 비밀정보 스크러빙). 전항목이 `tests/backend/`의 대응 테스트로
검증됨 — 상세 file:line은 `AI_HARNESS.md` 참조.

**6. Ontology가 단순 enum과 다른 점은 무엇인가요?**
`PostingField`는 단순 enum이 아니라, enum(`status`) + 근거(`EvidenceSpan`) + 파생 행동
(`VerificationAction`)이 하나의 타입 안에서 서로 참조 관계를 이루는 구조다 — status가 vague/absent면
반드시 VerificationAction이 생성되는 관계가 Pydantic 모델 조립 코드(`audit_pipeline.py:90-97`)에
강제되어 있다. `RegionPack`은 아직 이 수준으로 구현되어 있지 않으며, 본 문서는 그 갭을 숨기지 않고
명시했다.

**7. 데이터가 전국으로 커지면 어떻게 확장하나요?**
`REGION_PACK_ONTOLOGY.md`의 최소 구현안대로 `RegionCode` enum과 `RegionPack` 모델을 도입하면,
`matching.py`/`finance.py`/`audit_pipeline.py`(엔진)는 변경하지 않고 지역별 `RegionPack` 인스턴스
(데이터 파일 경로 + 주거비 baseline)만 추가하는 구조로 확장한다. 데이터 규모가 수천 건이 되면
RAG 최소 파이프라인(§RAG)을 region/occupation 필터 **뒤**에 얹는다 — 처음부터 임베딩 검색으로
시작하지 않는다.

**8. 다른 지역으로 확장하면 전북 문제 해결 효과가 약해지지 않나요?**
현재 시스템은 "전북 vs 수도권"이라는 단일 비교를 하드코딩하지 않고, occupation/employment_type
기준 결정론적 매칭 + 사용자 입력 기반 재정 비교라는 **일반 로직**으로 구현되어 있다(지역명이
로직에 특권적으로 반영된 곳은 하드코딩된 리터럴 3곳뿐이며, 이는 이번 문서의 `RegionCode` 설계로
제거될 예정). 따라서 다른 지역을 추가해도 전북 로직 자체가 희석되지 않는다 — 오히려 전북은
`RegionPack` 인스턴스 중 하나가 되고, 전북 특화 UX(현재 데모 시나리오)는 프론트엔드 설정으로
유지 가능하다. 다만 현재 수도권 10건 데이터가 전부 인천/경기이고 서울 소재가 0건이라는 점
(`REAL_DATA_ACQUISITION_HANDOFF.md:182-186`)은 전국 확장 이전에 데이터 수집 단계에서 먼저
해소해야 할 별도 문제다.

**9. 로그인 지역 기반 추천이 개인정보 침해가 되지 않나요?**
현재 코드에는 로그인/세션/사용자 프로필 저장 기능이 없다(`CURRENT_SYSTEM_FLOW.md` §1 — `<LogIn>`은
장식용 아이콘일 뿐). "고용24 로그인 데모"는 아직 구현되지 않은 시연 서사이며, 실제로 구현될 때는
현재 harness가 이미 채택한 개인정보 제거 관행(`scripts/annotation_ops/`의 PII 정규식 스크리닝,
`AI_HARNESS.md` §7의 비밀정보 스크러빙과 동일 계열)을 사용자 프로필에도 동일하게 적용해야 한다는
점을 본 문서의 MCP 섹션에 명시했다. 현재는 해당 기능이 없으므로 침해 여부를 평가할 대상 자체가
없다.

**10. 멀티 에이전트를 쓰지 않은 이유는 무엇인가요?**
재정 계산은 결정론적 함수이고(`finance.py`, LLM 미개입), 매칭은 명시적 규칙 기반이며(`matching.py`),
검증은 이미 Harness가 담당한다. 이 세 영역에 LLM 에이전트를 추가로 세워도 정확도가 개선된다는
근거(gold 라벨 기반 A/B 비교)가 없고, 오히려 에이전트 간 전달 과정에서 원문 근거(evidence span)가
손실될 위험과 비용만 늘어난다. 정확도 개선이 실측되기 전까지는 도입하지 않는 것이 옳은 판단이다.

---

## 요약

새로 추가된 코드/의존성 없음. 본 문서 세트는 `backend/app/**`가 이미 구현하고 있는 검증 관행을
"Harness"로 명명·문서화하고, 아직 없는 `RegionPack` 구조의 최소 설계를 제시했으며,
LangGraph/RAG/MCP/LangChain/멀티 에이전트는 전부 도입 조건 미충족으로 판정했습니다.
