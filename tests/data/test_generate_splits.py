from generate_splits import build_units, choose_holdout_units, rare_status_counts


def make_postings():
    postings = []
    for i in range(1, 6):
        pair_id = f"P{i:02d}"
        postings.append(
            {"posting_id": f"JB-{i:03d}", "region_group": "jeonbuk", "matched_pair_id": pair_id, "unmatched": False}
        )
        postings.append(
            {"posting_id": f"MET-{i:03d}", "region_group": "metro", "matched_pair_id": pair_id, "unmatched": False}
        )
    postings.append({"posting_id": "JB-999", "region_group": "jeonbuk", "matched_pair_id": None, "unmatched": True})
    return postings


def test_build_units_groups_pairs_and_keeps_unmatched_singleton():
    postings = make_postings()
    units = build_units(postings)
    pair_units = [u for u in units if len(u["posting_ids"]) == 2]
    singleton_units = [u for u in units if len(u["posting_ids"]) == 1]
    assert len(pair_units) == 5
    assert len(singleton_units) == 1
    assert singleton_units[0]["posting_ids"] == ["JB-999"]


def test_choose_holdout_units_targets_roughly_20_percent():
    postings = make_postings()
    units = build_units(postings)
    total = len(postings)  # 11
    holdout = choose_holdout_units(units, rare_counts={}, total_postings=total)
    holdout_size = sum(len(u["posting_ids"]) for u in holdout)
    # target is 0.2 * 11 = 2.2. With all-zero rarity, units are ordered by
    # unit_id ("JB-999" sorts before "P01".."P05"), so the closest prefix is
    # [JB-999 (1), P01 (2)] = 3, which is closer to 2.2 than stopping at 1.
    assert holdout_size == 3


def test_rare_status_counts_counts_only_absent():
    adjudicated = [
        {"posting_id": "JB-001", "field": "salary", "adjudicated_status": "absent"},
        {"posting_id": "JB-001", "field": "duties", "adjudicated_status": "confirmed"},
        {"posting_id": "JB-002", "field": "salary", "adjudicated_status": "absent"},
    ]
    counts = rare_status_counts(adjudicated)
    assert counts == {"JB-001": 1, "JB-002": 1}


def test_choose_holdout_units_prioritizes_rare_status_units():
    postings = make_postings()
    units = build_units(postings)
    # Make P05's pair (JB-005/MET-005) carry all the rare "absent" statuses.
    rare_counts = {"JB-005": 3, "MET-005": 2}
    holdout = choose_holdout_units(units, rare_counts, total_postings=len(postings))
    holdout_ids = {pid for u in holdout for pid in u["posting_ids"]}
    assert "JB-005" in holdout_ids and "MET-005" in holdout_ids
