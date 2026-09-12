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
   as a per-card expansion (`내 지역 유사 일자리 보기`) inside the existing
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

## Backend (unchanged on this branch)

No backend file was modified for this task. The listing/matching/analysis/
finance endpoints, the six-field evidence-grounded harness, and the
server-enforced home-region scoping (`DEMO_HOME_REGION`) are exactly as
documented in `docs/architecture/AI_HARNESS.md` and
`docs/architecture/REGION_PACK_ONTOLOGY.md`. This branch is presentation-layer
only: it re-labels and re-groups what the backend already returns, and never
mutates a `confirmed/vague/absent` status or invents a fourth backend value.
