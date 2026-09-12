# Collection & evaluation methodology (public repository layer)

This document is the publishable summary of how the Jeonbuk
career-due-diligence dataset is meant to be built and evaluated. It is
written so it stays accurate even before real data exists — every section
says explicitly what is done vs. designed-but-pending.

## 1. Source and occupation feasibility (Phase 1)

We researched public/open sources for Korean job postings rather than
scraping private recruitment platforms. The most plausible candidate is the
고용24/워크넷 채용정보 Open API published on `data.go.kr` by 한국고용정보원
(Korea Employment Information Service). As of this writing, using it
requires a `data.go.kr` account and a per-API usage application that issues
a service key — a manual, human step this project has not yet completed.
Full details, including every source considered and why it was accepted,
excluded, or blocked, are in `data/sources/source_inventory.yaml`.

We provisionally selected **생산직(제조 조립원)** (production/assembly-line
worker), 정규직 (regular/full-time), as the target occupation, reasoning in
`data/occupation_selection.md`. This choice is not yet confirmed against a
real source and may change once real querying is possible.

## 2. Rubric (Phase 2)

Six fields — `salary`, `duties`, `tools_or_skills`,
`training_or_mentoring`, `probation_terms`, `employment_type` — are each
labeled `confirmed`, `vague`, or `absent` against the controlling principle:
*distinguish wording being present from decision-useful information being
present*. The full rubric, with per-field criteria, examples, and
deterministic checks, is versioned at `data/rubric/rubric.yaml` /
`data/rubric/rubric.md` (current version `1.0.0-draft`).

## 3. Corpus construction (Phase 3)

Because no real postings have been obtained yet (see §1), the corpus in
`data/postings/` is a **self-authored synthetic fixture set**: 10 fictional
Jeonbuk postings, 10 fictional metropolitan postings forming 10 matched
pairs, and 2 additional postings deliberately left unmatched to exercise
that code path. This is the fallback explicitly allowed by
`TASK_DATA_EVALUATION.md` Phase 3 ("generate separate synthetic fixtures for
repository tests and demos") — it is not a substitute for real sourcing, and
no finding in this repository treats it as real-world evidence. See
`data/postings/README.md`.

## 4. Human annotation (Phase 4)

Two independent annotators are meant to label every posting-field cell with
a status, exact evidence text and offsets (for confirmed/vague), and a
reason code, without seeing each other's answers or the AI suggestions.
Templates are in `data/annotation/annotator_A_template.jsonl` and
`_B_template.jsonl`; the process is documented in
`data/annotation/schema.md`. **As of this writing these templates are
blank** — no real annotation has happened. A rule-based (non-LLM) AI
suggestion generator (`scripts/data/ai_suggest_labels.py`) produces
suggestions in a separate file to speed up eventual human labeling; those
suggestions are never copied into gold automatically.

## 5. Adjudication (Phase 4)

`scripts/data/adjudicate.py` compares two completed annotator files cell by
cell, reports percent agreement and (when the label distribution makes it
meaningful) Cohen's kappa, and produces a working file for a human
adjudicator to resolve disagreements. A dataset is gold only once this step
is complete for every cell with a genuine human decision recorded.

## 6. Split (Phase 5)

`scripts/data/generate_splits.py` groups postings into matched-pair units
(kept together) and singleton units (the unmatched records), sorts them so
units carrying rarer statuses (currently: `absent`) are spread across
splits, and selects a holdout whose size is closest to 20% of postings while
guaranteeing both regions appear in it. It writes a manifest with posting
IDs, rubric version, an explicit `is_gold` flag, and SHA-256 checksums of
each split's ID list. The holdout is read-only by convention: once frozen,
it must not be inspected or used for prompt/rubric tuning.

## 7. Statistics and evaluation (Phase 6)

- `scripts/data/aggregate_stats.py` computes posting/cell counts, status
  proportions by region and field, matched-pair descriptive differences, and
  unmatched counts — from adjudicated labels only, and always tags its
  output with `is_gold` plus the mandatory
  `exploratory sample; not population-generalizable` disclaimer.
- `scripts/data/evaluate_predictions.py` compares a backend prediction JSONL
  against gold, reporting schema failures and unsupported/fabricated
  evidence as first-class counts (not silently dropped), a 3×3 confusion
  matrix, raw correct/incorrect counts as the **primary** result, and macro
  precision/recall/F1 only as a clearly-caveated secondary figure — per
  project rules against overstating small-sample per-field F1.
- `scripts/data/generate_report.py` renders `aggregate_stats.py`'s JSON into
  a Markdown report, automatically prefixing a "NOT GOLD" banner whenever
  the input's `is_gold` flag is false.

## Known limitations (update as real work lands)

- No real postings exist yet; every number produced by this pipeline today
  is a demonstration of the code, not a research finding.
- The occupation choice is provisional and unverified against a real
  source.
- The rubric has not yet been pilot-tested by two humans against real
  postings; deterministic checks (e.g. the probation duration+condition
  conjunction) are only validated against the synthetic fixtures so far.
- All regional comparisons in this repository, once real data exists, will
  remain exploratory-sample findings about the specific matched postings
  collected, not claims about all Jeonbuk or metropolitan postings.
