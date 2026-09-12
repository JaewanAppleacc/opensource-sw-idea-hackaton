# Expansion technology feasibility assessment

Read alongside `CLAUDE.md`'s architecture constraints (no LangGraph unless
a genuine multi-turn stateful loop exists, no RAG for the single-occupation
MVP, no product-level multi-agent system) and `docs/data/AI_CONSENSUS_REVIEW.md`
(the "Harness" evidence below overlaps with what that document reports).

**This document evaluates; it does not implement.** No new dependency was
added to `package.json` or `requirements.txt` as a result of writing this.
Judgments use exactly three values: `IMPLEMENT_NOW`, `NEXT_STAGE`,
`NOT_JUSTIFIED`. Using a framework is never treated as evidence for itself.

---

## 1. LangGraph

1. **Problem this would solve.** A genuine multi-turn state loop: analyze
   → generate a verification question → user/company supplies an answer →
   re-verify only that field → update the comparison, preserving prior
   state across turns.
2. **Solvable with current structure?** Yes, for everything actually built
   in this branch. Every request in this codebase (`analyze`,
   `analyze-by-id`, `match`, `home-region-matches`, `finance/compare`)
   starts and finishes inside one HTTP call with no cross-request state.
   The inline agent's two analyze calls
   (`src/components/ai-job-recommend/InlineJeonbukAgentPanel.tsx`) run via
   plain `Promise.allSettled`, not a graph. A state machine library adds
   nothing to code that has no state to hold between requests.
3. **Real benefit if added anyway.** None today. LangGraph's value is
   checkpointed, resumable, branching state across turns — there is no
   such state in this branch.
4. **Complexity/failure risk.** A new dependency, a new execution model to
   reason about and test, and a mismatch with the rest of the codebase's
   plain-function style (`backend/app/services/*.py`) for zero behavioral
   gain.
5. **Verdict: `NOT_JUSTIFIED`** for this branch's actual scope.
6. **Adoption condition.** Only once the specific loop in section 8 of the
   task brief is actually built: a real "확인 질문 → 기업/사용자 응답 입력 →
   해당 항목만 재검증 → 비교 갱신" feature with persisted state across
   multiple HTTP requests for the same comparison session.
7. **Minimal implementation if adopted.** A single graph with nodes
   `extract → ask → await_answer → reverify_field → recompute_comparison`,
   state keyed by a comparison session id, reusing today's
   `analyze_posting()`/`evaluate_confirmed()` as node bodies rather than
   rewriting them.
8. **One sentence for judges.** "We don't have a multi-turn loop yet, so a
   state-graph library would only add a dependency with nothing to
   coordinate — we'll reach for it the day a real follow-up-question loop
   exists, not before."

---

## 2. LangChain

1. **Problem this would solve.** Provider abstraction, document loading,
   or output parsing that today's code writes by hand.
2. **Solvable with current structure?** Yes, and already solved:
   `backend/app/providers/base.py` defines a two-line `ExtractionProvider`
   protocol; `mock_provider.py`, `anthropic_provider.py`, and
   `nvidia_provider.py` each implement it directly against their native
   SDK/HTTP call. Output parsing is a forced tool-call
   (`anthropic_provider.py`'s `_EXTRACTION_JSON_SCHEMA` +
   `RawExtraction.model_validate`), which is more precise than a
   general-purpose output parser because it's the exact Pydantic contract
   this product already enforces everywhere else.
3. **Real benefit if added anyway.** None identified. This product does
   not load documents (postings are plain strings, either pasted or
   resolved server-side from JSON), and its output parsing requirement
   (offset-verified, schema-locked JSON) is narrower and stricter than
   what a general parser abstraction buys.
4. **Complexity/failure risk.** A dependency whose version churn and
   abstraction surface would sit between this code and the exact provider
   behavior it needs to control precisely (forced tool choice, no
   retries beyond the deterministic `MAX_ATTEMPTS = 2` in
   `backend/app/services/audit_pipeline.py:23`, defensive key-scrubbing in
   `_scrub_secret` — `anthropic_provider.py:68`). Wrapping these in a
   generic chain abstraction would make the exact behavior *harder* to
   verify, not easier.
5. **Verdict: `NOT_JUSTIFIED`.**
6. **Adoption condition.** Only if a genuinely reusable piece (e.g. a
   document loader for a new, real input format) has clearly less code and
   equal control by using LangChain's version versus a 10-20 line native
   implementation — has not occurred in this codebase yet.
