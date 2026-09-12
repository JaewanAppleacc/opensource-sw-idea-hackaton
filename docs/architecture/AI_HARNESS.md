# Evidence-Grounded Job Audit Harness

이 문서는 새 프레임워크를 도입하자는 제안이 아니라, `backend/app/` 안에 **이미 구현되어 있는** 검증
파이프라인을 "Harness"라는 이름으로 공식 정의하고 문서화하는 문서입니다. 코드/테스트를 근거로 검증
가능한 사실만 기술하며, 과제 지시서 §9의 10개 체크리스트를 그대로 절 제목으로 사용합니다.

기준 브랜치: `origin/feature/home-visual-fidelity`. 전체 흐름 요약은 `CURRENT_SYSTEM_FLOW.md` §3 참조.

## 정의

**Evidence-Grounded Job Audit Harness**: LLM이 산출한 채용공고 구조화 추출 결과를, (1) 닫힌 스키마,
(2) 원문 대비 정확 일치 근거 검증, (3) 결정론적 강등 규칙, (4) 제한된 재시도, (5) 실패 시 폐쇄형
오류 처리, (6) 비밀정보 스크러빙의 6단 관문을 거쳐야만 응답으로 내보내는 결정론적 검증 계층.
LLM의 자기 신고(self-report)를 신뢰하지 않고, 모든 최종 판정은 검증 가능한 규칙이 내린다.

---

## 입력부터 최종 응답까지 — 검증 단계 (파이프라인 순서)

```
원문 공고 텍스트 (source_text)
      │
      ▼
[1] Provider.extract(source_text, expected_occupation) → dict
      providers/base.py:6-24 (Protocol), factory.py:8,11-29 (env 기반 선택)
      │
      ▼
[2] RawExtraction.model_validate(dict)  — 닫힌 스키마 검증
      extra="forbid" 강제, 정의되지 않은 필드/오탈자 필드 즉시 거부
      models/common.py:45-48 (StrictModel), posting.py:11,25,41,48,54
      실패 시 ↓ [4]로
      │
      ▼
[3] validate_evidence_span(source_text, evidence_text, start, end) — 필드별
      source_text[start:end] == evidence_text 정확 일치 (오프셋+부분문자열 이중 검증)
      services/evidence.py:15-24, 구조적 검증 models/common.py:58-64
      실패 시 EvidenceMismatchError → [4]로
      │
      ▼
[4] 재시도 (최대 1회, 총 시도 2회)
      audit_pipeline.py:23 (MAX_ATTEMPTS=2), 30-43행
      2회 모두 실패 → AnalysisFailedError (45-49행, 타입화된 실패, 값 추측/생성 없음)
      │
      ▼
[5] evaluate_confirmed() — 결정론적 강등 규칙 (LLM 미개입)
      rules/field_rules.py:71-104, YAML 룹릭 field_rules.yaml 기반
      관련 없음 → absent (63-72행) / 관련 있으나 기준 미달 → vague (80-88행)
      상태는 "절대 상향되지 않음, 절대 지어내지 않음" (audit_pipeline.py:4-7 docstring)
      │
      ▼
[6] AuditedField + ValidationWarning 조립 (90-95행)
      │
      ▼
[7] VerificationAction 생성 — vague/absent 필드만, 고정 템플릿
      audit_pipeline.py:96-97, services/verification.py
      │
      ▼
[8] PostingAnalysis 조립 + 6필드 전원 존재 재검증 (99-107행, models/posting.py:63-71)
      │
      ▼
응답 (API 계약: contracts/schema.json, openapi.json)
```

---

### 1. Pydantic closed schema / `extra="forbid"`

`StrictModel(BaseModel)`이 `model_config = ConfigDict(extra="forbid")`을 선언(`models/common.py:45-48`)하고,
`PostingInput`/`AuditedField`/`EvidenceSpan`/`VerificationAction`/`PostingAnalysis` 등 모든 도메인
모델이 이를 상속(`models/posting.py:11,25,41,48,54`). LLM 툴콜 경계에서도 원시 JSON Schema에
`"additionalProperties": false`를 명시(`providers/anthropic_provider.py:35,48`)하여 스키마 밖 필드를
프롬프트 레벨에서도 차단.

