# Annotation schema and workflow (Phase 4)

## Files in this directory

| File | Who writes it | Purpose |
|---|---|---|
| `ai_suggestions.jsonl` | `scripts/data/ai_suggest_labels.py` (rule-based, no LLM) | Suggestions only. Kept visually/structurally separate. **Never a source of gold.** |
| `annotator_A_template.jsonl` | Human annotator A | Independent labels, filled in from the original posting text. |
| `annotator_B_template.jsonl` | Human annotator B | Independent labels, filled in from the original posting text, without seeing A's answers. |
| `adjudication_output.jsonl` | `scripts/data/adjudicate.py`, then a human adjudicator | A vs. B comparison + adjudicated final label. |

Annotators A and B must not see each other's answers, or the AI suggestions,
while labeling. AI suggestions exist so a team member can sanity-check the
rubric or pre-stage a template faster, not to be pasted into either
annotator's file.

## Per-cell record shape (annotator template)

```json
{
  "posting_id": "JB-001",
  "field": "salary",
  "annotator_id": "A",
  "status": "confirmed",
  "evidence_text": "월급 235만원(세전) 지급.",
  "offsets": [78, 96],
  "reason_code": "amount_and_unit_present",
  "disagreement_note": null,
  "rubric_version": "1.0.0-draft"
}
```

Rules:

- `status` must be exactly one of `confirmed`, `vague`, `absent`. Nothing
  else (no `external_verified`, no error codes).
- `offsets` is `[start, end]` such that
  `posting.full_text[start:end] == evidence_text` exactly (Python slice
  convention: `end` is exclusive).
- `evidence_text` / `offsets` are **required** (non-null) when `status` is
  `confirmed` or `vague`, and **must be null** when `status` is `absent`.
- `reason_code` is a short free-text label naming which rubric criterion
  applied (e.g. `amount_and_unit_present`, `deferred_to_interview`,
  `duration_only_no_pay_detail`, `no_relevant_text`). It is required for
  every filled-in row — see `data/rubric/rubric.yaml` criteria text for
  the vocabulary each field's criteria imply. It is not a fixed enum; pick
  the phrase from the rubric criteria that best matches your decision so a
  reviewer can trace it back.
- `disagreement_note` is optional and is the annotator's own note (e.g. "I
  was unsure whether this counts as a named tool"), not the adjudicator's.
- `rubric_version` must match the version the annotator was actually working
  from (`data/rubric/rubric.yaml: rubric_version`).

## Validation

Run `python scripts/data/validate_dataset.py --annotations <file.jsonl>`
before treating any annotator file as complete. It checks:

- exactly six fields present per posting, no duplicates;
- only the three allowed statuses appear;
- evidence is present for confirmed/vague and null for absent;
- `full_text[start:end] == evidence_text` for every offset pair;
- no duplicate `(posting_id, field)` cells;
- matched-pair integrity against `data/postings/matched_pairs.jsonl`.

## Adjudication

Once both `annotator_A_template.jsonl` and `annotator_B_template.jsonl` are
fully filled in (no null `status` remaining) and both pass validation, run:

```
python scripts/data/adjudicate.py \
  --annotator-a data/annotation/annotator_A_template.jsonl \
  --annotator-b data/annotation/annotator_B_template.jsonl \
  --out data/annotation/adjudication_output.jsonl
```

This produces one row per cell with both raw labels, an `agreement` flag,
and empty `adjudicated_status` / `adjudicated_evidence_text` /
`adjudicated_offsets` / `adjudicator_note` fields for a human adjudicator to
fill in — required on every disagreement, optional (a straight copy is fine)
on agreements. The script also prints percent agreement and, when the label
distribution makes it meaningful, Cohen's kappa. See
`docs/data/METHODOLOGY.md` for how to read those numbers and
`DATA_HANDOFF.md` for the current status of real annotation.

**A dataset only becomes "gold" after this adjudication step is complete for
every cell.** Nothing in this repository currently qualifies — see
`DATA_HANDOFF.md`.
