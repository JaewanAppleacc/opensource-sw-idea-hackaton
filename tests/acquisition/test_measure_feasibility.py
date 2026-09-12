from measure_feasibility import measure


def make_posting(posting_id, region_group, full_text="x" * 60, **overrides):
    base = {
        "posting_id": posting_id,
        "region_group": region_group,
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "collection_date": "2026-09-12",
        "full_text": full_text,
        "full_text_available_privately": True,
    }
    base.update(overrides)
    return base


def test_empty_postings_reports_insufficient_sample():
    report = measure([])
    assert report["overall_status"] == "INSUFFICIENT_SAMPLE"
    assert report["total_real_postings_ingested"] == 0
    assert report["candidates"] == []


def test_below_minimum_reports_insufficient_sample():
    postings = [make_posting("JB-01", "jeonbuk"), make_posting("MET-01", "metro")]
    report = measure(postings)
    assert report["overall_status"] == "INSUFFICIENT_SAMPLE"
    candidate = report["candidates"][0]
    assert candidate["jeonbuk_count"] == 1
    assert candidate["metro_count"] == 1
    assert candidate["meets_min_10_10"] is False
    assert candidate["human_boundary_review_completed"] is None


def test_meeting_10_10_flips_status_pending_human_review():
    postings = [make_posting(f"JB-{i:02d}", "jeonbuk") for i in range(10)] + [
        make_posting(f"MET-{i:02d}", "metro") for i in range(10)
    ]
    report = measure(postings)
    candidate = report["candidates"][0]
    assert candidate["meets_min_10_10"] is True
    assert candidate["meets_target_20_20"] is False
    assert report["overall_status"] == "MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW"


def test_short_full_text_not_counted_as_sufficient_when_not_private():
    postings = [
        make_posting("JB-01", "jeonbuk", full_text="짧음", full_text_available_privately=False),
    ]
    report = measure(postings)
    candidate = report["candidates"][0]
    assert candidate["full_text_sufficient_count"]["jeonbuk"] == 0


def test_redacted_public_text_still_counts_sufficient_via_private_flag():
    postings = [
        make_posting("JB-01", "jeonbuk", full_text=None, full_text_available_privately=True),
    ]
    report = measure(postings)
    candidate = report["candidates"][0]
    assert candidate["full_text_sufficient_count"]["jeonbuk"] == 1


def test_distinct_occupation_employment_groups_are_separate_candidates():
    postings = [
        make_posting("JB-01", "jeonbuk"),
        make_posting("JB-02", "jeonbuk", employment_type="계약직"),
    ]
    report = measure(postings)
    assert len(report["candidates"]) == 2