**테스트**: `tests/backend/test_models.py`에 `pytest.raises(ValidationError)` 10개소(12-77행).

### 2. Evidence offset 검증

`services/evidence.py:15-24`의 `validate_evidence_span`이 `start`/`end` 범위를 먼저 검사하고,
`EvidenceSpan` 모델(`models/common.py:58-64`)이 `end - start == len(text)` 구조적 제약을 추가로 건다.

**테스트**: `tests/backend/test_evidence.py:10-33` — 정상 span, out-of-bounds, `end<=start` 케이스 포함.

### 3. Exact substring 검증

같은 함수(`evidence.py:15-24`)가 `source_text[start:end] == evidence_text` 완전 일치를 요구 —
LLM이 원문을 의역/요약한 텍스트는 근거로 인정되지 않음. 불일치 시 `EvidenceMismatchError`.

**테스트**: `test_evidence.py`에 "지어낸 텍스트", "맞는 텍스트인데 오프셋이 틀림" 케이스 각각 포함.

### 4. 결정론적 강등(downgrade)

`rules/field_rules.py:71-104`(`evaluate_confirmed`)가 LLM 호출 없이 YAML 룹릭(`field_rules.yaml`)만으로
판정. 오케스트레이션은 `audit_pipeline.py:60-88`. `confirmed`로 자기 신고된 필드라도 규칙을 통과하지
못하면 `vague`/`absent`로 강등되며, 반대 방향(격상)은 코드 상 경로 자체가 없음.

**테스트**: `test_audit_pipeline.py:162` `test_irrelevant_real_evidence_is_downgraded_to_absent_by_deterministic_rule`
— `reason_code == "no_relevant_keyword"`와 `downgraded_to_absent` 경고를 명시적으로 assert.

### 5. 재시도 최대 1회

`audit_pipeline.py:23` `MAX_ATTEMPTS = 2`(최초 1회 + 재시도 1회), `ValidationError`/`EvidenceMismatchError`에서만
재시도(30-43행). 2회 모두 실패 시 `AnalysisFailedError`(45-49행).

**테스트**: `test_audit_pipeline.py:91,111,134,148`이 `provider.calls == 2`를 assert. `:188`
`test_provider_recovers_after_one_retry`는 재시도가 실제로 유효함을 증명.

### 6. Provider fail-closed

두 지점에서 확인됨. (a) 알 수 없는 `LLM_PROVIDER` 설정 → `ProviderUnavailableError`, mock으로
조용히 폴백하지 않음(`providers/factory.py:23-29`). (b) 요청/네트워크/SDK 예외는 모두
`ProviderUnavailableError`로 재포장되어 전파되며, 이 예외는 **재시도 대상이 아님**
(`anthropic_provider.py:96,103-115`).

**테스트**: `test_audit_pipeline.py:203` `test_provider_unavailable_propagates_without_retrying`이
`provider.calls == 1`을 assert (재시도 없이 즉시 실패 전파). `test_provider_factory.py:27-59`의
`test_unknown_or_mistyped_provider_fails_closed_not_mock`도 동일 원칙 검증.

**실환경 증거**: `docs/validation/LIVE_LLM_SMOKE.md` Phase C — 실제 Anthropic provider로
`GET /health`가 `provider_mode: "anthropic"`을 반환한 뒤, 계정 크레딧 부족으로 `POST /analyze`가
`503 provider_unavailable`을 반환. 이는 목(mock)이 아니라 실제 운영 환경에서 fail-closed 경로가
작동한 직접 증거임(코드 결함이 아니라 빌링 문제로 도달한 정상 실패 경로).

### 7. 비밀정보(secret) 스크러빙

`anthropic_provider.py:68-76`의 `_scrub_secret(message, secret)`이 예외 메시지에서 API 키 리터럴을
`[REDACTED]`로 치환. `nvidia_provider.py`도 동일 함수 재사용(25행 import, 92행 적용).

