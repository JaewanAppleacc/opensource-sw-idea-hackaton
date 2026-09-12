"""Render the JSON output of aggregate_stats.py into a careful, human-readable
Markdown exploratory report (Phase 6).

Wording rules enforced by construction (not just convention):
  - Every report opens with sample size, source, period, occupation,
    employment type, and rubric version pulled straight from the input JSON
    -- never re-typed by hand.
  - The "exploratory sample; not population-generalizable" disclaimer is
    always the second line.
  - If the input JSON has is_gold=false, the report is prefixed with a loud
    NOT GOLD banner and every statistic is captioned accordingly. Nothing in
    generate_report.py can flip is_gold to true; it only reads what
    aggregate_stats.py already decided.

Usage:
  python scripts/data/generate_report.py \\
      --stats data/reports/demo_aggregate_stats.json \\
      --out data/reports/demo_exploratory_report.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(stats: dict) -> str:
    lines: list[str] = []
    is_gold = stats.get("is_gold", False)

    if not is_gold:
        lines.append("# ⚠️ NOT GOLD — synthetic/demo data, pipeline-verification report")
        lines.append("")
        lines.append(
            "**This report is generated from a non-gold, synthetic/demo adjudicated "
            "file.** It exists only to prove the statistics and reporting code runs "
            "correctly end to end. It is not a claim about real Jeonbuk or "
            "metropolitan postings. See `DATA_HANDOFF.md` for what real annotation "
            "work remains."
        )
    else:
        lines.append("# Exploratory sample report")

    lines.append("")
    lines.append(f"**{stats['disclaimer']}**")
    lines.append("")
    lines.append("## Sample")
    lines.append(f"- Sample size: {stats['sample_size']} postings ({stats['cell_count']} audited cells)")
    lines.append(f"- Posting count by region: {stats['posting_count_by_region']}")
    lines.append(f"- Data source: {stats['data_source']}")
    lines.append(f"- Collection period: {stats['collection_period']}")
    lines.append(f"- Occupation(s): {', '.join(stats['occupation'])}")
    lines.append(f"- Employment type(s): {', '.join(stats['employment_type'])}")
    lines.append(f"- Rubric version: {stats['rubric_version']}")
    lines.append("")

    lines.append("## Status proportions by region and field")
    lines.append("")
    lines.append("| Region | Field | confirmed | vague | absent | n |")
    lines.append("|---|---|---|---|---|---|")
    for region, fields in stats["status_proportions_by_region_and_field"].items():
        for field, props in fields.items():
            lines.append(
                f"| {region} | {field} | {props['confirmed']:.0%} | {props['vague']:.0%} | "
                f"{props['absent']:.0%} | {props['_n']} |"
            )
    lines.append("")

    mp = stats["matched_pair_descriptive_differences"]
    lines.append("## Matched-pair descriptive differences (per field, share of pairs where the two postings' statuses differ)")
    lines.append("")
    lines.append("| Field | Pairs compared | Differ rate |")
    lines.append("|---|---|---|")
    for field, rate in mp["per_field_status_differs_rate"].items():
        n_compared = mp["per_field_pairs_compared"].get(field, 0)
        rate_str = f"{rate:.0%}" if rate is not None else "n/a"
        lines.append(f"| {field} | {n_compared} | {rate_str} |")
    lines.append("")
    lines.append(
        "These are descriptive differences within this specific matched sample only. "
        "They are not a statement about typical postings in either region."
    )
    lines.append("")

    unmatched = stats["unmatched"]
    lines.append("## Unmatched records")
    lines.append(f"- Unmatched count: {unmatched['unmatched_count']}")
    for rec in unmatched["unmatched_records"]:
        lines.append(f"  - {rec['posting_id']} ({rec['region_group']}): {rec['reason']}")
    lines.append(f"- {unmatched['interpretation_note']}")
    lines.append("")

    lines.append("## Status")
    lines.append(f"- {stats['gold_status_note']}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    stats = json.loads(args.stats.read_text(encoding="utf-8"))
    report_md = render(stats)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report_md, encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
