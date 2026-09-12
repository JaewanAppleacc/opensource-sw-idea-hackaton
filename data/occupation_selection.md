# Occupation selection note (Phase 1)

Status: **PROVISIONAL**. This note documents the occupation the pipeline is
*designed around*, not a confirmed 10:10 real-data result. See
`data/sources/source_inventory.yaml` for why no real postings exist yet.

## Chosen occupation

- Occupation: **생산직 (제조 조립원)** — production/assembly-line worker
- Employment type for matched pairs: **정규직** (regular/full-time)

## Why this occupation, once real sourcing is possible

- Jeonbuk (전주·군산·익산·완주 일대) has an active manufacturing base
  (automotive parts, machinery, food processing), so production/assembly
  roles are one of the more plausible occupations to reach 10+ postings from
  a single source and period without needing a specialized/rare skill match.
- Production/assembly postings tend to describe duties, required
  tools/certifications (지게차, PLC 등), and shift/probation terms in fairly
  concrete, checklist-like language, which makes the six-field audit rubric
  easier for two independent human annotators to apply consistently — a
  precondition this project requires before selecting an occupation.
- Employment type (정규직 vs 계약직) is usually stated explicitly for this
  occupation, reducing ambiguity in the `employment_type` field.

## Feasibility checks required before this becomes a real, non-provisional choice

Per `TASK_DATA_EVALUATION.md` Phase 1, an occupation may only be finalized
after verifying, against an actual source:

1. At least 10 Jeonbuk postings are obtainable from the same source and
   collection period. **Not yet verified — no source access.**
2. Metropolitan matches are obtainable for the same occupation and employment
   type from the same source/period. **Not yet verified.**
3. The team can reasonably adjudicate all six fields for this occupation
   (i.e., the concepts map onto real posting language). **Partially checked**
   via the synthetic fixtures and rubric authored in this pass — see
   `data/rubric/rubric.md`, section "Occupation-specific field mapping" —
   but this is a design check, not a check against real postings.

## What would trigger re-selecting the occupation

- If, once a data.go.kr key is issued, the 고용24/워크넷 API returns fewer
  than 10 Jeonbuk postings for 생산직 in a reasonable recent window, fall
  back to a broader occupation code (e.g. general 제조/생산 group codes) or a
  different candidate occupation (e.g. 요양보호사, 콜센터 상담원) — do not
  lower the 10-posting minimum instead.
- If duties/tools language for this occupation turns out to be too
  boilerplate to distinguish `confirmed` from `vague` in practice during a
  trial annotation pass on real postings, record that finding and reconsider.

## Non-goal

This note is not a labor-market claim about Jeonbuk manufacturing employment.
It only explains a data-pipeline design choice.
