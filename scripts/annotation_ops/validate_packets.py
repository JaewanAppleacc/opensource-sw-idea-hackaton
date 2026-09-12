"""Completeness + isolation validation for a pair of annotator packets
(Phase D2 #3).

Runs the existing schema/evidence checks from
`scripts/data/validate_dataset.py` against each packet unchanged, then adds
isolation checks that script has no reason to know about:

  - every row's `annotator_id` matches the packet it came from
  - packet A and packet B are not the same file (different resolved path
    AND different content checksum)
  - neither packet contains an AI-suggestion-only key
    (`ai_suggested` / `suggested_status`)
  - every row has an explicit boolean `synthetic_test_fixture` (never null
    or missing)
  - A and B agree on `synthetic_test_fixture` and `rubric_version` per cell,
    so a provenance mismatch is caught here with a precise message instead
    of surfacing later as a bare ValueError from adjudicate.py

Usage:
  python scripts/annotation_ops/validate_packets.py \\
      --packet-a data/private/annotation_run_001/annotator_A/packet.jsonl \\
      --packet-b data/private/annotation_run_001/annotator_B/packet.jsonl \\
      --postings /path/to/real_postings.jsonl \\
      [--allow-incomplete]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import AI_SUGGESTION_ONLY_KEYS, read_jsonl, sha256_of_file
from validate_dataset import validate_annotation_file


def is_packet_complete(records: list[dict]) -> bool:
    return all(r.get("status") is not None for r in records)


def check_annotator_id_isolation(records: list[dict], expected_annotator_id: str) -> list[str]:
    errors = []
    for i, rec in enumerate(records):
        aid = rec.get("annotator_id")
        if aid != expected_annotator_id:
            errors.append(
                f"row {i} ({rec.get('posting_id')}/{rec.get('field')}): "
                f"annotator_id {aid!r} != expected {expected_annotator_id!r}"
            )
    return errors


def check_no_ai_suggestion_keys(records: list[dict]) -> list[str]:
    errors = []
    for i, rec in enumerate(records):
        leaked = AI_SUGGESTION_ONLY_KEYS & rec.keys()
        if leaked:
            errors.append(
                f"row {i} ({rec.get('posting_id')}/{rec.get('field')}): "
                f"contains AI-suggestion-only key(s) {sorted(leaked)}"
            )
    return errors


def check_synthetic_flag_present(records: list[dict]) -> list[str]:
    errors = []
    for i, rec in enumerate(records):
        if not isinstance(rec.get("synthetic_test_fixture"), bool):
            errors.append(
                f"row {i} ({rec.get('posting_id')}/{rec.get('field')}): "
                "synthetic_test_fixture is missing or not a bool"
            )
    return errors


def check_files_distinct(path_a: Path, path_b: Path) -> list[str]:
    if Path(path_a).resolve() == Path(path_b).resolve():
        return ["packet A and packet B point to the same file path"]
    if sha256_of_file(path_a) == sha256_of_file(path_b):
        return ["packet A and packet B have identical content checksums -- are these really two independent annotators?"]
    return []


def check_cross_annotator_provenance(a_records: list[dict], b_records: list[dict]) -> list[str]:
    errors = []
    a_by_cell = {(r["posting_id"], r["field"]): r for r in a_records if r.get("posting_id") and r.get("field")}
    b_by_cell = {(r["posting_id"], r["field"]): r for r in b_records if r.get("posting_id") and r.get("field")}
    for cell in sorted(set(a_by_cell) & set(b_by_cell)):
        a_rec, b_rec = a_by_cell[cell], b_by_cell[cell]
        if a_rec.get("synthetic_test_fixture") != b_rec.get("synthetic_test_fixture"):
            errors.append(
                f"{cell}: synthetic_test_fixture disagrees between A "
                f"({a_rec.get('synthetic_test_fixture')!r}) and B ({b_rec.get('synthetic_test_fixture')!r})"
            )
        if a_rec.get("rubric_version") != b_rec.get("rubric_version"):
            errors.append(
                f"{cell}: rubric_version disagrees between A "
                f"({a_rec.get('rubric_version')!r}) and B ({b_rec.get('rubric_version')!r})"
            )
    return errors


def validate_packet_pair(
    path_a: Path,
    path_b: Path,
    postings_path: Path,
    allow_incomplete: bool = False,
) -> tuple[bool, dict[str, list[str]]]:
    postings = read_jsonl(postings_path)
    postings_by_id = {p["posting_id"]: p for p in postings}
    a_records = read_jsonl(path_a)
    b_records = read_jsonl(path_b)

    r_a = validate_annotation_file(a_records, postings_by_id, allow_incomplete=allow_incomplete)
    r_b = validate_annotation_file(b_records, postings_by_id, allow_incomplete=allow_incomplete)

    results: dict[str, list[str]] = {
        "annotator_A schema/evidence": r_a.errors,
        "annotator_B schema/evidence": r_b.errors,
        "annotator_A isolation (annotator_id)": check_annotator_id_isolation(a_records, "A"),
        "annotator_B isolation (annotator_id)": check_annotator_id_isolation(b_records, "B"),
        "annotator_A no AI-suggestion keys": check_no_ai_suggestion_keys(a_records),
        "annotator_B no AI-suggestion keys": check_no_ai_suggestion_keys(b_records),
        "annotator_A synthetic flag present": check_synthetic_flag_present(a_records),
        "annotator_B synthetic flag present": check_synthetic_flag_present(b_records),
        "A/B files distinct": check_files_distinct(path_a, path_b),
        "A/B cross-provenance": check_cross_annotator_provenance(a_records, b_records),
    }
    ok = all(len(errs) == 0 for errs in results.values())
    return ok, results


def _print_results(results: dict[str, list[str]]) -> None:
    for name, errors in results.items():
        print(f"--- {name} ---")
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
        else:
            print("  OK")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packet-a", required=True, type=Path)
    ap.add_argument("--packet-b", required=True, type=Path)
    ap.add_argument("--postings", required=True, type=Path)
    ap.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow null status cells (use while annotation is still in progress; adjudication still refuses incomplete packets regardless)",
    )
    args = ap.parse_args()

    ok, results = validate_packet_pair(args.packet_a, args.packet_b, args.postings, allow_incomplete=args.allow_incomplete)
    _print_results(results)

    print()
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
