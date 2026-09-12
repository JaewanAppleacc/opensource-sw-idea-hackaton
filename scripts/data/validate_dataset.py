"""Dataset + annotation validator (Phase 4 deliverable).

Checks, per TASK_DATA_EVALUATION.md Phase 4:
  - six fields per posting (no more, no fewer, no duplicates)
  - allowed statuses only (confirmed/vague/absent)
  - evidence required for confirmed/vague
  - null evidence for absent
  - offset and substring correctness
  - no duplicate IDs
  - matched-pair integrity

Usable as a library (import the `validate_*` functions, e.g. from tests) or
as a CLI:

  python scripts/data/validate_dataset.py \\
      --postings data/postings/postings.jsonl \\
      --pairs data/postings/matched_pairs.jsonl \\
      [--annotations FILE ...] [--allow-incomplete]

Exit code 0 = no errors found. Exit code 1 = at least one error found.
Warnings (e.g. incomplete/pending cells) never fail the run on their own.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import ALLOWED_STATUSES, REQUIRED_FIELDS, load_postings_by_id, read_jsonl  # noqa: E402


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_postings(postings: list[dict]) -> ValidationResult:
    r = ValidationResult()
    seen_ids: set[str] = set()
    for i, p in enumerate(postings):
        pid = p.get("posting_id")
        if not pid:
            r.error(f"postings[{i}]: missing posting_id")
            continue
        if pid in seen_ids:
            r.error(f"duplicate posting_id: {pid}")
        seen_ids.add(pid)

        if p.get("region_group") not in {"jeonbuk", "metro"}:
            r.error(f"{pid}: region_group must be 'jeonbuk' or 'metro', got {p.get('region_group')!r}")
        if not p.get("occupation"):
            r.error(f"{pid}: missing occupation")
        if not p.get("employment_type"):
            r.error(f"{pid}: missing employment_type")
        if not p.get("full_text"):
            r.error(f"{pid}: missing full_text")

        unmatched = p.get("unmatched", False)
        if unmatched:
            if p.get("matched_pair_id") is not None:
                r.error(f"{pid}: unmatched=true but matched_pair_id is not null")
            if not p.get("unmatched_reason"):
                r.error(f"{pid}: unmatched=true requires a factual unmatched_reason")
        else:
            if not p.get("matched_pair_id"):
                r.error(f"{pid}: unmatched=false but matched_pair_id is missing")
            if p.get("unmatched_reason"):
                r.error(f"{pid}: unmatched=false but unmatched_reason is set")
    return r


def validate_matched_pairs(pairs: list[dict], postings_by_id: dict[str, dict]) -> ValidationResult:
    r = ValidationResult()
    seen_pair_ids: set[str] = set()
    for p in pairs:
        pair_id = p.get("matched_pair_id")
        if not pair_id:
            r.error("matched_pairs: row missing matched_pair_id")
            continue
        if pair_id in seen_pair_ids:
            r.error(f"duplicate matched_pair_id: {pair_id}")
        seen_pair_ids.add(pair_id)

        jb_id = p.get("jeonbuk_posting_id")
        met_id = p.get("metro_posting_id")
        if not jb_id or jb_id not in postings_by_id:
            r.error(f"{pair_id}: jeonbuk_posting_id {jb_id!r} not found in postings")
            continue
        if not met_id or met_id not in postings_by_id:
            r.error(f"{pair_id}: metro_posting_id {met_id!r} not found in postings")
            continue

        jb = postings_by_id[jb_id]
        met = postings_by_id[met_id]
        if jb.get("occupation") != met.get("occupation"):
            r.error(f"{pair_id}: occupation mismatch between {jb_id} and {met_id}")
        if jb.get("employment_type") != met.get("employment_type"):
            r.error(f"{pair_id}: employment_type mismatch between {jb_id} and {met_id}")
        if jb.get("matched_pair_id") != pair_id:
            r.error(f"{pair_id}: {jb_id}.matched_pair_id does not point back to {pair_id}")
        if met.get("matched_pair_id") != pair_id:
            r.error(f"{pair_id}: {met_id}.matched_pair_id does not point back to {pair_id}")
    return r


def validate_annotation_file(
    records: list[dict],
    postings_by_id: dict[str, dict],
    allow_incomplete: bool = False,
) -> ValidationResult:
    r = ValidationResult()
    seen_cells: set[tuple[str, str]] = set()
    per_posting_fields: dict[str, set[str]] = {}

    for i, rec in enumerate(records):
        pid = rec.get("posting_id")
        field = rec.get("field")
        loc = f"row {i} ({pid}/{field})"

        if not pid or pid not in postings_by_id:
            r.error(f"{loc}: posting_id {pid!r} not found in postings")
            continue
        if field not in REQUIRED_FIELDS:
            r.error(f"{loc}: field {field!r} is not one of {REQUIRED_FIELDS}")
            continue

        cell = (pid, field)
        if cell in seen_cells:
            r.error(f"{loc}: duplicate cell for {cell}")
        seen_cells.add(cell)
        per_posting_fields.setdefault(pid, set()).add(field)

        status = rec.get("status")
        if status is None:
            if allow_incomplete:
                r.warn(f"{loc}: status not yet filled in (incomplete)")
                continue
            r.error(f"{loc}: status is null and --allow-incomplete was not set")
            continue

        if status not in ALLOWED_STATUSES:
            r.error(f"{loc}: status {status!r} is not one of {sorted(ALLOWED_STATUSES)}")
            continue

        evidence_text = rec.get("evidence_text")
        offsets = rec.get("offsets")

        if status == "absent":
            if evidence_text is not None or offsets is not None:
                r.error(f"{loc}: status=absent requires evidence_text and offsets to be null")
            continue

        # confirmed / vague
        if not evidence_text:
            r.error(f"{loc}: status={status} requires a non-empty evidence_text")
            continue
        if not (isinstance(offsets, list) and len(offsets) == 2):
            r.error(f"{loc}: status={status} requires offsets as [start, end], got {offsets!r}")
            continue

        start, end = offsets
        if not (isinstance(start, int) and isinstance(end, int) and 0 <= start < end):
            r.error(f"{loc}: offsets {offsets!r} are not a valid non-empty [start, end) range")
            continue

        full_text = postings_by_id[pid].get("full_text", "")
        substring = full_text[start:end]
        if substring != evidence_text:
            r.error(
                f"{loc}: evidence_text does not match full_text[{start}:{end}] "
                f"(expected {substring!r}, got {evidence_text!r})"
            )

        if not rec.get("reason_code"):
            r.error(f"{loc}: status={status} requires a non-empty reason_code")

    for pid, fields in per_posting_fields.items():
        missing = set(REQUIRED_FIELDS) - fields
        if missing:
            r.error(f"{pid}: missing annotation cells for fields {sorted(missing)}")

    return r


def _print_result(name: str, result: ValidationResult) -> None:
    print(f"--- {name} ---")
    if result.errors:
        for e in result.errors:
            print(f"  ERROR: {e}")
    if result.warnings:
        for w in result.warnings:
            print(f"  WARNING: {w}")
    if result.ok and not result.warnings:
        print("  OK")
    elif result.ok:
        print(f"  OK ({len(result.warnings)} warning(s))")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--postings", required=True, type=Path)
    ap.add_argument("--pairs", required=True, type=Path)
    ap.add_argument("--annotations", nargs="*", default=[], type=Path)
    ap.add_argument("--allow-incomplete", action="store_true")
    args = ap.parse_args()

    postings = read_jsonl(args.postings)
    pairs = read_jsonl(args.pairs)
    postings_by_id = {p["posting_id"]: p for p in postings}

    overall_ok = True

    r_postings = validate_postings(postings)
    _print_result(f"postings ({args.postings})", r_postings)
    overall_ok &= r_postings.ok

    r_pairs = validate_matched_pairs(pairs, postings_by_id)
    _print_result(f"matched_pairs ({args.pairs})", r_pairs)
    overall_ok &= r_pairs.ok

    for ann_path in args.annotations:
        records = read_jsonl(ann_path)
        r_ann = validate_annotation_file(records, postings_by_id, allow_incomplete=args.allow_incomplete)
        _print_result(f"annotations ({ann_path})", r_ann)
        overall_ok &= r_ann.ok

    print()
    print("PASS" if overall_ok else "FAIL")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
