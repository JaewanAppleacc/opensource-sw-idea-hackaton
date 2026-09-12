"""Generate blank per-cell annotation templates for two independent human
annotators (Phase 4).

Each row is one (posting_id, field) cell. `status`, `evidence_text`,
`offsets`, and `reason_code` start as null -- a human annotator fills them
in directly, working from the original posting text (not from
ai_suggestions.jsonl, which is a separate, visually distinct file per
project rules: AI suggestions must never be copied into gold automatically).

Run: python scripts/data/generate_annotation_templates.py
Writes: data/annotation/annotator_A_template.jsonl
        data/annotation/annotator_B_template.jsonl
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTINGS_PATH = REPO_ROOT / "data" / "postings" / "postings.jsonl"
RUBRIC_VERSION = "1.0.0-draft"

FIELDS = [
    "salary",
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
    "employment_type",
]


def blank_row(posting_id: str, field: str, annotator_id: str) -> dict:
    return {
        "posting_id": posting_id,
        "field": field,
        "annotator_id": annotator_id,
        "status": None,  # human fills: "confirmed" | "vague" | "absent"
        "evidence_text": None,  # required (exact substring) if status is confirmed/vague; must stay null if absent
        "offsets": None,  # [start, end] into full_text, required with evidence_text
        "reason_code": None,  # short free-text reason, required once status is filled in
        "disagreement_note": None,  # optional; annotator's own note, not the adjudicator's
        "rubric_version": RUBRIC_VERSION,
    }


def main() -> None:
    posting_ids = []
    with POSTINGS_PATH.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                posting_ids.append(json.loads(line)["posting_id"])

    for annotator_id, filename in [("A", "annotator_A_template.jsonl"), ("B", "annotator_B_template.jsonl")]:
        out_path = REPO_ROOT / "data" / "annotation" / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for pid in posting_ids:
                for field in FIELDS:
                    f.write(json.dumps(blank_row(pid, field, annotator_id), ensure_ascii=False) + "\n")
        print(f"Wrote {len(posting_ids) * len(FIELDS)} blank rows to {out_path}")


if __name__ == "__main__":
    main()
