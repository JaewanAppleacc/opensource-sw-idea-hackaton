from pair_postings import UNMATCHED_REASON, pair_postings


def make_posting(posting_id, region_group, occupation="생산직(제조 조립원)", employment_type="정규직"):
    return {
        "posting_id": posting_id,
        "region_group": region_group,
        "occupation": occupation,
        "employment_type": employment_type,
        "source_name": "고용24",
        "matched_pair_id": None,
        "match_criteria": None,
        "unmatched": None,
        "unmatched_reason": None,
    }


def test_equal_counts_pair_everything():
    postings = [
        make_posting("JB-01", "jeonbuk"),
        make_posting("JB-02", "jeonbuk"),
        make_posting("MET-01", "metro"),
        make_posting("MET-02", "metro"),
    ]
    updated, pairs = pair_postings(postings)
    assert len(pairs) == 2
    assert all(p["unmatched"] is False for p in updated)
    assert all(p["unmatched_reason"] is None for p in updated)
    assert all(p["matched_pair_id"] is not None for p in updated)


def test_leftover_jeonbuk_marked_unmatched_with_factual_reason():
    postings = [
        make_posting("JB-01", "jeonbuk"),
        make_posting("JB-02", "jeonbuk"),
        make_posting("MET-01", "metro"),
    ]
    updated, pairs = pair_postings(postings)
    assert len(pairs) == 1
    by_id = {p["posting_id"]: p for p in updated}
    leftover_ids = [pid for pid, p in by_id.items() if p["unmatched"]]
    assert len(leftover_ids) == 1
    leftover = by_id[leftover_ids[0]]
    assert leftover["unmatched_reason"] == UNMATCHED_REASON
    assert "부족" not in leftover["unmatched_reason"]  # never an interpretive scarcity claim


def test_different_occupation_or_employment_type_never_pairs_across_groups():
    postings = [
        make_posting("JB-01", "jeonbuk", employment_type="정규직"),
        make_posting("MET-01", "metro", employment_type="계약직"),
    ]
    updated, pairs = pair_postings(postings)
    assert len(pairs) == 0
    assert all(p["unmatched"] for p in updated)


def test_pair_ids_are_stable_and_unique():
    postings = [
        make_posting("JB-01", "jeonbuk"),
        make_posting("MET-01", "metro"),
        make_posting("JB-02", "jeonbuk", occupation="요양보호사"),
        make_posting("MET-02", "metro", occupation="요양보호사"),
    ]
    _, pairs = pair_postings(postings)
    pair_ids = [p["matched_pair_id"] for p in pairs]
    assert len(pair_ids) == len(set(pair_ids)) == 2
