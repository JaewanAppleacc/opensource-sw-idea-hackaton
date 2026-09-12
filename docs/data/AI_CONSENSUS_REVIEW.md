# AI-A/B consensus review with human adjudication (real 20-posting batch)

Read alongside `docs/data/HUMAN_ANNOTATION_RUNBOOK.md`,
`REAL_DATA_ACQUISITION_HANDOFF.md`, and `DATA_HANDOFF.md`. **This document
does not report a human-gold dataset or a model accuracy number.**

## What this is

실제 채용공고 20건의 120개 필드에 대해 두 독립 AI 검수를 수행했다. 최초
113개 셀이 일치해 AI 간 일치율은 94.2%였다. 불일치한 7개 duties/
tools_or_skills 경계 사례는 팀 리드가 원문과 rubric을 검토하여 confirmed로
조정했다. 최종 120개 셀이 해결됐으나, 이 데이터는 두 명의 독립적인 사람이
구축한 Human Gold가 아니라 사람 조정이 포함된 AI consensus reference set이다.

## What this is not

- **Not** a two-human-annotator gold dataset (`DATA_HANDOFF.md`'s
  "Remaining manual steps" still require that separately — real
  `annotator_A`/`annotator_B` packets exist and are untouched by this
  review, see `data/private/annotation_packets/`).
- **Not** a model accuracy or performance number. 94.2% is an
  agreement/consistency rate between two independent AI review passes on
  their `suggested_status`, not a comparison against any ground truth.
- **Not** an input to `GET /data/gap-stats`, which reads only
  `GOLD_LABELS_PATH` (adjudicated *human* gold) and remains `ready: false`
  until that exists.
- **Not** a change to `human_boundary_review_completed` (still `null` in
  `data/intake/occupation_feasibility.json`) or `is_gold` (still `false`
  everywhere this pipeline writes it).

## Process

1. Two independent AI review passes (`reviewer_id: AI-A` / `AI-B`,
   `reviewer_type: "ai"`) each produced a `suggested_status` for all 120
   cells (20 postings × 6 fields) of the real batch, privately, in
   `data/private/ai_reviews/agent_A_suggestions.jsonl` and
   `agent_B_suggestions.jsonl` (gitignored — never committed).
2. `scripts/annotation_ops/build_ai_consensus.py` compared the two passes
   cell-by-cell on `suggested_status` only (not on the exact evidence text
   — see "Known limitation" below).
3. 113/120 cells agreed on `suggested_status` → recorded as
   `resolution_source: "ai_consensus"`.
4. 7/120 cells disagreed → a human team lead reviewed each against the
   real posting text and `data/rubric/rubric.yaml`, and recorded a real
   `adjudicator_note` naming the rubric criterion applied (never a bare
   "AI-B에 동의함") → recorded as `resolution_source: "human_adjudicated"`.
5. Output: `data/private/ai_reviews/ai_consensus_adjudicated.jsonl`
   (gitignored — real evidence text and offsets stay there only; this
   tracked document reports aggregates only).

## Result

| | Count |
|---|---|
| Total cells | 120 |
| Initial AI-A/B agreement | 113 (94.2%) |
| Human-adjudicated disagreements | 7 |
| Final `confirmed` | 60 |
| Final `vague` | 17 |
| Final `absent` | 43 |

The 7 human-adjudicated cells, all resolved to `confirmed`:

| Posting | Field |
|---|---|
| JB-01 | tools_or_skills |
| JB-02 | tools_or_skills |
| JB-07 | duties |
| JB-10 | duties |
| MET-02 | tools_or_skills |
| MET-03 | tools_or_skills |
| MET-06 | duties |

Each carries a rubric-grounded reason in the private file (e.g. "evidence
length meets the duties confirmed deterministic check and names a specific
product category" or "names a specific named processing technique under
tools_or_skills' occupation_mapping") — not reproduced here since it quotes
real posting text.

## Known limitations

- **Selection bias — do not use this subset to claim model performance.**
  The 7 disagreements are, almost by construction, the *hardest* boundary
  cases in the batch (exactly the ones where two independent reviews
  diverged). Any accuracy-style statistic computed only over the 113
  cells that already agreed would be measuring the easy cases and
  excluding the hard ones — it would overstate how well any extraction
  approach performs on this occupation's real posting language. This
  dataset must never be cited as "model accuracy," on the 113 subset or
  the full 120.
- **Agreement was measured on `status` only, not on evidence text.** A
  spot check found at least one cell (not among the 7 disagreements
  above) where `suggested_status` matched between A and B but the quoted
  `evidence_text` differed substantially — meaning "94.2% agreement"
  somewhat overstates true independent consensus. This is disclosed here
  rather than silently corrected, since redefining "agreement" after the
  fact would itself be a form of cherry-picking.
- **Not annotator-independent in the human-gold sense.** Sections 1-4 of
  `TASK_DATA_EVALUATION.md`'s two-human-annotator requirement are
  unaffected by and unmet by this review — it is a separate, faster,
  AI-assisted sanity pass, not a substitute.
- **Occupation-specific.** Every judgment call here (e.g. what counts as a
  "named skill" under `tools_or_skills`, or how much product-specificity
  satisfies `duties`) is scoped to 생산직(제조 조립원) postings and the
  rubric version recorded in each row (`1.0.0-draft`); it does not
  generalize to other occupations.

## Where the real content lives (never committed)

| File | Contents |
|---|---|
| `data/private/ai_reviews/agent_A_suggestions.jsonl` | AI-A's 120 per-cell suggestions with evidence and reasoning |
| `data/private/ai_reviews/agent_B_suggestions.jsonl` | AI-B's 120 per-cell suggestions with evidence and reasoning |
| `data/private/ai_reviews/ai_consensus_adjudicated.jsonl` | Merged result: both agents' status/evidence, agreement flag, final status, resolution source, adjudicator notes for the 7 human-adjudicated cells |

Regenerate the merged file (deterministic given the same two input files)
with:

```bash
python scripts/annotation_ops/build_ai_consensus.py \
  --agent-a data/private/ai_reviews/agent_A_suggestions.jsonl \
  --agent-b data/private/ai_reviews/agent_B_suggestions.jsonl \
  --out data/private/ai_reviews/ai_consensus_adjudicated.jsonl
```