**테스트**: `test_provider_factory.py:66` `test_anthropic_error_message_never_contains_the_configured_key`,
`:88`에 NVIDIA 동일 테스트.

**실환경 증거(중립적으로 기재)**: `LIVE_LLM_SMOKE.md`에 `.env` 파싱 오류로 디버깅 중 키가 툴 출력에
한 차례 노출된 사고가 자체 기록되어 있음 — 즉시 키 로테이션 후 `grep -inE "sk-ant|authorization|x-api-key"`로
서버 stdout에 잔존 노출이 없음을 재확인. 완전무결 기록이 아니라 "사고 발생 → 즉시 탐지 → 로테이션 →
사후 검증"이 실제로 작동했다는 증거로 인용.

### 8. mock/real mode 분리

`ExtractionProvider`는 `typing.Protocol`(`providers/base.py:6-24`). 구현체 3종: Mock/Anthropic/NVIDIA,
`factory.get_provider()`가 `settings.llm_provider`(환경변수 기반)로 선택(`factory.py:8,11-29`).

**테스트**: `test_provider_factory.py:27-59` — 미설정 시 mock 기본값, 명시적 mock/anthropic/nvidia 라우팅
모두 검증.

### 9. AI consensus 평가

`docs/data/AI_CONSENSUS_REVIEW.md`: 독립 AI 리뷰 패스 2개(A/B)가 20건×6필드=120셀에 대해
`suggested_status`를 각각 산출, 113/120(94.2%) 일치, 불일치 7건은 `scripts/annotation_ops/build_ai_consensus.py`의
`HUMAN_ADJUDICATIONS` 딕셔너리(34-98행)에 룹릭을 인용한 사람 판단으로만 해소 — 매칭되는 사람 판단이
없으면 `ValueError`(139행)로 실패("추측해서 해소하지 않음"). 이 병합 로직 자체는 **런타임에 LLM을
전혀 호출하지 않는** 순수 결정론적 Python(`prepare_adjudication.py:23`: "No LLM is used anywhere in
this file." grep으로 7개 파일 전체에서 `openai`/`anthropic`/`api_key` 등 0건 확인).

문서 자체가 "이는 모델 정확도 지표가 아니라 AI 리뷰 패스 간 일치율일 뿐이며, gold 라벨과의 비교가
아니다"(21-23행)라고 명시하고, "상태값만 비교했으므로 실제 독립성을 과대평가한다"는 한계도 자체
공개(91-97행) — 과장 없는 평가 문화의 증거로 인용 가능.

### 10. API 계약 생성

`contracts/schema.json`(1753행), `contracts/openapi.json`(1181행) — 5개 엔드포인트, 모든 모델의
필드/enum/타입이 코드의 Pydantic 모델과 1:1 대응. 계약이 코드에서 생성되므로 문서와 구현의
드리프트 위험이 구조적으로 낮음.

### 11. 단위·통합 테스트

`tests/backend/`: 17개 파일, 1173행. 위 1-8번 각 항목마다 명시적 assertion을 가진 테스트가 존재함을
개별 확인(표 아님, 각 절에 인용). `tests/annotation_ops/`: 6개 파일, 1125행 — AI 합의 병합, 패킷
빌드, private-source 조인, 리뷰 CLI 교차 어노테이터 격리(`test_run_review_session_never_reads_other_annotator_or_ai_suggestion_data`),
패킷 검증(어노테이터 ID 오염, AI 제안 키 유출, evidence 오프셋 불일치)까지 커버. 확인 과정에서
"체크리스트 항목인데 테스트가 없는" 갭은 발견되지 않았음.

---

## 결론

위 1-11번 전부가 코드/테스트에 실제로 존재함을 확인했습니다. 이 Harness는 새 프레임워크 설치가
아니라 **이미 있는 구조의 명명(naming)과 문서화**이며, `EXPANSION_TECH_ASSESSMENT.md`에서 Harness
항목의 판정은 `IMPLEMENT_NOW`(단, "구현"의 의미는 "지금 이 문서로 공식화"이지 "새로 만든다"가 아님)로
유지됩니다.
