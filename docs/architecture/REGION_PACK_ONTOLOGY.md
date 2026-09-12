# Region Pack Ontology

Standalone reference for the domain/region-pack ontology (see
`docs/architecture/EXPANSION_TECH_ASSESSMENT.md` sections 6 and 9 for the
full adoption-decision writeup this summarizes). Unchanged by
`feature/work24-ai-extension-layer` -- no backend or data-model file was
touched on this branch; this document only makes the existing structure
easier to find.

## Domain ontology (documentation only, no graph DB)

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

Backed by `data/rubric/rubric.yaml` (field definitions, confirmed/vague/absent
criteria, occupation mapping) and `backend/app/models/{common,posting}.py`.

## Region pack extension (login-based self-region matching)

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

**Implementation status:** a `Literal`/env-var pair (`DEMO_HOME_REGION`,
defaulting to `"jeonbuk"` — `backend/app/datasets/loader.py::home_region()`)
already realizes this without a graph database: the loader only ever
returns rows matching the configured home region, and
`real_postings.py::find_home_region_matches` double-checks every candidate's
region again before returning (up to three: the pre-linked pair first, then
other same-group postings in deterministic collection order -- never a
similarity ranking). No request model
(`HomeRegionMatchRequest`, `AnalyzeByIdRequest`) has a region field, so a
client can never request a different region than the server's configured
one — this is server-enforced, not a UI convention.

**Verdict for a heavier region-pack engine:** `NOT_JUSTIFIED_NOW` while
exactly one region pack exists; revisit once a second region pack (e.g.
Jeonnam) is actually onboarded with its own dataset file.

## UI-only presentation layer addendum (feature/work24-ai-extension-layer)

The comparison-axes presentation layer (`src/lib/comparisonAxes.ts`) adds
one purely frontend concept that is *not* part of this ontology's backend
types: `AxisDisplayStatus = FieldStatus | 'not_evaluated'`. This exists only
because two comparison sub-items (근로시간·교대제·통근, 복지·기숙사·통근지원)
have no `PostingField` behind them at all in the current extraction
pipeline — `not_evaluated` says "this MVP's analysis doesn't check this,"
which is a different claim from `absent` ("the posting didn't state this").
It is never written to or read from the backend, never appears in
`FieldStatus`, and is structurally excluded from any absent-count or
priority-unresolved logic (`src/lib/priorityUnresolved.ts`).
