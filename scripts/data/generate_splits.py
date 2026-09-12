"""Generate a stratified development/holdout split and a checksummed
manifest (Phase 5).

Design choices (documented here since Phase 5 leaves them to the
implementation):

  - The unit of splitting is a matched pair (both postings travel together),
    or a single posting for the two intentionally-unmatched records. This
    guarantees "both regions in the holdout" for free whenever at least one
    pair lands there, and keeps a Jeonbuk/metropolitan comparison intact
    within a split.
  - "Rare status" stratification is approximated by counting `absent` cells
    per unit from the supplied adjudicated-label file (absent is treated as
    the status most likely to be under-represented and most interesting to
    keep out of a single split). Units are sorted by descending rare-count
    so rare-status units are spread across dev/holdout rather than
    clustered.
  - The holdout size is chosen as whichever whole-unit prefix of that sorted
    list lands closest to floor(20% of postings), since 22 postings split
    into pair-units of size 2 (plus two size-1 units) cannot hit exactly
    20% every time.

This script deliberately works on ANY adjudicated-label file that follows
the adjudication_output.jsonl schema (posting_id, field, adjudicated_status)
-- including the synthetic demo file -- but the manifest it writes must
never be described as a gold split unless the input actually was gold. The
caller is responsible for that framing (see DATA_HANDOFF.md).

Usage:
  python scripts/data/generate_splits.py \\
      --postings data/postings/postings.jsonl \\
      --pairs data/postings/matched_pairs.jsonl \\
      --adjudicated data/demo_synthetic_annotations/adjudicated_demo.jsonl \\
      --rubric-version 1.0.0-draft \\
      --out-dir data/splits \\
      --label demo
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import read_jsonl, sha256_of_records, write_jsonl  # noqa: E402


def build_units(postings: list[dict]) -> list[dict]:
    by_pair: dict[str, list[str]] = {}
    unmatched: list[str] = []
    for p in postings:
        if p.get("unmatched"):
            unmatched.append(p["posting_id"])
        else:
            by_pair.setdefault(p["matched_pair_id"], []).append(p["posting_id"])

    units = [{"unit_id": pair_id, "posting_ids": ids} for pair_id, ids in sorted(by_pair.items())]
    units += [{"unit_id": pid, "posting_ids": [pid]} for pid in sorted(unmatched)]
    return units


def rare_status_counts(adjudicated: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in adjudicated:
        if row.get("adjudicated_status") == "absent":
            counts[row["posting_id"]] = counts.get(row["posting_id"], 0) + 1
    return counts


def choose_holdout_units(units: list[dict], rare_counts: dict[str, int], total_postings: int) -> list[dict]:
    def unit_rarity(unit: dict) -> int:
        return sum(rare_counts.get(pid, 0) for pid in unit["posting_ids"])

    sorted_units = sorted(units, key=lambda u: (-unit_rarity(u), u["unit_id"]))

    target = 0.2 * total_postings
    best_prefix_len = 0
    best_count = 0
    running = 0
    best_diff = abs(0 - target)
    for i, unit in enumerate(sorted_units, start=1):
        running += len(unit["posting_ids"])
        diff = abs(running - target)
        if diff <= best_diff:
            best_diff = diff
            best_prefix_len = i
            best_count = running

    return sorted_units[:best_prefix_len]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--postings", required=True, type=Path)
    ap.add_argument("--pairs", required=True, type=Path)
    ap.add_argument("--adjudicated", required=True, type=Path)
    ap.add_argument("--rubric-version", required=True)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--label", default="", help="Suffix for output filenames, e.g. 'demo'.")
    ap.add_argument(
        "--is-gold",
        action="store_true",
        help="Pass only when the --adjudicated file is a REAL, two-human-adjudicated gold dataset.",
    )
    args = ap.parse_args()

    postings = read_jsonl(args.postings)
    adjudicated = read_jsonl(args.adjudicated)

    units = build_units(postings)
    rare_counts = rare_status_counts(adjudicated)
    total_postings = len(postings)

    holdout_units = choose_holdout_units(units, rare_counts, total_postings)
    holdout_unit_ids = {u["unit_id"] for u in holdout_units}
    holdout_posting_ids = sorted(pid for u in holdout_units for pid in u["posting_ids"])

    dev_posting_ids = sorted(
        pid
        for u in units
        if u["unit_id"] not in holdout_unit_ids
        for pid in u["posting_ids"]
    )

    postings_by_id = {p["posting_id"]: p for p in postings}
    holdout_regions = {postings_by_id[pid]["region_group"] for pid in holdout_posting_ids}

    suffix = f"_{args.label}" if args.label else ""
    dev_path = args.out_dir / f"dev_split{suffix}.json"
    holdout_path = args.out_dir / f"holdout_split{suffix}.json"
    manifest_path = args.out_dir / f"manifest{suffix}.json"

    import json

    args.out_dir.mkdir(parents=True, exist_ok=True)
    dev_path.write_text(json.dumps({"split": "dev", "posting_ids": dev_posting_ids}, ensure_ascii=False, indent=2), encoding="utf-8")
    holdout_path.write_text(json.dumps({"split": "holdout", "posting_ids": holdout_posting_ids}, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rubric_version": args.rubric_version,
        "is_gold": args.is_gold,
        "source_adjudicated_file": str(args.adjudicated),
        "total_postings": total_postings,
        "dev_posting_ids": dev_posting_ids,
        "holdout_posting_ids": holdout_posting_ids,
        "holdout_fraction_actual": len(holdout_posting_ids) / total_postings,
        "holdout_regions_present": sorted(holdout_regions),
        "dev_checksum_sha256": sha256_of_records([{"posting_id": pid} for pid in dev_posting_ids]),
        "holdout_checksum_sha256": sha256_of_records([{"posting_id": pid} for pid in holdout_posting_ids]),
        "read_only_convention": (
            "The holdout split above must not be inspected or used for prompt/rubric "
            "tuning after this manifest is generated. Treat holdout_split*.json as "
            "read-only by convention; re-generating it after tuning defeats its purpose."
        ),
        "gold_status_note": (
            "This manifest is a GOLD split only if is_gold=true, which requires the "
            "source adjudicated file to come from two independent completed human "
            "annotation passes. See DATA_HANDOFF.md for current status."
            if not args.is_gold
            else "is_gold=true: verify this claim against DATA_HANDOFF.md before relying on it."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Dev split: {len(dev_posting_ids)} postings -> {dev_path}")
    print(f"Holdout split: {len(holdout_posting_ids)} postings ({manifest['holdout_fraction_actual']:.1%}) -> {holdout_path}")
    print(f"Holdout regions present: {sorted(holdout_regions)}")
    print(f"Manifest -> {manifest_path}")
    if not args.is_gold:
        print("NOTE: is_gold=false -- this is a non-gold demonstration split, not a reportable result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