7. **Minimal implementation if adopted.** Adopt only the single loader/parser
   class needed, imported directly (`from langchain.document_loaders import
   X`), never the framework's agent/chain orchestration layer.
8. **One sentence for judges.** "Every provider call we make needs exact
   control over retries, tool-forcing, and secret handling — a generic
   wrapper would cost us that control for no code we're not already
   writing in twenty lines."

---

## 3. RAG

1. **Problem this would solve.** Finding relevant Jeonbuk postings for a
   given capital-area posting at a scale where exact-field filtering stops
   working.
2. **Solvable with current structure?** Yes, at the current scale. The
   real batch is 20 postings total (10:10,
   `data/intake/real_postings.jsonl`), with an exact, pre-computed 1:1
   pairing already on disk (`data/intake/real_matched_pairs.jsonl`, 10
   pairs). `backend/app/services/real_postings.py::find_home_region_matches`
   does an O(pairs) dict lookup — a vector index over 20 documents would
   be slower to build, harder to explain to a judge, and would replace an
   *exact* pairing with an *approximate* one for no accuracy gain.
3. **Real benefit if added anyway.** None at n=20. Direct filtering
   (occupation, employment_type, region pack) is exhaustive and exact.
4. **Complexity/failure risk.** A vector DB dependency, an embedding
   pipeline, and a new failure mode (semantic near-misses) where today
   there is a verifiable, deterministic match.
5. **Verdict: `NOT_JUSTIFIED`** at the current data size; **`NEXT_STAGE`**
   is the honest label for the scenario the task explicitly asks about
   (postings growing into the thousands with multiple region packs).
6. **Adoption condition.** Occupation and region-pack filtering no longer
   narrows the candidate pool enough for exact/rule-based matching to stay
   both fast and precise — concretely, once a single (occupation,
   employment_type, region pack) filter regularly returns more candidates
   than a human should scan, or once postings must be matched on
   free-text similarity (e.g. duties described very differently for the
   same real job) rather than structured fields.
7. **Minimal implementation if adopted.** Scope the search to the user's
   region pack *first* (filter, not rank), then run semantic search only
   within that already-small pool — never a global vector search across
   every region pack. Evaluate before shipping with:
   - Recall@K and Precision@K against the existing exact-match pairs as a
     ground truth set (do the pairs `data/intake/real_matched_pairs.jsonl`
     already encode still rank in the top K?)
   - 직무 일치율 (occupation match rate) and 지역 일치율 (region match rate)
     on retrieved candidates
   - 잘못된 직군 매칭 비율 (wrong-occupation-family match rate) — must be
     ~0%, since this is a stricter tripwire than plain accuracy
8. **One sentence for judges.** "With 20 real postings and an exact
   matched-pair file already computed, a vector index would add
   infrastructure to approximate something we can already compute exactly
   — we'd revisit this if the catalog grows into the thousands."

---

## 4. MCP

1. **Problem this would solve.** Standardizing calls to external data
   sources this product doesn't yet integrate: public job postings,
   Jeonbuk youth policy info, regional housing-cost baselines, official
   company career pages.
2. **Solvable with current structure?** Yes, for everything integrated
   today. The product reads only local files (`data/**`) and its own
   FastAPI backend — there is no external tool call anywhere in the
   current codebase to standardize.
3. **Real benefit if added anyway.** None yet, since there is nothing on
   the other end of an MCP connection for this product to call. The
   benefit is real but *entirely future*: once `get_regional_housing_baseline`,
   `get_regional_youth_policies`, etc. become real external calls, giving
   them one standard tool-calling interface (rather than N bespoke client
   modules) is a legitimate reason to reach for MCP.
4. **Complexity/failure risk.** Standing up even one MCP server today
   would mean building a fake/stub server purely to demonstrate the term
   "MCP" — explicitly disallowed by this task's own instructions
   ("단순히 MCP라는 용어를 보여주기 위해 가짜 서버를 만들지 마십시오").
5. **Verdict: `NOT_JUSTIFIED`** now; **`NEXT_STAGE`** once any one of the
   three external integrations below is actually being built.
6. **Adoption condition.** The moment a second external, region-scoped
   data source needs the same call shape (region_code + occupation in,
   structured data out) — at that point a shared tool interface earns its
   keep versus two bespoke HTTP clients.
