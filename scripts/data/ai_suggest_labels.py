"""Generate AI (rule-based, deterministic) label SUGGESTIONS for the six
audited fields on every posting in data/postings/postings.jsonl.

Per CLAUDE.md / TASK_DATA_EVALUATION.md Phase 4:
  "AI may prepare suggestions in a visually separate column, but those
   suggestions must not be copied into gold automatically."

This script is intentionally NOT an LLM call: the data/evaluation track must
not depend on a model provider, and keeping the suggestion logic as plain
keyword/regex rules over data/rubric/rubric.yaml's own criteria keeps the
"suggestion vs. gold" boundary auditable in a code review. It also means
these suggestions can be wrong in exactly the ways a rushed human or a real
model would be wrong (e.g. missing a keyword phrased differently) -- that is
expected and is why they are suggestions, never gold.

Output: data/annotation/ai_suggestions.jsonl
Each record: {posting_id, field, suggested_status, evidence_text, offsets,
              ai_suggested: true, rubric_version}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTINGS_PATH = REPO_ROOT / "data" / "postings" / "postings.jsonl"
OUT_PATH = REPO_ROOT / "data" / "annotation" / "ai_suggestions.jsonl"
RUBRIC_VERSION = "1.0.0-draft"

FIELDS = [
    "salary",
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
    "employment_type",
]

# Sentence splitter tuned for these fixtures: Korean sentences here all end
# in a period. This is a heuristic, not a general-purpose tokenizer.
_SENT_SPLIT = re.compile(r"(?<=\.)\s+")

CONFIRMED_KEYWORDS = {
    "salary": ["만원"],
    "duties": ["조립 및 품질 검사", "성형기 운영", "포장 업무", "조립 라인 근무", "조립 보조 업무", "선별 및 포장"],
    "tools_or_skills": ["지게차", "PLC", "캘리퍼스", "도면 해독"],
    "training_or_mentoring": ["OJT", "사수", "안전교육"],
    "employment_type": ["정규직", "계약직"],
}

VAGUE_KEYWORDS = {
    "salary": ["내규", "협의"],
    "duties": ["업무 전반"],
    "tools_or_skills": ["관련 경험자"],
    "training_or_mentoring": ["교육 시스템"],
}


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def find_span(text: str, sentence: str) -> tuple[int, int]:
    start = text.index(sentence)
    return start, start + len(sentence)


def suggest_simple_field(field: str, text: str, sentences: list[str]) -> dict:
    for kw in CONFIRMED_KEYWORDS.get(field, []):
        for sent in sentences:
            if kw in sent:
                start, end = find_span(text, sent)
                return dict(status="confirmed", evidence_text=sent, offsets=[start, end])
    for kw in VAGUE_KEYWORDS.get(field, []):
        for sent in sentences:
            if kw in sent:
                start, end = find_span(text, sent)
                return dict(status="vague", evidence_text=sent, offsets=[start, end])
    return dict(status="absent", evidence_text=None, offsets=None)


def suggest_probation(text: str, sentences: list[str]) -> dict:
    duration_re = re.compile(r"\d+\s*(개월|주)")
    condition_tokens = ["%", "지급", "동일"]
    probation_sentences = [s for s in sentences if "수습" in s]
    if not probation_sentences:
        return dict(status="absent", evidence_text=None, offsets=None)
    for sent in probation_sentences:
        has_duration = bool(duration_re.search(sent))
        has_condition = any(tok in sent for tok in condition_tokens)
        if has_duration and has_condition:
            start, end = find_span(text, sent)
            return dict(status="confirmed", evidence_text=sent, offsets=[start, end])
    # Mentions probation but doesn't satisfy both conditions in one sentence.
    sent = probation_sentences[0]
    start, end = find_span(text, sent)
    return dict(status="vague", evidence_text=sent, offsets=[start, end])


def suggest_employment_type(text: str, sentences: list[str]) -> dict:
    result = suggest_simple_field("employment_type", text, sentences)
    if result["status"] != "absent":
        return result
    for sent in sentences:
        if ("채용형태" in sent or "고용형태" in sent) and "결정" in sent:
            start, end = find_span(text, sent)
            return dict(status="vague", evidence_text=sent, offsets=[start, end])
    return result


def suggest_all_fields(text: str) -> dict:
    sentences = split_sentences(text)
    out = {}
    for field in FIELDS:
        if field == "probation_terms":
            out[field] = suggest_probation(text, sentences)
        elif field == "employment_type":
            out[field] = suggest_employment_type(text, sentences)
        else:
            out[field] = suggest_simple_field(field, text, sentences)
    return out


def main() -> None:
    postings = []
    with POSTINGS_PATH.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                postings.append(json.loads(line))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for posting in postings:
            suggestions = suggest_all_fields(posting["full_text"])
            for field, sugg in suggestions.items():
                record = {
                    "posting_id": posting["posting_id"],
                    "field": field,
                    "suggested_status": sugg["status"],
                    "evidence_text": sugg["evidence_text"],
                    "offsets": sugg["offsets"],
                    "ai_suggested": True,
                    "rubric_version": RUBRIC_VERSION,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

    print(f"Wrote {count} AI suggestion records ({len(postings)} postings x {len(FIELDS)} fields) to {OUT_PATH}")


if __name__ == "__main__":
    main()
