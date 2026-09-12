# DATA_HANDOFF.md — Data & evaluation track (Parallel task B)

Read alongside `CLAUDE.md` and `TASK_DATA_EVALUATION.md`. This document is
the single source of truth for what the data/evaluation track has produced,
what every path means, and — most importantly — **what real human work is
still required before anything here can be called gold or cited as a
finding.**

## TL;DR for the integration track / whoever reads this next

- The rubric, schema, annotation workflow, validation, split, statistics,
  and evaluation **code** is complete, tested, and runs end to end.
- **No real Jeonbuk or metropolitan postings have been collected, and no
  human has annotated anything.** Every posting, label, split, and report in
  this repository today is either self-authored synthetic fixture data or a
  rule-based (non-LLM) suggestion, clearly tagged as such.
- Nothing here is labeled `gold`. Per `TASK_DATA_EVALUATION.md`'s completion
  check: *"If two independent humans have not completed annotation, do not
  label the result gold, do not create a misleading performance claim, and
  list the exact remaining manual steps."* That list is in
  [Remaining manual steps](#remaining-manual-steps) below.

## What exists and where

| Deliverable (per TASK_DATA_EVALUATION.md) | Path | Status |
|---|---|---|
| Source feasibility inventory | `data/sources/source_inventory.yaml` | Done — real research, documents the blocker |
| Occupation-selection note | `data/occupation_selection.md` | Done, marked provisional |
| Versioned rubric (YAML + Markdown) | `data/rubric/rubric.yaml`, `data/rubric/rubric.md` | Done, `rubric_version: 1.0.0-draft` |
| Curated posting metadata + matched-pair table | `data/postings/postings.jsonl`, `data/postings/matched_pairs.jsonl` | Done, **synthetic only** (see `data/postings/README.md`) |
| Independent annotation templates | `data/annotation/annotator_A_template.jsonl`, `_B_template.jsonl` | Done, **blank**, ready for real humans |
| AI suggestions (separate column) | `data/annotation/ai_suggestions.jsonl` | Done, rule-based, `ai_suggested: true` |
| Adjudication workflow | `scripts/data/adjudicate.py`, `data/annotation/schema.md` | Done, tested; not yet run on real annotations |
| Validated gold dataset | — | **Not produced.** Requires real annotation first. |
| Development/holdout manifests | `data/splits/manifest_demo.json` (+ `dev_split_demo.json`, `holdout_split_demo.json`) | Demo only, `"is_gold": false` |
| Dataset validation script + tests | `scripts/data/validate_dataset.py`, `tests/data/test_validate_dataset.py` | Done |
| Aggregate-statistics script + tests | `scripts/data/aggregate_stats.py`, `tests/data/test_aggregate_stats.py` | Done |
| Evaluation script (backend prediction JSONL) | `scripts/data/evaluate_predictions.py`, `tests/data/test_evaluate_predictions.py` | Done |
| Generated exploratory report | `data/reports/demo_exploratory_report.md` | Demo only, "NOT GOLD" banner |
| This document | `DATA_HANDOFF.md` | Done |

Supporting pieces not explicitly named above but needed to make the rest
runnable: `scripts/data/utils.py` (shared I/O/checksum helpers),
`scripts/data/build_synthetic_fixtures.py` (how the fixtures were built),
`scripts/data/ai_suggest_labels.py` (rule-based suggestion generator),
`scripts/data/generate_annotation_templates.py`,
`scripts/data/build_demo_synthetic_annotations.py` (builds the NOT-GOLD demo
set), `scripts/data/generate_report.py`, `scripts/data/run_pipeline_demo.sh`
(runs the whole thing in order), `docs/data/METHODOLOGY.md` (publishable
methodology writeup), and `data/README.md` /
`data/demo_synthetic_annotations/README.md` (internal map + NOT-GOLD
warning).

## Why there is no real data yet

Per Phase 1, real Jeonbuk/metropolitan postings must come from a public/open
source or from postings a user explicitly supplies — scraping private
recruitment platforms (사람인, 잡코리아, etc.) is disallowed by project rules
regardless of technical feasibility. The one plausible public source
identified, **고용24/워크넷 채용정보 Open API** on `data.go.kr`, requires a
human to create a `data.go.kr` account and submit a per-API usage
application to receive a service key. That is an interactive, human-gated
step this agent session cannot complete on its own, and no user-supplied
postings were provided during this work session either. Full detail and
every other source considered is in `data/sources/source_inventory.yaml`.

Rather than invent postings and present them as real (explicitly
prohibited), or leave the rest of the pipeline unbuilt, this pass:

1. documented the blocker honestly;
2. built a complete, reproducible, self-authored **synthetic** fixture
   corpus (`scripts/data/build_synthetic_fixtures.py`) explicitly sanctioned
   by Phase 3 ("generate separate synthetic fixtures for repository tests
   and demos") to exercise every later phase; and
3. built and tested the rubric, annotation, validation, split, statistics,
   and evaluation code against that synthetic corpus, so the only remaining
   work to reach a real result is the data-collection and annotation labor
   itself, not more engineering.

## Remaining manual steps

These are the concrete, human-gated steps still needed, in order:

1. **Get a `data.go.kr` account and Open API key** for 한국고용정보원_워크넷
   채용정보 (or identify and vet an alternative public/compliant source).
   This is a human signup + usage-purpose application; see
   `data/sources/source_inventory.yaml` for the exact API pages.
2. **Query real postings** for the candidate occupation (or a replacement
   chosen via the same feasibility criteria in
   `data/occupation_selection.md`) and confirm at least 10 Jeonbuk + 10
   metropolitan postings, same source/period/occupation/employment type, are
   actually obtainable. Re-run the Phase 1 feasibility checklist against the
   real result before finalizing the occupation.
3. **Re-confirm redistribution rights** for the chosen source at the moment
   the key/terms are visible, before putting any real full text in the
   public repository layer (`data/README.md` explains the internal-vs-public
   split).
4. **Replace the synthetic corpus** with real curated records following the
   exact schema in `data/postings/README.md` (reuse the JSONL shape; the
   synthetic-fixture-specific fields like `fixture_build_date` can be
   dropped or repurposed for a real `collection_date`).
5. **Run two independent human annotators** through
   `data/annotation/annotator_A_template.jsonl` / `_B_template.jsonl`
   (regenerated against the real corpus via
   `scripts/data/generate_annotation_templates.py`), without either seeing
   the other's answers or `ai_suggestions.jsonl`.
6. **Validate both annotator files**
   (`python scripts/data/validate_dataset.py --annotations ...`) before
   treating them as complete.
7. **Run `scripts/data/adjudicate.py`** on the two real annotator files,
   then have a human adjudicator fill in every `adjudicated_status` (a
   straight copy is fine on agreement; a real decision with
   `adjudicator_note` is required on every disagreement). Report percent
   agreement and, if the label distribution supports it, Cohen's kappa —
   as raw counts, not overstated per-field F1, given the small sample.
8. **Only then** run `scripts/data/generate_splits.py` with
   `--is-gold true` on the real adjudicated file, freeze the holdout, and
   treat it as read-only.
9. **Only then** run `scripts/data/aggregate_stats.py` with `--is-gold` set
   appropriately and `scripts/data/generate_report.py` to produce a
   reportable (not "NOT GOLD"-banner) exploratory report.
10. Hand the real dev split + rubric to the integration track (Task C) to
    run extraction and produce predictions; evaluate those with
    `scripts/data/evaluate_predictions.py --is-gold-source true` against the
    real holdout **once**, per the no-silent-retuning rule in
    `TASK_INTEGRATION_AFTER_PARALLEL.md`.

Until step 7 is complete, nothing produced by steps 8-10 may be called gold
or cited as a performance/regional finding.

## How to verify what's here (completion check)

```
bash scripts/data/run_pipeline_demo.sh
```

This runs, in order, against the synthetic fixtures: the dataset validator,
the annotation/adjudication integrity check, split + checksum generation,
aggregate report generation, evaluation on the synthetic prediction fixture
(`tests/data/fixtures/sample_predictions.jsonl`), and the full pytest suite
(42 tests, `tests/data/`). All six steps pass as of this writing. Individual
commands are documented inline in each script's module docstring and in
`docs/data/METHODOLOGY.md`.

Every artifact this produces under `data/demo_synthetic_annotations/` and
`data/reports/demo_*` is explicitly non-gold — see
`data/demo_synthetic_annotations/README.md`.

## Schemas quick reference

- Posting record: `data/postings/README.md`
- Annotation cell record: `data/annotation/schema.md`
- Adjudication row: see `scripts/data/adjudicate.py` module docstring /
  `build_adjudication_rows`
- Split manifest: written by `scripts/data/generate_splits.py`, includes
  `rubric_version`, `is_gold`, posting-ID lists, SHA-256 checksums per
  split, and a read-only-convention note
- Aggregate stats / evaluation report JSON: see the respective scripts'
  module docstrings in `scripts/data/aggregate_stats.py` and
  `scripts/data/evaluate_predictions.py`

## Known limitations

- Occupation choice (생산직(제조 조립원), 정규직) is provisional and
  unverified against any real source — see
  `data/occupation_selection.md`.
- The rubric (`v1.0.0-draft`) has been exercised only against synthetic
  text; it has not been pilot-annotated by two humans on real postings, so
  its criteria may need revision (bump `rubric_version` when they do).
- The rule-based AI suggestion generator
  (`scripts/data/ai_suggest_labels.py`) is a fixed keyword/regex heuristic
  tuned to the synthetic fixtures' vocabulary. It is not expected to
  generalize to real posting phrasing without revision, and it must never
  be treated as a model baseline — it exists only to speed up eventual human
  template prefill, and its suggestions are visually/structurally separate
  from any annotator's actual answer.
- The "20% holdout" split algorithm in `scripts/data/generate_splits.py`
  picks the whole-unit prefix closest to exactly 20%; with a small posting
  count this can land a few points away from 20% (e.g. 18.2% in the current
  demo run with 22 postings). This is expected and documented in the
  script, not a bug.
- All statistics, once computed on real gold data, will remain **exploratory
  sample findings** about the specific matched postings collected — never a
  population-wide or causal claim about Jeonbuk vs. metropolitan employment.
