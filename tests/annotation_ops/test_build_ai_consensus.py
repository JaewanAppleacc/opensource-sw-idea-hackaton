"""Synthetic-fixture-only tests for build_ai_consensus.py. Never touches
data/private/ai_reviews/** real content.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "annotation_ops"))

import pytest
from build_ai_consensus import build_consensus_rows


def suggestion(posting_id, field, agent, status, evidence_text=None, offsets=None):
    return {
        "posting_id": posting_id,
        "field": field,
        "reviewer_id": agent,
        "reviewer_type": "ai",
        "suggested_status": status,
        "evidence_text": evidence_text,
        "offsets": offsets,
        "reason_code": "x",
        "uncertainty_note": None,
        "rubric_version": "1.0.0-draft",
        "ai_suggested": True,
        "synthetic_test_fixture": True,
    }


def test_agreed_cell_is_ai_consensus_with_no_adjudicator_note():
    a = [suggestion("TEST-01", "salary", "AI-A", "confirmed", "월급 250만원", [0, 6])]
    b = [suggestion("TEST-01", "salary", "AI-B", "confirmed", "월급 250만원", [0, 6])]
    rows = build_consensus_rows(a, b)
    assert len(rows) == 1
    row = rows[0]
    assert row["initial_agreement"] is True
    assert row["resolution_source"] == "ai_consensus"
    assert row["final_status"] == "confirmed"
    assert row["adjudicator_note"] is None
    assert row["is_gold"] is False


def test_disagreed_cell_without_recorded_adjudication_raises():
    a = [suggestion("TEST-99", "duties", "AI-A", "vague")]
    b = [suggestion("TEST-99", "duties", "AI-B", "confirmed", "조립 업무", [0, 4])]
    with pytest.raises(ValueError, match="no human adjudication"):
        build_consensus_rows(a, b)


def test_mismatched_cell_sets_between_agents_raises():
    a = [suggestion("TEST-01", "salary", "AI-A", "confirmed", "x", [0, 1])]
    b = [suggestion("TEST-02", "salary", "AI-B", "confirmed", "x", [0, 1])]
    with pytest.raises(ValueError, match="same"):
        build_consensus_rows(a, b)


def test_never_sets_is_gold_true_or_human_boundary_review():
    a = [suggestion("TEST-01", "salary", "AI-A", "absent")]
    b = [suggestion("TEST-01", "salary", "AI-B", "absent")]
    rows = build_consensus_rows(a, b)
    assert rows[0]["is_gold"] is False
    assert "human_boundary_review_completed" not in rows[0]
