"""Local, single-annotator review CLI (Phase D2 #2).

Reads exactly one packet file (one annotator's own rows) and the postings
file the packet references, and nothing else -- it never opens the other
annotator's file or `data/annotation/ai_suggestions.jsonl`, so isolation
is structural, not just a instruction to the human running it.

Per cell it:
  - shows the original posting full_text and the field currently being coded
  - asks for a status (confirmed / vague / absent)
  - for confirmed/vague, asks for the exact evidence substring and searches
    the source text for it; if it appears more than once, the human picks
    which occurrence with a printed context snippet
  - asks for a reason_code (required) and an optional note
  - saves the packet back to disk immediately after every answered cell, so
    the session can be interrupted and resumed by re-running the same
    command (already-answered cells are skipped unless --redo is passed)

This tool never proposes or infers a status -- it only makes typing an
already-decided answer, and finding its offset, less error-prone.

Usage:
  python scripts/annotation_ops/review_cli.py \\
      --packet data/private/annotation_run_001/annotator_A/packet.jsonl \\
      --postings /path/to/real_postings.jsonl
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import read_jsonl, write_jsonl


class QuitReview(Exception):
    pass


def find_all_occurrences(full_text: str, evidence_text: str) -> list[tuple[int, int]]:
    if not evidence_text:
        return []
    occurrences = []
    start = 0
    while True:
        idx = full_text.find(evidence_text, start)
        if idx == -1:
            break
        occurrences.append((idx, idx + len(evidence_text)))
        start = idx + 1
    return occurrences


def context_snippet(full_text: str, start: int, end: int, radius: int = 20) -> str:
    lo = max(0, start - radius)
    hi = min(len(full_text), end + radius)
    return f"...{full_text[lo:start]}[{full_text[start:end]}]{full_text[end:hi]}..."


def prompt_cell(posting_id: str, field: str, full_text: str, input_fn=input, print_fn=print) -> dict | None:
    """Returns a dict of the fields to update on the row, or None if the
    human chose to skip this cell for now. Raises QuitReview on 'quit'.
    """
    print_fn("=" * 60)
    print_fn(f"posting_id={posting_id} field={field}")
    print_fn(full_text)
    while True:
        status = input_fn("status [confirmed/vague/absent/skip/quit]: ").strip().lower()
        if status == "quit":
            raise QuitReview()
        if status == "skip":
            return None
        if status not in ("confirmed", "vague", "absent"):
            print_fn("  invalid status, try again")
            continue

        reason_code = input_fn("reason_code (short phrase from the rubric criterion you applied): ").strip()
        if not reason_code:
            print_fn("  reason_code is required, try again")
            continue
        note = input_fn("optional note (blank for none): ").strip() or None

        if status == "absent":
            return {
                "status": "absent",
                "evidence_text": None,
                "offsets": None,
                "reason_code": reason_code,
                "disagreement_note": note,
            }

        while True:
            evidence_text = input_fn("evidence_text (paste the exact excerpt from the posting above): ").strip()
            if not evidence_text:
                print_fn("  evidence_text is required for confirmed/vague, try again")
                continue
            occurrences = find_all_occurrences(full_text, evidence_text)
            if not occurrences:
                print_fn("  that text was not found verbatim in the posting -- try again (exact substring required)")
                continue
            break

        if len(occurrences) > 1:
            print_fn(f"  found {len(occurrences)} occurrences, choose one:")
            for i, (s, e) in enumerate(occurrences):
                print_fn(f"    [{i}] {context_snippet(full_text, s, e)}")
            while True:
                choice = input_fn("  choice index: ").strip()
                if choice.isdigit() and 0 <= int(choice) < len(occurrences):
                    break
                print_fn("  invalid choice, try again")
            offset = occurrences[int(choice)]
        else:
            offset = occurrences[0]

        return {
            "status": status,
            "evidence_text": evidence_text,
            "offsets": [offset[0], offset[1]],
            "reason_code": reason_code,
            "disagreement_note": note,
        }


def run_review_session(
    rows: list[dict],
    postings_by_id: dict[str, dict],
    input_fn=input,
    print_fn=print,
    save_fn=None,
    redo: bool = False,
    limit: int | None = None,
) -> dict:
    answered = 0
    quit_early = False
    for row in rows:
        if limit is not None and answered >= limit:
            break
        if row.get("status") is not None and not redo:
            continue
        posting = postings_by_id.get(row["posting_id"])
        if posting is None:
            print_fn(f"WARN: posting_id {row['posting_id']!r} not found in --postings file, skipping cell")
            continue
        full_text = posting.get("full_text", "")
        try:
            update = prompt_cell(row["posting_id"], row["field"], full_text, input_fn=input_fn, print_fn=print_fn)
        except QuitReview:
            quit_early = True
            break
        if update is None:
            continue
        row.update(update)
        answered += 1
        if save_fn is not None:
            save_fn()
    return {"answered": answered, "quit_early": quit_early}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packet", required=True, type=Path, help="This annotator's own packet.jsonl -- never the other annotator's file")
    ap.add_argument("--postings", required=True, type=Path, help="The postings JSONL the packet was built from")
    ap.add_argument("--redo", action="store_true", help="Revisit cells that already have a status, not just unanswered ones")
    ap.add_argument("--limit", type=int, default=None, help="Stop after answering this many cells this session")
    args = ap.parse_args()

    rows = read_jsonl(args.packet)
    if not rows:
        print(f"{args.packet}: packet is empty")
        return 1

    annotator_ids = {r.get("annotator_id") for r in rows}
    if len(annotator_ids) != 1:
        print(f"ERROR: {args.packet} has mixed or missing annotator_id values: {annotator_ids}")
        return 1

    postings = read_jsonl(args.postings)
    postings_by_id = {p["posting_id"]: p for p in postings}

    def save() -> None:
        write_jsonl(args.packet, rows)

    result = run_review_session(rows, postings_by_id, save_fn=save, redo=args.redo, limit=args.limit)
    save()

    total = len(rows)
    remaining = sum(1 for r in rows if r.get("status") is None)
    print(f"\nSaved {args.packet}")
    print(f"Answered this session: {result['answered']}")
    print(f"Remaining unanswered: {remaining}/{total}")
    if result["quit_early"]:
        print("Session ended early via 'quit'. Re-run the same command to resume where you left off.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