7. **Minimal implementation if adopted.** Three narrow, typed tools, no
   more:
   ```text
   get_local_postings(region_code, occupation)
   get_regional_housing_baseline(region_code)
   get_regional_youth_policies(region_code)
   ```
   Each backed by a real public data source with its own redistribution
   terms checked the same way `REAL_DATA_ACQUISITION_HANDOFF.md` already
   requires for postings — not a speculative schema for a source that
   doesn't exist yet.
8. **One sentence for judges.** "We don't call any external API yet, so an
   MCP server today would just be theater — the day we add a second
   region's housing-cost or policy lookup, a shared tool interface for
   both becomes worth building."

---

## 5. Harness

1. **Problem this would solve.** Preventing an LLM (or a deterministic
   mock standing in for one) from producing an ungrounded, inconsistent,
   or silently-wrong result that reaches a user.
2. **Solvable with current structure?** **Already solved, and already
   built** — this is the one entry in this document where the answer is
   "we did this, we just hadn't named it." Concretely, in this repository:
   - **Schema validation**: every request/response model is a `StrictModel`
     (`backend/app/models/common.py`) with `extra="forbid"`; the raw
     provider output additionally validates against `RawExtraction`
     (`backend/app/providers/raw.py`) before any rule runs.
   - **Evidence offset/substring verification**: `validate_evidence_span()`
     (`backend/app/services/evidence.py`) rejects any evidence whose
     `source_text[start:end]` doesn't match the claimed text exactly —
     catches both fabricated and mis-offset evidence.
   - **Deterministic downgrade rules**: `evaluate_confirmed()`
     (`backend/app/rules/field_rules.py:71`) can only downgrade
     confirmed→vague→absent, never upgrade, never invent — enforced in
     `audit_pipeline.py`.
   - **Retry limit**: exactly one retry on schema/evidence failure
     (`MAX_ATTEMPTS = 2`, `audit_pipeline.py:23`); a provider connectivity
     failure is never retried and never downgraded into a posting status.
   - **Provider fail-closed**: an unrecognized `LLM_PROVIDER` value raises
     a typed error instead of silently falling back to mock
     (`backend/app/providers/factory.py`, hardened on
     `feature/p0-release-hardening`); defensive key-scrubbing
     (`_scrub_secret`, `anthropic_provider.py:68`) strips the configured
     key from any exception text before it reaches an API response.
   - **Gold/AI-consensus evaluation discipline**: `docs/data/AI_CONSENSUS_REVIEW.md`
     explicitly separates AI-A/B agreement from human gold, discloses a
     selection-bias limitation, and never lets `GET /data/gap-stats` treat
     AI consensus as gold input.
   - **Tests and contract verification**: 242 automated tests as of this
     branch (`python -m pytest -q`), plus a contract-diff discipline
     (`contracts/schema.json`/`openapi.json` regenerated and diffed before
     every merge in this project's history) that catches accidental
     contract drift.
   - **Secret scrubbing**: covered above and independently verified via
     full-git-history secret scans in every prior handoff on this branch
     lineage (`REAL_DATA_ACQUISITION_HANDOFF.md`,
     `docs/review/P0_RELEASE_HARDENING.md`).
3. **Real benefit of a new framework.** None over what exists — a
   third-party "LLM eval harness" library would duplicate checks already
   enforced at the Pydantic/service layer, with less precise control over
   this product's specific grounding rules (offset-exact evidence,
   closed three-value status enum, no `external_verified`).
4. **Complexity/failure risk of adding one anyway.** Real: it would either
   duplicate the above checks (wasted surface) or partially replace them
   with a generic library's notion of "groundedness," which is looser than
   this product's exact-substring requirement.
5. **Verdict: `IMPLEMENT_NOW`** — meaning: formalize and document what
   already exists as this product's AI safety/evaluation harness (this
   section, plus the diagram below), not adopt a new framework.
6. **Adoption condition for a *replacement* framework.** Only if a future
   requirement needs guarantees this hand-built harness structurally
   cannot express (e.g. cross-model ensemble voting at scale, which the
   AI-A/B consensus process already does manually and honestly for one
   dataset pass).
7. **Minimal implementation.** Already done; this document plus the
   diagram below is the "minimal implementation" the task calls for
   (documentation and a structure diagram, not new code).
8. **One sentence for judges.** "Our harness — schema validation, exact
   evidence-offset checks, deterministic-only downgrades, fail-closed
   providers, and a disclosed AI-vs-human-gold separation — already exists
   in code and tests; we're naming it, not replacing it with a framework."

### Harness structure diagram

