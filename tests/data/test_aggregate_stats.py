from aggregate_stats import (
    matched_pair_descriptive_differences,
    status_proportions_by_region_field,
    unmatched_summary,
)


def test_status_proportions_by_region_field_basic():
    postings_by_id = {
        "JB-001": {"region_group": "jeonbuk"},
        "JB-002": {"region_group": "jeonbuk"},
        "MET-001": {"region_group": "metro"},
    }
    adjudicated = [
        {"posting_id": "JB-001", "field": "salary", "adjudicated_status": "confirmed"},
        {"posting_id": "JB-002", "field": "salary", "adjudicated_status": "absent"},
        {"posting_id": "MET-001", "field": "salary", "adjudicated_status": "confirmed"},
    ]
    result = status_proportions_by_region_field(postings_by_id, adjudicated)
    assert result["jeonbuk"]["salary"]["confirmed"] == 0.5
    assert result["jeonbuk"]["salary"]["absent"] == 0.5
    assert result["jeonbuk"]["salary"]["_n"] == 2
    assert result["metro"]["salary"]["confirmed"] == 1.0


def test_status_proportions_ignores_undecided_cells():
    postings_by_id = {"JB-001": {"region_group": "jeonbuk"}}
    adjudicated = [{"posting_id": "JB-001", "field": "salary", "adjudicated_status": None}]
    result = status_proportions_by_region_field(postings_by_id, adjudicated)
    assert result == {}


def test_matched_pair_descriptive_differences_counts_differing_pairs():
    pairs = [{"matched_pair_id": "P01", "jeonbuk_posting_id": "JB-001", "metro_posting_id": "MET-001"}]
    adjudicated_by_cell = {
        ("JB-001", "salary"): "confirmed",
        ("MET-001", "salary"): "vague",
        ("JB-001", "duties"): "confirmed",
        ("MET-001", "duties"): "confirmed",
    }
    result = matched_pair_descriptive_differences(pairs, adjudicated_by_cell)
    assert result["per_field_status_differs_rate"]["salary"] == 1.0
    assert result["per_field_status_differs_rate"]["duties"] == 0.0


def test_matched_pair_descriptive_differences_skips_undecided_fields():
    pairs = [{"matched_pair_id": "P01", "jeonbuk_posting_id": "JB-001", "metro_posting_id": "MET-001"}]
    result = matched_pair_descriptive_differences(pairs, {})
    assert result["per_field_status_differs_rate"]["salary"] is None
    assert result["per_field_pairs_compared"]["salary"] == 0


def test_unmatched_summary_reports_reasons():
    postings = [
        {"posting_id": "JB-011", "region_group": "jeonbuk", "unmatched": True, "unmatched_reason": "no candidate found under recorded query"},
        {"posting_id": "JB-001", "region_group": "jeonbuk", "unmatched": False, "unmatched_reason": None},
    ]
    result = unmatched_summary(postings)
    assert result["unmatched_count"] == 1
    assert result["unmatched_records"][0]["posting_id"] == "JB-011"
    assert "observations only" in result["interpretation_note"]
