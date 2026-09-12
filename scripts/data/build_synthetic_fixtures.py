"""Build the synthetic (NOT real) posting corpus used to exercise the data
pipeline end to end.

Why this exists: as of the date in data/sources/source_inventory.yaml, no
real Jeonbuk/metropolitan postings had been obtained (the one plausible
public source, the 고용24/워크넷 Open API, requires a human-completed
data.go.kr credential application). Per TASK_DATA_EVALUATION.md Phase 3,
"generate separate synthetic fixtures for repository tests and demos" is the
explicitly sanctioned fallback -- this script is that fallback, kept as
plain, reviewable code instead of hand-typed JSON so the fictional origin of
every field is obvious.

Every posting produced here is self-authored fiction: fictional company
names, fictional numbers, fictional locations used only as label diversity.
`source_name` is always "synthetic_fixture_v1" and `source_id_url` is always
null so nothing here can be mistaken for a scraped or sourced record.

Run: python scripts/data/build_synthetic_fixtures.py
Writes: data/postings/postings.jsonl, data/postings/matched_pairs.jsonl
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTINGS_PATH = REPO_ROOT / "data" / "postings" / "postings.jsonl"
PAIRS_PATH = REPO_ROOT / "data" / "postings" / "matched_pairs.jsonl"

OCCUPATION = "생산직(제조 조립원)"
FIXTURE_BUILD_DATE = "2026-09-12"
SOURCE_NAME = "synthetic_fixture_v1"

# Each tuple: (posting_id, region_group, municipality, employment_type,
#              company, full_text)
# full_text is hand-composed so that ai_suggest_labels.py can locate each
# field's evidence span with a plain substring search -- offsets are
# computed from this exact text, never hand-counted.

POSTINGS: list[dict] = [
    dict(
        posting_id="JB-001", region_group="jeonbuk", municipality="전주시",
        employment_type="정규직", company="(예시) 가상제조 전주1호(주)",
        full_text=(
            "(예시) 가상제조 전주1호(주)에서 생산직(제조 조립원)을 모집합니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "지게차 운전면허 소지자 우대하며 관련 경험이 있으면 더욱 좋습니다. "
            "월급 235만원(세전) 지급. 수습기간 3개월 적용하며 자세한 급여 조건은 "
            "면접 시 안내합니다. 고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="JB-002", region_group="jeonbuk", municipality="전주시",
        employment_type="정규직", company="(예시) 가상제조 전주2호(주)",
        full_text=(
            "(예시) 가상제조 전주2호(주) 생산부서 신규 인원 채용 공고입니다. "
            "사출 성형기 운영 및 제품 포장 업무를 수행합니다. "
            "PLC 설비 조작 경험자 및 도면 해독 능력 보유자를 우대합니다. "
            "급여는 경력에 따라 협의 후 결정합니다. "
            "입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. "
            "수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. "
            "고용형태: 정규직."
        ),
    ),
    dict(
        posting_id="JB-003", region_group="jeonbuk", municipality="전주시",
        employment_type="정규직", company="(예시) 가상산업 전주3호",
        full_text=(
            "(예시) 가상산업 전주3호에서 생산 인력을 채용합니다. "
            "생산 관련 업무 전반을 수행합니다. 관련 경험자 우대합니다. "
            "채용형태는 면접 후 결정합니다."
        ),
    ),
    dict(
        posting_id="JB-004", region_group="jeonbuk", municipality="군산시",
        employment_type="정규직", company="(예시) 가상모터스 군산1호(주)",
        full_text=(
            "(예시) 가상모터스 군산1호(주)에서 생산직(제조 조립원)을 모집합니다. "
            "차량 부품 조립 라인 근무 및 공정 검사 업무를 담당합니다. "
            "지게차 운전면허 및 캘리퍼스 사용 가능자를 우대합니다. "
            "월급 250만원(세전) 지급합니다. "
            "매월 1회 정기 안전교육을 제공합니다. "
            "수습기간 3개월, 수습기간 동안 동일 급여 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="JB-005", region_group="jeonbuk", municipality="군산시",
        employment_type="정규직", company="(예시) 가상부품 군산2호",
        full_text=(
            "(예시) 가상부품 군산2호 생산라인 인원 모집 공고입니다. "
            "생산 관련 업무 전반을 수행합니다. "
            "급여는 회사 내규에 따라 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="JB-006", region_group="jeonbuk", municipality="군산시",
        employment_type="정규직", company="(예시) 가상기계 군산3호(주)",
        full_text=(
            "(예시) 가상기계 군산3호(주)에서 조립 생산직을 채용합니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "관련 경험자를 우대합니다. "
            "월급 240만원(세전) 지급합니다. "
            "입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. "
            "수습기간 있음(세부 조건은 면접 시 안내). "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="JB-007", region_group="jeonbuk", municipality="익산시",
        employment_type="정규직", company="(예시) 가상농산 익산1호",
        full_text=(
            "(예시) 가상농산 익산1호에서 인원을 모집합니다. "
            "성실하고 책임감 있는 분을 찾습니다."
        ),
    ),
    dict(
        posting_id="JB-008", region_group="jeonbuk", municipality="익산시",
        employment_type="정규직", company="(예시) 가상전자 익산2호(주)",
        full_text=(
            "(예시) 가상전자 익산2호(주)에서 생산직(제조 조립원)을 모집합니다. "
            "완성차 부품 조립 업무를 담당합니다. "
            "관련 경험자 우대합니다. "
            "급여는 경력에 따라 협의 후 결정합니다. "
            "체계적인 교육 시스템을 운영하고 있습니다. "
            "수습기간 있음(세부 조건은 면접 시 안내). "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="JB-009", region_group="jeonbuk", municipality="완주군",
        employment_type="정규직", company="(예시) 가상정밀 완주1호(주)",
        full_text=(
            "(예시) 가상정밀 완주1호(주)에서 생산직(제조 조립원)을 채용합니다. "
            "사출 성형기 운영 및 제품 포장 업무를 수행합니다. "
            "도면 해독 능력 및 캘리퍼스 사용 가능자를 우대합니다. "
            "월급 245만원(세전) 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="JB-010", region_group="jeonbuk", municipality="정읍시",
        employment_type="정규직", company="(예시) 가상식품 정읍1호",
        full_text=(
            "(예시) 가상식품 정읍1호 생산라인 인원 모집입니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "급여는 회사 내규에 따라 지급합니다. "
            "수습기간 있음(세부 조건은 면접 시 안내). "
            "채용형태는 면접 후 결정합니다."
        ),
    ),
    # --- Metropolitan matches ---
    dict(
        posting_id="MET-001", region_group="metro", municipality="서울특별시",
        employment_type="정규직", company="(예시) 가상제조 서울1호(주)",
        full_text=(
            "(예시) 가상제조 서울1호(주)에서 생산직(제조 조립원)을 모집합니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "지게차 운전면허 및 PLC 설비 조작 경험자를 우대합니다. "
            "월급 270만원(세전) 지급합니다. "
            "입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. "
            "수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-002", region_group="metro", municipality="서울특별시",
        employment_type="정규직", company="(예시) 가상모터스 서울2호(주)",
        full_text=(
            "(예시) 가상모터스 서울2호(주) 생산부서 채용 공고입니다. "
            "사출 성형기 운영 및 제품 포장 업무를 수행합니다. "
            "관련 경험자를 우대합니다. "
            "월급 265만원(세전) 지급합니다. "
            "매월 1회 정기 안전교육 및 사내 직무교육을 제공합니다. "
            "수습기간 3개월, 수습기간 동안 동일 급여 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-003", region_group="metro", municipality="인천광역시",
        employment_type="정규직", company="(예시) 가상부품 인천1호(주)",
        full_text=(
            "(예시) 가상부품 인천1호(주)에서 생산직(제조 조립원)을 채용합니다. "
            "차량 부품 조립 라인 근무 및 공정 검사 업무를 담당합니다. "
            "도면 해독 능력 및 캘리퍼스 사용 가능자를 우대합니다. "
            "월급 268만원(세전) 지급합니다. "
            "체계적인 교육 시스템을 운영하고 있습니다. "
            "수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-004", region_group="metro", municipality="인천광역시",
        employment_type="정규직", company="(예시) 가상기계 인천2호",
        full_text=(
            "(예시) 가상기계 인천2호 생산라인 인원 모집 공고입니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "지게차 운전면허 소지자를 우대합니다. "
            "급여는 경력에 따라 협의 후 결정합니다. "
            "입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. "
            "수습기간 있음(세부 조건은 면접 시 안내). "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-005", region_group="metro", municipality="부산광역시",
        employment_type="정규직", company="(예시) 가상정밀 부산1호(주)",
        full_text=(
            "(예시) 가상정밀 부산1호(주)에서 생산직(제조 조립원)을 모집합니다. "
            "사출 성형기 운영 및 제품 포장 업무를 수행합니다. "
            "관련 경험자를 우대합니다. "
            "월급 260만원(세전) 지급합니다. "
            "매월 1회 정기 안전교육을 제공합니다. "
            "수습기간 3개월, 수습기간 동안 동일 급여 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-006", region_group="metro", municipality="부산광역시",
        employment_type="정규직", company="(예시) 가상전자 부산2호(주)",
        full_text=(
            "(예시) 가상전자 부산2호(주) 생산직 채용 공고입니다. "
            "생산 관련 업무 전반을 수행합니다. "
            "PLC 설비 조작 경험자 및 도면 해독 능력 보유자를 우대합니다. "
            "월급 262만원(세전) 지급합니다. "
            "수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-007", region_group="metro", municipality="대구광역시",
        employment_type="정규직", company="(예시) 가상산업 대구1호(주)",
        full_text=(
            "(예시) 가상산업 대구1호(주)에서 생산직(제조 조립원)을 채용합니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "지게차 운전면허 및 캘리퍼스 사용 가능자를 우대합니다. "
            "월급 258만원(세전) 지급합니다. "
            "입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. "
            "수습기간 있음(세부 조건은 면접 시 안내). "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-008", region_group="metro", municipality="광주광역시",
        employment_type="정규직", company="(예시) 가상농산 광주1호",
        full_text=(
            "(예시) 가상농산 광주1호 생산라인 인원 모집입니다. "
            "완성차 부품 조립 업무를 담당합니다. "
            "관련 경험자를 우대합니다. "
            "급여는 회사 내규에 따라 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-009", region_group="metro", municipality="대전광역시",
        employment_type="정규직", company="(예시) 가상식품 대전1호(주)",
        full_text=(
            "(예시) 가상식품 대전1호(주)에서 생산직(제조 조립원)을 모집합니다. "
            "사출 성형기 운영 및 제품 포장 업무를 수행합니다. "
            "월급 255만원(세전) 지급합니다. "
            "체계적인 교육 시스템을 운영하고 있습니다. "
            "수습기간 3개월, 수습기간 동안 동일 급여 지급합니다. "
            "고용형태는 정규직입니다."
        ),
    ),
    dict(
        posting_id="MET-010", region_group="metro", municipality="경기 화성시",
        employment_type="정규직", company="(예시) 가상제조 화성1호(주)",
        full_text=(
            "(예시) 가상제조 화성1호(주)에서 생산직(제조 조립원)을 채용합니다. "
            "완성차 부품 조립 및 품질 검사 업무를 담당합니다. "
            "지게차 운전면허 및 PLC 설비 조작 경험자를 우대합니다. "
            "월급 272만원(세전) 지급합니다. "
            "입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. "
            "수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. "
            "채용형태는 면접 후 결정합니다."
        ),
    ),
    # --- Intentionally unmatched records (Phase 3 requires demonstrating this path) ---
    dict(
        posting_id="JB-011", region_group="jeonbuk", municipality="고창군",
        employment_type="계약직", company="(예시) 가상농산가공 고창1호",
        full_text=(
            "(예시) 가상농산가공 고창1호에서 농산물 가공 생산직(계약직)을 "
            "모집합니다. 원료 선별 및 포장 라인 보조 업무를 수행합니다. "
            "월급 210만원(세전) 지급합니다. 고용형태는 계약직(6개월)입니다."
        ),
    ),
    dict(
        posting_id="MET-011", region_group="metro", municipality="경기 수원시",
        employment_type="계약직", company="(예시) 가상전자 수원1호",
        full_text=(
            "(예시) 가상전자 수원1호에서 생산직(제조 조립원, 계약직)을 "
            "모집합니다. 완성차 부품 조립 보조 업무를 수행합니다. "
            "월급 225만원(세전) 지급합니다. 고용형태는 계약직(1년)입니다."
        ),
    ),
]

MATCHED_PAIR_IDS = [f"P{i:02d}" for i in range(1, 11)]


def build_postings() -> list[dict]:
    records = []
    for i, p in enumerate(POSTINGS):
        pid = p["posting_id"]
        is_unmatched = pid in ("JB-011", "MET-011")
        matched_pair_id = None
        match_criteria = None
        unmatched = False
        unmatched_reason = None

        if not is_unmatched:
            # Pairs by index within their region-ordered halves: JB-00k <-> MET-00k
            idx = int(pid.split("-")[1]) - 1
            matched_pair_id = MATCHED_PAIR_IDS[idx]
            match_criteria = (
                f"source={SOURCE_NAME}; occupation={OCCUPATION}; "
                f"employment_type={p['employment_type']}; fixture_build_date={FIXTURE_BUILD_DATE}"
            )
        else:
            unmatched = True
            if pid == "JB-011":
                unmatched_reason = (
                    "no candidate found under recorded query "
                    "(occupation=농산물 가공 생산직, employment_type=계약직 "
                    "combination has no metropolitan fixture in this build)"
                )
            else:
                unmatched_reason = (
                    "no candidate found under recorded query "
                    "(employment_type=계약직 has no Jeonbuk 생산직 fixture "
                    "in this build; the Jeonbuk contract-type pool used a "
                    "different sub-occupation, see JB-011)"
                )

        records.append(
            {
                "posting_id": pid,
                "region_group": p["region_group"],
                "municipality": p["municipality"],
                "occupation": OCCUPATION,
                "employment_type": p["employment_type"],
                "collection_date": None,
                "fixture_build_date": FIXTURE_BUILD_DATE,
                "source_name": SOURCE_NAME,
                "source_id_url": None,
                "company_name": p["company"],
                "full_text": p["full_text"],
                "redistributable": True,
                "matched_pair_id": matched_pair_id,
                "match_criteria": match_criteria,
                "unmatched": unmatched,
                "unmatched_reason": unmatched_reason,
            }
        )
    return records


def build_matched_pairs(postings: list[dict]) -> list[dict]:
    by_pair: dict[str, list[dict]] = {}
    for rec in postings:
        if rec["matched_pair_id"]:
            by_pair.setdefault(rec["matched_pair_id"], []).append(rec)

    pairs = []
    for pair_id in MATCHED_PAIR_IDS:
        members = by_pair.get(pair_id, [])
        jeonbuk = next((m for m in members if m["region_group"] == "jeonbuk"), None)
        metro = next((m for m in members if m["region_group"] == "metro"), None)
        pairs.append(
            {
                "matched_pair_id": pair_id,
                "jeonbuk_posting_id": jeonbuk["posting_id"] if jeonbuk else None,
                "metro_posting_id": metro["posting_id"] if metro else None,
                "occupation": OCCUPATION,
                "employment_type": jeonbuk["employment_type"] if jeonbuk else None,
                "match_criteria": jeonbuk["match_criteria"] if jeonbuk else None,
            }
        )
    return pairs


def main() -> None:
    postings = build_postings()
    pairs = build_matched_pairs(postings)

    POSTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with POSTINGS_PATH.open("w", encoding="utf-8") as f:
        for rec in postings:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with PAIRS_PATH.open("w", encoding="utf-8") as f:
        for rec in pairs:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(postings)} postings to {POSTINGS_PATH}")
    print(f"Wrote {len(pairs)} matched pairs to {PAIRS_PATH}")


if __name__ == "__main__":
    main()
