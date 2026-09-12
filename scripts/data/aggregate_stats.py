"""Compute descriptive statistics from human (adjudicated) gold labels only
(Phase 6).

Never computes anything from AI suggestions or from a single un-adjudicated
annotator file as if it were gold -- callers pass an adjudicated-label file
and must set --is-gold truthfully; the output JSON carries that flag forward
so downstream report generation cannot accidentally claim more than it
should.

Usage:
  python scripts/data/aggregate_stats.py \\
      --postings data/postings/postings.jsonl \\
      --pairs data/postings/matched_pairs.jsonl \\
      --adjudicated data/demo_synthetic_annotations/adjudicated_demo.jsonl \\
      --rubric-version 1.0.0-draft \\
      --out data/reports/demo_aggregate_stats.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import REQUIRED_FIELDS, read_jsonl  # noqa: E402

REQUIRED_REPORT_METADATA_NOTE = "exploratory sample; not population-generalizable"


def status_proportions_by_region_field(
    postings_by_id: dict[str, dict], adjudicated: list[dict]
) -> dict[str, dict[str, dict[str, float]]]:
    counts: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for row in adjudicated:
        pid = row["posting_id"]
        posting = postings_by_id.get(pid)
        if posting is None:
            continue
        region = posting["region_group"]
        field = row["field"]
        status = row.get("adjudicated_status")
        if status is None:
            continue
        counts[region][field][status] += 1

    result: dict[str, dict[str, dict[str, float]]] = {}
    for region, field_counts in counts.items():
        result[region] = {}
        for field, status_counts in field_counts.items():
            total = sum(status_counts.values())
            result[region][field] = {
                status: round(status_counts.get(status, 0) / total, 4) if total else 0.0
                for status in ("confirmed", "vague", "absent")
            }
            result[region][field]["_n"] = total
    return result


def matched_pair_descriptive_differences(pairs: list[dict], adjudicated_by_cell: dict[tuple[str, str], str]) -> dict:
    per_field_diff_count = Counter()
    per_field_total = Counter()
    pair_details = []
    for pair in pairs:
        jb_id = pair.get("jeonbuk_posting_id")
        met_id = pair.get("metro_posting_id")
        if not jb_id or not met_id:
            continue
        diffs = {}
        for field in REQUIRED_FIELDS:
            jb_status = adjudicated_by_cell.get((jb_id, field))
            met_status = adjudicated_by_cell.get((met_id, field))
            if jb_status is None or met_status is None:
                continue
            per_field_total[field] += 1
            differs = jb_status != met_status
            if differs:
                per_field_diff_count[field] += 1
            diffs[field] = {"jeonbuk": jb_status, "metro": met_status, "differs": differs}
        pair_details.append({"matched_pair_id": pair["matched_pair_id"], "field_status": diffs})

    per_field_diff_rate = {
        field: round(per_field_diff_count[field] / per_field_total[field], 4) if per_field_total[field] else None
        for field in REQUIRED_FIELDS
    }
    return {
        "per_field_status_differs_rate": per_field_diff_rate,
        "per_field_pairs_compared": {field: per_field_total[field] for field in REQUIRED_FIELDS},
        "pair_details": pair_details,
    }


def unmatched_summary(postings: list[dict]) -> dict:
    unmatched = [p for p in postings if p.get("unmatched")]
    return {
        "unmatched_count": len(unmatched),
        "unmatched_records": [
            {"posting_id": p["posting_id"], "region_group": p["region_group"], "reason": p.get("unmatched_reason")}
            for p in unmatched
        ],
        "interpretation_note": (
            "Unmatched records are observations only. They must not be interpreted as "
            "evidence of regional job scarcity."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--postings", required=True, type=Path)
    ap.add_argument("--pairs", required=True, type=Path)
    ap.add_argument("--adjudicated", required=True, type=Path)
    ap.add_argument("--rubric-version", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--is-gold", action="store_true")
    ap.add_argument("--data-source", default="synthetic_fixture_v1 (see data/sources/source_inventory.yaml)")
    ap.add_argument("--collection-period", default="n/a (synthetic fixtures; no real collection period)")
    args = ap.parse_args()

    postings = read_jsonl(args.postings)
    pairs = read_jsonl(args.pairs)
    adjudicated = read_jsonl(args.adjudicated)

    postings_by_id = {p["posting_id"]: p for p in postings}
    adjudicated_by_cell = {(r["posting_id"], r["field"]): r.get("adjudicated_status") for r in adjudicated}

    occupations = sorted({p["occupation"] for p in postings})
    employment_types = sorted({p["employment_type"] for p in postings})
    region_counts = Counter(p["region_group"] for p in postings)

    report = {
        "sample_size": len(postings),
        "posting_count_by_region": dict(region_counts),
        "cell_count": len(postings) * len(REQUIRED_FIELDS),
        "data_source": args.data_source,
        "collection_period": args.collection_period,
        "occupation": occupations,
        "employment_type": employment_types,
        "rubric_version": args.rubric_version,
        "is_gold": args.is_gold,
        "status_proportions_by_region_and_field": status_proportions_by_region_field(postings_by_id, adjudicated),
        "matched_pair_descriptive_differences": matched_pair_descriptive_differences(pairs, adjudicated_by_cell),
        "unmatched": unmatched_summary(postings),
        "disclaimer": REQUIRED_REPORT_METADATA_NOTE,
        "gold_status_note": (
            "is_gold=true: verify against DATA_HANDOFF.md before citing."
            if args.is_gold
            else "is_gold=false: these statistics are computed from a NON-GOLD synthetic/demo "
            "adjudicated file and exist only to prove the statistics code path works. "
            "They are not a claim about real Jeonbuk or metropolitan postings."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote aggregate stats to {args.out}")
    print(f"sample_size={report['sample_size']} is_gold={report['is_gold']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