```text
Provider (mock | anthropic | nvidia)
        │  raw dict, never trusted
        ▼
RawExtraction.model_validate()         ── schema gate (extra=forbid, 6 fields exactly once)
        │
        ▼
validate_evidence_span() per field     ── source_text[start:end] == evidence_text, else reject
        │  (schema/evidence failure -> retry once, MAX_ATTEMPTS=2; provider failure -> never retried)
        ▼
evaluate_confirmed() per field         ── deterministic rubric rule; downgrade-only, never invent
        │
        ▼
AuditedField (status ∈ {confirmed, vague, absent}, reason_code required)
        │
        ▼
build_verification_action() for vague/absent
        │
        ▼
PostingAnalysis  ──────────────────────► API response (StrictModel, extra=forbid)
```

---

## 6. Ontology

1. **Problem this would solve.** Making the relationships between the six
   fields, their three-value status, evidence, and verification actions
   explicit and referenceable, rather than implicit in scattered code.
2. **Solvable with current structure?** Largely yes, already: `data/rubric/rubric.yaml`
   (field definitions, confirmed/vague/absent criteria, occupation mapping)
   and the Pydantic models in `backend/app/models/{common,posting}.py`
   jointly express almost exactly this structure today — they *are* a
   lightweight ontology, just not labeled or diagrammed as one.
3. **Real benefit of formalizing it.** Yes, this one is worth doing:
   naming the relationships explicitly makes onboarding a second occupation
   or a second region pack faster and less error-prone, and gives judges
   and future contributors one diagram instead of three files to
   cross-reference.
4. **Complexity/failure risk.** Low, *if* kept at documentation level. A
   real graph database (Neo4j, RDF triple store, etc.) would be pure
   overhead for six fields and three statuses — there is no query this
   product needs that Pydantic + YAML + a doc can't already answer.
5. **Verdict: `IMPLEMENT_NOW`** — as documentation only, expressed with the
   diagram below plus the region-pack extension in section 9. No graph DB.
6. **Adoption condition for a heavier ontology tool.** Only if the number
   of field types, relationships, or cross-occupation rules grows enough
   that a YAML file and a handful of Pydantic models can no longer express
   them without duplication — not reached in this project.
7. **Minimal implementation.** This document's diagram, kept in sync with
   `data/rubric/rubric.yaml` and `backend/app/models/common.py` by hand
   (both are small enough that this is not a burden).
8. **One sentence for judges.** "Our rubric YAML and Pydantic models
   already are a lightweight ontology — we wrote it down as one diagram
   instead of standing up a graph database for six fields."

### Domain ontology (documentation only)

```text
JobPosting
 ├─ hasField → Compensation (salary)
 ├─ hasField → Duties
 ├─ hasField → Skills (tools_or_skills)
 ├─ hasField → Training (training_or_mentoring)
 ├─ hasField → Probation (probation_terms)
 └─ hasField → EmploymentType

PostingField
 ├─ hasDisclosureStatus → confirmed | vague | absent   (closed enum, no external_verified)
 ├─ supportedBy → Evidence (exact substring + offsets, required iff confirmed|vague)
 └─ missingOrVagueCreates → VerificationAction (channel, prompt; required iff vague|absent)

Comparison
 ├─ compares → MetroPosting
 ├─ compares → LocalPosting (home-region posting)
 └─ contains → FieldComparison (per PostingField, no aggregate score)
```

---

## 7. Multi-agent

1. **Problem this would solve (claimed).** Splitting analysis, search,
   finance calculation, and verification into separate LLM agents that
   negotiate or hand off to each other.
2. **Solvable with current structure?** Yes, entirely, and already solved
   with plain deterministic code: matching is a dict/dataclass filter
   (`real_postings.py`), finance is pure arithmetic
   (`backend/app/services/finance.py`, explicitly "no LLM" per
   `CLAUDE.md`), and "verification" is a rubric rule table
   (`field_rules.py`), not an agent. None of these need judgment calls an
   LLM agent would make differently or better.
3. **Real benefit if added anyway.** None demonstrated or plausible for
   this product's actual tasks. There is no evidence (here or generally)
   that splitting deterministic arithmetic or dict lookups into "agents"
   improves their accuracy — they have no accuracy to improve; they are
   exact.
4. **Complexity/failure risk.** Significant: inter-agent communication
   failure modes, higher latency, harder-to-audit decisions, and — per
   `CLAUDE.md`'s explicit prohibition — a direct violation of this
   project's own architecture constraint ("Do not add a product-level
   multi-agent system").
