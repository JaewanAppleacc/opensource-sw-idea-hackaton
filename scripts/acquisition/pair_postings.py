"""Pair real Jeonbuk/metropolitan postings by occupation + employment type
(Phase 3, TASK_REAL_DATA_ACQUISITION.md section 3).

Reads data/intake/real_postings.jsonl (written by manual_intake.py and/or
work24_client.py), groups postings by (occupation, employment_type), and
pairs jeonbuk <-> metro records within each group in the order they appear
in the file (i.e. the order they were collected/entered — this script never
reorders by "how complete" a posting looks, only by group membership).
Leftover, unpaired records are marked `unmatched: true` with a factual,
non-interpretive reason (never a claim like "전북 일자리 부족 때문").

Writes data/intake/real_matched_pairs.jsonl and rewrites
data/intake/real_postings.jsonl in place with `matched_pair_id`,
`match_criteria`, `unmatched`, and `unmatched_reason` filled in — every other
field is preserved byte-for-byte.

CLI:
  python scripts/acquisition/pair_postings.py \\
      [--postings data/intake/real_postings.jsonl] \\
      [--pairs-out data/intake/real_matched_pairs.jsonl]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquisition_utils import read_jsonl, write_jsonl  # noqa: E402

UNMATCHED_REASON = (
    "표본 내 동일 직종·고용형태의 상대 지역 레코드가 남아있지 않음 "
    "(no remaining opposite-region record with the same occupation and "
    "employment_type in the current intake batch)"
)


def pair_postings(postings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"jeonbuk": [], "metro": []}
    )
    for p in postings:
        key = (p["occupation"], p["employment_type"])
        groups[key][p["region_group"]].append(p)

    pairs: list[dict[str, Any]] = []
    pair_seq = 0
    updated_by_id: dict[str, dict[str, Any]] = {p["posting_id"]: dict(p) for p in postings}

    for (occupation, employment_type), by_region in groups.items():
        jeonbuk_list = by_region["jeonbuk"]
        metro_list = by_region["metro"]
        n_pairs = min(len(jeonbuk_list), len(metro_list))
        for i in range(n_pairs):
            pair_seq += 1
            pair_id = f"P-REAL-{pair_seq:03d}"
            jb, met = jeonbuk_list[i], metro_list[i]
            match_criteria = (
                f"occupation={occupation}; employment_type={employment_type}; "
                f"source_name={jb.get('source_name')}/{met.get('source_name')}"
            )
            pairs.append(
                {
                    "matched_pair_id": pair_id,
                    "jeonbuk_posting_id": jb["posting_id"],
                    "metro_posting_id": met["posting_id"],
                    "occupation": occupation,
                    "employment_type": employment_type,
                    "match_criteria": match_criteria,
                }
            )
            for rec, opposite_id in ((jb, met["posting_id"]), (met, jb["posting_id"])):
                updated_by_id[rec["posting_id"]].update(
                    {
                        "matched_pair_id": pair_id,
                        "match_criteria": match_criteria,
                        "unmatched": False,
                        "unmatched_reason": None,
                    }
                )
        for leftover in jeonbuk_list[n_pairs:] + metro_list[n_pairs:]:
            updated_by_id[leftover["posting_id"]].update(
                {
                    "matched_pair_id": None,
                    "match_criteria": None,
                    "unmatched": True,
                    "unmatched_reason": UNMATCHED_REASON,
                }
            )

    updated_postings = [updated_by_id[p["posting_id"]] for p in postings]
    return updated_postings, pairs


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--postings", type=Path, default=Path("data/intake/real_postings.jsonl"))
    p.add_argument("--pairs-out", type=Path, default=Path("data/intake/real_matched_pairs.jsonl"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if not args.postings.exists():
        print(f"error: {args.postings} does not exist yet — run manual_intake.py first", file=sys.stderr)
        return 1
    postings = read_jsonl(args.postings)
    if not postings:
        print(f"error: {args.postings} is empty — nothing to pair", file=sys.stderr)
        return 1
    updated_postings, pairs = pair_postings(postings)
    write_jsonl(args.postings, updated_postings)
    write_jsonl(args.pairs_out, pairs)
    unmatched_count = sum(1 for p in updated_postings if p.get("unmatched"))
    print(f"wrote {len(pairs)} pair(s) to {args.pairs_out}; {unmatched_count} unmatched posting(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
