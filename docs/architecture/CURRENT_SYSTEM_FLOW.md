# Current system flow (work24-ai-extension-layer)

Describes the actual end-to-end flow as implemented on
`feature/work24-ai-extension-layer`, framed as an **extension of** 고용24's
existing AI추천/잡케어 flow rather than a separate competing product (TASK
"고용24 기존 AI 서비스 위에 지역 의사결정 에이전트 확장 레이어 구현").

## Screen flow

```text
고용24 로그인 데모                         (src/lib/demoAuth.ts, localStorage-only)
  → 잡케어 관심직무 표시 (시연용 프로필)      (JobCareProfilePanel.tsx)
  → 고용24 AI추천 수도권 공고                (AiJobRecommendPage.tsx -> GET /postings/home-region-listing)
  → 지역 선택 보정 에이전트 활성화            (InlineJeonbukAgentPanel.tsx, per-card toggle)
  → 비교 가능한 전북 공고                    (POST /postings/home-region-matches)
  → 중요조건 선택 (최대 3개)                 (ImportantConditionsSelector.tsx)
  → 근거 기반 6개 축 비교                    (comparisonAxes.ts + ComparisonAxesPanel.tsx)
  → 중요한 미확인 정보                       (priorityUnresolved.ts + PriorityUnresolvedPanel.tsx)
  → 1년·3년 정착 시나리오                    (FinanceComparisonPanel.tsx -> POST /finance/compare)
  → 조건 역전점                             (backend crossover + financeCrossovers.ts)
  → 지원 전 확인 질문                        (CompanyQuestionsPanel.tsx)
```

A small ①②③④ step strip (`ServiceStepIndicator.tsx`) is rendered twice:
once at the page level (step ① before login, step ② after login), and
again inside each expanded posting card (step ③ while matching/selecting a
candidate, step ④ once both postings' analyses have succeeded). It never
gates navigation -- it is purely a "where am I in the 고용24 flow" marker,
reinforcing that this is one continuous flow, not a separate tool.

## Why this reads as an extension, not a separate platform

1. **Same page, same list.** The region comparison agent only ever appears
   as a per-card expansion (`내 지역 비교 공고 보기`) inside the existing
   AI추천 posting list -- there is no separate route, nav item, or
   standalone "paste your posting here" tool for the demo login path (the
   original manual-paste flow still exists at `/manual-analysis`, unchanged,
   for direct testing/demo convenience, and is linked only as a small
   secondary link at the bottom of the page).
2. **Explicit differentiation copy**, collapsed by default
   (`ServiceDifferentiationNotice.tsx`) so the first screen isn't cluttered:
   고용24 AI추천 = "사람과 일자리의 적합성을 분석"; 지역 선택 보정 에이전트 =
   "수도권과 자기 지역 일자리의 비교 가능성을 분석". A second comparison
   distinguishes this from 고용24's *existing* AI 구인공고 검증 (law-violation
   language/wage checks) versus this feature's information-sufficiency
   checks.
3. **잡케어 hand-off is explicitly a demo stand-in.** `JobCareProfilePanel.tsx`
   never calls a real JobCare API and never fabricates 취업확률/역량점수/
   심리검사 -- see `docs/architecture/EXPANSION_TECH_ASSESSMENT.md` section 10
   for what a real integration's data flow would look like.

## Current MVP matching vs. a future 고용24 integration

**This section exists because the wording used to matter here got sloppy
once ("real, curated 10:10 matched-pair batch") and needs a permanent,
explicit split between what is actually implemented today and what a real
고용24 integration would look like** (TASK "데모 매칭 표현 정직화 및 현재/확장
구조 분리"). Do not blur these two into one description again.

### Current MVP (implemented, `feature/demo-matching-transparency` and earlier)

```text
고용24 로그인 화면 재현
→ 고용24 AI추천 목록 재현
→ 수도권 공고 선택
→ 기록된 직종·고용형태가 같은 전북 공고를 사전 계산된 1:1 연결표에서 조회
   (data/intake/real_matched_pairs.jsonl, scripts/acquisition/pair_postings.py)
→ 수집 순서에 따른 결정론적 1:1 연결 (유사도 검색도, 사람의 큐레이션도 아님)
→ 기존 6필드 분석
→ Evidence Harness 검증
→ 조건 비교
→ 미확인 정보 질문
→ 선택적 정착 시나리오
```

Not present in this path today, and never claimed to be:

```text
고용24 공식 jobsCd/empTpCd
실시간 고용24 API 호출
담당업무·기술 기반 자동 후보 검색 또는 유사도 점수
복수 후보 자동 추천 (현재 배치는 metro posting당 jeonbuk 후보 최대 1건)
NCS 코드 자동 매핑
LangGraph / RAG / MCP / 멀티 에이전트
```

`data/intake/real_matched_pairs.jsonl` is a data-acquisition-time adapter
built to work around 고용24 API access limits and to keep the demo stable
(`scripts/acquisition/pair_postings.py` groups postings by an exact match
on the recorded `occupation`/`employment_type` strings and pairs them 1:1
in collection order) -- it is not a claim that this is how candidate
retrieval should work at scale, and it is not a similarity or ranking
algorithm of any kind.

### Future: real 고용24 integration (not implemented, planning only)

```text
고용24 기존 AI가 개인 맞춤 공고 추천
→ 로그인 생활권으로 지역 후보 제한
→ 고용24 공식 jobsCd/empTpCd로 1차 후보 조회       (jobsCd/empTpCd do not exist in this MVP's data)
→ 경력·자격 등 명백한 조건 충돌 제거
→ 공고 원문의 업무·기술·진입조건 비교
→ 비교 가능한 지역 후보 복수 제공                  (planned, NOT implemented)
→ 조건 차이와 미확인 정보 설명
```

The pre-computed pair table above is exactly the piece a real integration
would replace with an automatic candidate-retrieval service driven by
official codes -- everything downstream of "비교 가능한 전북 공고" (the
six-field analysis, evidence harness, comparison, questions, finance
scenario) is unaffected by which retrieval method feeds it a posting_id
pair, and needs no change either way.

## Backend

The listing/matching/analysis/finance endpoints, the six-field
evidence-grounded harness, and the server-enforced home-region scoping
(`DEMO_HOME_REGION`) are exactly as documented in
`docs/architecture/AI_HARNESS.md` and
`docs/architecture/REGION_PACK_ONTOLOGY.md`. `feature/work24-ai-extension-layer`
touched no backend file at all (presentation-layer only). This branch
(`feature/demo-matching-transparency`) makes one backend change, wording-only:
`backend/app/services/real_postings.py`'s module/function docstrings and its
`REAL_DATASET_DESCRIPTION` string (the text actually shown to users under
the candidate list) were rewritten to state the deterministic
occupation/employment-type-match-plus-collection-order pairing accurately,
instead of the earlier "curated...matched-pair batch" phrasing that could
read as human-curated similarity matching. No field, type, enum, or route
was added, removed, or renamed -- `contracts/schema.json`/`openapi.json`
have zero diff from this branch.