5. **Verdict: `NOT_JUSTIFIED`.**
6. **Adoption condition.** None identified for this product's current
   scope. Would require a task that is genuinely open-ended and
   judgment-heavy in a way deterministic code cannot express — none of
   this MVP's five tasks (extract, match, finance, verify, compare) are.
7. **Minimal implementation if ever adopted.** N/A — not recommended even
   in minimal form; the deterministic harness in section 5 is the correct
   minimal design for this product's grounding requirements.
8. **One sentence for judges.** "Matching, finance, and rule-based
   verification are exact and deterministic today — turning them into
   negotiating LLM agents would add latency and failure modes to
   calculations that are already provably correct."

---

## 8. Summary table

| Technology | Verdict | One-line reason |
|---|---|---|
| LangGraph | `NOT_JUSTIFIED` (→ `NEXT_STAGE` if the follow-up-question loop is built) | No multi-turn state exists yet in this branch |
| LangChain | `NOT_JUSTIFIED` | Existing 20-line provider abstraction has more precise control |
| RAG | `NOT_JUSTIFIED` now / `NEXT_STAGE` at scale | 20 real postings with an exact pre-computed pairing; no ranking problem to solve |
| MCP | `NOT_JUSTIFIED` now / `NEXT_STAGE` per external integration | No external API calls exist to standardize yet |
| Harness | `IMPLEMENT_NOW` (already built; formalize only) | Schema/evidence/rule/fail-closed/secret-scrub/test discipline already in code |
| Ontology | `IMPLEMENT_NOW` (docs only, no graph DB) | Rubric YAML + Pydantic models already express it |
| Multi-agent | `NOT_JUSTIFIED` | Every current task is deterministic; `CLAUDE.md` prohibits this outright |

---

## 9. Region Pack Ontology (login-based self-region matching addendum)

Extends section 6 for the region-scoped comparison policy (see README's
product definition and `backend/app/datasets/loader.py::home_region()` /
`backend/app/services/real_postings.py`).

```text
UserProfile
 └─ hasHomeRegion → RegionPack

RegionPack
 ├─ contains → LocalPosting
 ├─ hasHousingBaseline → RegionalCostBaseline   (not populated in this MVP; finance inputs are user-entered)
 └─ allowsComparisonWith → CapitalArea

ComparisonRequest
 ├─ selectedPosting → CapitalAreaPosting
 ├─ scopedBy → UserProfile.homeRegion
 └─ returns → LocalPosting[]
```

**Implementation status:** a `Literal`/env-var pair
(`DEMO_HOME_REGION`, defaulting to `"jeonbuk"` — see
`backend/app/datasets/loader.py::home_region()`) already realizes this
without a graph database: the loader only ever returns rows matching the
configured home region, and `real_postings.py::find_home_region_matches`
double-checks the paired candidate's region against it again before
returning — a client can never request a different region because none of
the new request models (`HomeRegionMatchRequest`, `AnalyzeByIdRequest`)
have a region field at all. **Verdict for a heavier region-pack engine:
`NOT_JUSTIFIED`** while exactly one region pack exists; **`NEXT_STAGE`**
once a second region pack (e.g. Jeonnam) is actually onboarded with its
own dataset file, at which point `DEMO_HOME_REGION` becomes a per-deployment
or per-user-profile config value rather than a single fixed default —
still a `Literal`/config value, not a new data-modeling technology.

### MCP for region-scoped public data (scoped extension of section 4)

Same verdict as section 4 (`NOT_JUSTIFIED` now, `NEXT_STAGE` per real
integration), with the three tools it would eventually expose already
parameterized by `region_code` so a second region pack costs a config
value, not new code:

```text
get_local_postings(region_code, occupation)
get_regional_housing_baseline(region_code)
get_regional_youth_policies(region_code)
```

### RAG for region-scoped search (scoped extension of section 3)

If postings scale up, the region pack must be the *first* filter, applied
before any similarity search — never a global search that a region filter
narrows afterward, since that would let a capital-area or wrong-region
posting influence which results even get ranked:

```text
전체 공고
  → 사용자 지역권(region pack) 필터   ← always first, always server-enforced
  → 직무·고용조건 필터
  → 필요할 경우 의미 검색 (semantic search, only within the already-filtered pool)
  → 상위 후보 반환
```

At the current 20-posting, single-region-pack scale, none of this is
implemented or needed — the exact-match pairing already in
`data/intake/real_matched_pairs.jsonl` is both simpler and more precise.
