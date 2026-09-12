from __future__ import annotations

import json
from pathlib import Path

from app.datasets.loader import clear_dataset_cache
from app.models.finance import FinancialComparisonRequest
from app.models.posting import PostingInput
from app.providers.factory import get_provider
from app.services.audit_pipeline import analyze_posting
from app.services.finance import compare_financials
from app.services.matching import find_matches

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_three_anchor_offline_demo_flow(monkeypatch):
    anchors = json.loads((REPO_ROOT / "demo" / "anchors.json").read_text(encoding="utf-8"))["anchors"]
    assert len(anchors) == 3
    by_id = {anchor["posting_id"]: anchor for anchor in anchors}
    assert set(by_id) == {"MET-001", "JB-001", "JB-003"}

    metro = analyze_posting(
        PostingInput(
            posting_id="MET-001",
            source_text=by_id["MET-001"]["source_text"],
            expected_occupation="생산직(제조 조립원)",
        ),
        get_provider(),
    )
    assert metro.fields["salary"].status == "confirmed"

    monkeypatch.setenv(
        "JEONBUK_DATASET_PATH", str(REPO_ROOT / "data" / "postings" / "postings.jsonl")
    )
    clear_dataset_cache()
    candidates = find_matches("생산직(제조 조립원)", "정규직")
    assert any(candidate.posting_id == "JB-001" for candidate in candidates)

    gap_audit = analyze_posting(
        PostingInput(
            posting_id="JB-003",
            source_text=by_id["JB-003"]["source_text"],
            expected_occupation="생산직(제조 조립원)",
        ),
        get_provider(),
    )
    assert len(gap_audit.fields) == 6
    assert sum(field.status in {"vague", "absent"} for field in gap_audit.fields.values()) >= 3
    assert len(gap_audit.verification_actions) >= 3
    for field in gap_audit.fields.values():
        if field.evidence is not None:
            span = field.evidence
            assert by_id["JB-003"]["source_text"][span.start : span.end] == span.text

    comparison = compare_financials(
        FinancialComparisonRequest.model_validate(
            {
                "metropolitan": {
                    "label": "수도권 시나리오",
                    "monthly_income_after_tax": 2_400_000,
                    "monthly_housing_cost": 900_000,
                    "monthly_other_living_cost": 1_000_000,
                    "deposit": 10_000_000,
                },
                "jeonbuk": {
                    "label": "전북 시나리오",
                    "monthly_income_after_tax": 2_150_000,
                    "monthly_housing_cost": 450_000,
                    "monthly_other_living_cost": 900_000,
                    "deposit": 5_000_000,
                },
            }
        )
    )
    assert comparison.options["metropolitan"].one_year_liquid_cash == 6_000_000
    assert comparison.options["jeonbuk"].three_year_liquid_cash == 28_800_000
    assert comparison.crossover.varied_variable == "monthly_housing_cost"
