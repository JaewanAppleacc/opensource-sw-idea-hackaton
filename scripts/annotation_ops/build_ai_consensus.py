"""Builds the AI-A/B consensus + human-adjudication reference set for the
real 20-posting batch (Parallel task: P0 frontend-backend integration,
section 3).

This is NOT human gold. It never claims to be. Two independent AI review
passes (`data/private/ai_reviews/agent_A_suggestions.jsonl`,
`agent_B_suggestions.jsonl`, both `reviewer_type: "ai"`) were compared
cell-by-cell on `suggested_status`. Cells where both agreed are recorded as
`resolution_source: ai_consensus`. The small number where they disagreed
were reviewed by a human team lead against the rubric and the real posting
text and are recorded as `resolution_source: human_adjudicated`, each with
a real `adjudicator_note` explaining which rubric criterion applied --
never a bare "AI-B에 동의함".

Never sets `human_boundary_review_completed` or `is_gold` -- those remain
exactly what they were (see docs/data/HUMAN_ANNOTATION_RUNBOOK.md).

Usage:
  python scripts/annotation_ops/build_ai_consensus.py \\
      --agent-a data/private/ai_reviews/agent_A_suggestions.jsonl \\
      --agent-b data/private/ai_reviews/agent_B_suggestions.jsonl \\
      --out data/private/ai_reviews/ai_consensus_adjudicated.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Fixed, human-authored resolutions for the cells where AI-A and AI-B's
# suggested_status disagreed. Each note names the rubric criterion actually
# applied -- see data/rubric/rubric.yaml (duties, tools_or_skills) for the
# full text these paraphrase.
HUMAN_ADJUDICATIONS: dict[tuple[str, str], dict[str, str]] = {
    ("JB-01", "tools_or_skills"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "'스폿용접, 탭핑'은 담당업무 서술 안에 있지만 두 용어 모두 구체적인 "
            "가공/체결 기법명이다. rubric.yaml tools_or_skills의 occupation_mapping은 "
            "'명시적 기술(도면 해독 등)'을 named skill로 인정하며, 같은 문장이 duties "
            "근거로도 쓰였다는 사실이 tools_or_skills 판정을 막지 않는다. confirmed로 조정."
        ),
    },
    ("JB-02", "tools_or_skills"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "'사상'(연마/다듬질 가공)은 일반적 경력 요구가 아니라 구체적으로 이름 붙은 "
            "가공 기법이다. JB-01과 동일한 occupation_mapping 기준(named skill)을 적용해 "
            "confirmed로 조정. AI-A가 채택한 '발전플랜트 또는 중공업 유경험자 우대'는 "
            "여전히 vague 수준이지만, 본문에 더 구체적인 '사상' 근거가 별도로 존재함."
        ),
    },
    ("JB-07", "duties"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "duties confirmed의 deterministic_check는 'evidence_text length >= 8자'이며, "
            "'자동차 부품 생산업무'(10자)는 이를 충족한다. 특정 제품군(자동차 부품)을 "
            "명시했고, positive_examples('사출 성형기 운영 및 제품 포장 업무 수행')도 "
            "구체적 행위 동사보다 대상/제품 특정을 기준으로 삼는다. confirmed로 조정."
        ),
    },
    ("JB-10", "duties"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "'조립 로봇 제품 생산'(11자)도 JB-07과 동일하게 길이 기준을 충족하고 특정 "
            "제품군(조립 로봇 제품)을 지칭한다. AI-A가 지적한 모호성(제품이 조립 대상인지 "
            "조립 설비인지)은 실제 존재하나, 원문에 이를 더 명확히 하는 문구가 없어 이 "
            "수준의 제품 특정만으로 confirmed 기준(자세한 동사보다 대상 특정)을 적용."
        ),
    },
    ("MET-02", "tools_or_skills"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "duties 근거 문장에 함께 등장하는 '사상'을 tools_or_skills로도 인정한 JB-02 "
            "판정과 형평성을 맞춤 -- 같은 기법명이 반복되는 원문에서 다르게 판정할 근거가 "
            "없음. AI-A는 이 문장 자체를 후보에서 제외해 absent로 처리했으나 재검토 결과 "
            "'사상'이 실제로 존재하므로 confirmed로 조정."
        ),
    },
    ("MET-03", "tools_or_skills"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "'검사 및 사상'은 제목 줄에만 등장하고 본문 상세 업무는 '검사 및 포장'으로 "
            "재서술되어 boundary 사례이지만, 제목도 공고 원문의 일부이며 '사상'은 MET-02/"
            "JB-02와 동일하게 구체적 가공 기법명이다. 배치 전체에서 '사상' 처리 기준을 "
            "통일하기 위해 confirmed로 조정."
        ),
    },
    ("MET-06", "duties"): {
        "final_status": "confirmed",
        "adjudicator_note": (
            "'가로등주, 신호등주, LED교통신호등, 버스정류장, 조립식구조물, 방음판 등 "
            "생산직'(46자)은 길이 기준을 크게 상회하고, 지원자가 실제로 관여할 여러 "
            "제품군을 구체적으로 열거한다. AI-A가 지적한 대로 개별 조립/가공 동사는 "
            "없지만, JB-07/JB-10과 동일하게 '제품 특정'을 confirmed 기준으로 적용."
        ),
    },
}


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_consensus_rows(agent_a: list[dict], agent_b: list[dict]) -> list[dict]:
    by_key_a = {(r["posting_id"], r["field"]): r for r in agent_a}
    by_key_b = {(r["posting_id"], r["field"]): r for r in agent_b}
    if set(by_key_a) != set(by_key_b):
        raise ValueError("agent A and agent B do not cover the exact same (posting_id, field) cells")

    rows = []
    for key in sorted(by_key_a.keys()):
        ra, rb = by_key_a[key], by_key_b[key]
        posting_id, field = key
        status_a, status_b = ra["suggested_status"], rb["suggested_status"]
        initial_agreement = status_a == status_b

        if key in HUMAN_ADJUDICATIONS:
            resolution = HUMAN_ADJUDICATIONS[key]
            final_status = resolution["final_status"]
            resolution_source = "human_adjudicated"
            adjudicator_note = resolution["adjudicator_note"]
        else:
            if not initial_agreement:
                raise ValueError(
                    f"{key}: agent statuses disagree ({status_a!r} vs {status_b!r}) but no human "
                    "adjudication is recorded for this cell -- refusing to guess a resolution"
                )
            final_status = status_a
            resolution_source = "ai_consensus"
            adjudicator_note = None

        rows.append(
            {
                "posting_id": posting_id,
                "field": field,
                "agent_a_status": status_a,
                "agent_b_status": status_b,
                "agent_a_evidence_text": ra.get("evidence_text"),
                "agent_a_offsets": ra.get("offsets"),
                "agent_b_evidence_text": rb.get("evidence_text"),
                "agent_b_offsets": rb.get("offsets"),
                "initial_agreement": initial_agreement,
                "final_status": final_status,
                "resolution_source": resolution_source,
                "adjudicator_note": adjudicator_note,
                "reviewer_type": "ai_consensus_with_human_adjudication",
                "is_gold": False,
                "rubric_version": ra["rubric_version"],
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent-a", required=True, type=Path)
    ap.add_argument("--agent-b", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    agent_a = read_jsonl(args.agent_a)
    agent_b = read_jsonl(args.agent_b)
    rows = build_consensus_rows(agent_a, agent_b)
    write_jsonl(args.out, rows)

    n_total = len(rows)
    n_agree = sum(1 for r in rows if r["initial_agreement"])
    n_human = sum(1 for r in rows if r["resolution_source"] == "human_adjudicated")
    status_counts: dict[str, int] = {}
    for r in rows:
        status_counts[r["final_status"]] = status_counts.get(r["final_status"], 0) + 1

    print(f"wrote {n_total} rows to {args.out}")
    print(f"initial AI-A/B agreement: {n_agree}/{n_total} ({100 * n_agree / n_total:.1f}%)")
    print(f"human_adjudicated: {n_human}")
    print(f"final_status distribution: {status_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
