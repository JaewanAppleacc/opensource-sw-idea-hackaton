"""Measure occupation feasibility from real, ingested postings (Phase 2,
TASK_REAL_DATA_ACQUISITION.md).

Never assumes an occupation (e.g. 생산직(제조 조립원)) is final. Reads
data/intake/real_postings.jsonl (if it exists; treats a missing/empty file
as zero real postings collected so far — never invents a count) and reports,
per (occupation, employment_type) group, the raw counts the task's Phase 2
checklist requires:

  - jeonbuk_count / metro_count
  - pairable_count (min of the two — what a 10:10 or 20:20 check is against)
  - full_text_sufficient_count (non-trivial full text per region, a rough
    proxy for "enough原文 to six-field audit")
  - collection_date range per region (for judging same-period fit)
  - meets_min_10_10 / meets_target_20_20 (count-only; the second selection
    criterion in the task, "팀이 tools_or_skills/duties 경계를 사람 검수할 수
    있음", is NOT something this script can determine — it is left as
    `human_boundary_review_completed: null` for a human to fill in)

CLI:
  python scripts/acquisition/measure_feasibility.py \\
      [--postings data/intake/real_postings.jsonl] \\
      [--out data/intake/occupation_feasibility.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquisition_utils import read_jsonl  # noqa: E402

FULL_TEXT_SUFFICIENT_MIN_CHARS = 50


def _has_sufficient_text(record: dict[str, Any]) -> bool:
    text = record.get("full_text")
    if not text and record.get("full_text_available_privately"):
        # Public record redacted full_text for rights reasons; sufficiency
        # is still knowable because the private copy exists and was checked
        # at intake time (non-empty is enforced by manual_intake.py).
        return True
    return bool(text) and len(text.strip()) >= FULL_TEXT_SUFFICIENT_MIN_CHARS


def measure(postings: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for p in postings:
        groups[(p["occupation"], p["employment_type"])].append(p)

    candidates = []
    for (occupation, employment_type), recs in groups.items():
        by_region: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in recs:
            by_region[r["region_group"]].append(r)
        jeonbuk = by_region.get("jeonbuk", [])
        metro = by_region.get("metro", [])
        jb_count, met_count = len(jeonbuk), len(metro)
        pairable = min(jb_count, met_count)
        candidates.append(
            {
                "occupation": occupation,
                "employment_type": employment_type,
                "jeonbuk_count": jb_count,
                "metro_count": met_count,
                "pairable_count": pairable,
                "full_text_sufficient_count": {
                    "jeonbuk": sum(1 for r in jeonbuk if _has_sufficient_text(r)),
                    "metro": sum(1 for r in metro if _has_sufficient_text(r)),
                },
                "collection_dates": {
                    "jeonbuk": sorted({r.get("collection_date") for r in jeonbuk if r.get("collection_date")}),
                    "metro": sorted({r.get("collection_date") for r in metro if r.get("collection_date")}),
                },
                "meets_min_10_10": jb_count >= 10 and met_count >= 10,
                "meets_target_20_20": jb_count >= 20 and met_count >= 20,
                "human_boundary_review_completed": None,
            }
        )

    return {
        "measured_date": date.today().isoformat(),
        "total_real_postings_ingested": len(postings),
        "candidates": candidates,
        "overall_status": (
            "INSUFFICIENT_SAMPLE"
            if not postings or not any(c["meets_min_10_10"] for c in candidates)
            else "MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW"
        ),
        "note": (
            "meets_min_10_10 / meets_target_20_20 are raw-count checks only. "
            "Per TASK_REAL_DATA_ACQUISITION.md Phase 2, an occupation may "
            "only be finalized once a human has also confirmed "
            "tools_or_skills/duties boundaries are judgeable for it "
            "(human_boundary_review_completed)."
        ),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--postings", type=Path, default=Path("data/intake/real_postings.jsonl"))
    p.add_argument("--out", type=Path, default=Path("data/intake/occupation_feasibility.json"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    postings = read_jsonl(args.postings) if args.postings.exists() else []
    report = measure(postings)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote feasibility report ({report['overall_status']}) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
