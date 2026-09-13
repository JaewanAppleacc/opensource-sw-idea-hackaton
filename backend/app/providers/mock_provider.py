"""Deterministic, offline extraction provider.

This is the default provider (LLM_PROVIDER=mock) so the whole demo,
including automated tests, runs with no API key and no network access. It
never invents text: it only locates lines in the source that contain a
field's anchor keywords and reports that exact line (with correct offsets)
as a "confirmed" candidate. The audit pipeline's deterministic field rules
then decide whether that candidate really is confirmed, gets downgraded to
vague, or -- if it turns out irrelevant -- to absent.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from ..models.common import FIELD_NAMES
from ..rules.field_rules import get_field_rules

_EMPLOYMENT_TYPE_KEYWORDS = [
    ("기간의 정함이 없는 근로계약", "정규직"),
    ("정규직", "정규직"),
    ("계약직", "계약직"),
    ("파견직", "파견직"),
    ("파견", "파견"),
    ("인턴", "인턴"),
]


def _split_segments(source_text: str) -> List[Tuple[str, int]]:
    """Split into (stripped_line, absolute_start_offset) pairs.

    Offsets are computed against the original text so
    `source_text[start:start+len(line)] == line` always holds.
    """
    segments: List[Tuple[str, int]] = []
    cursor = 0
    for raw_line in source_text.split("\n"):
        line_start = cursor
        cursor += len(raw_line) + 1  # account for the stripped "\n"
        stripped = raw_line.strip()
        if not stripped:
            continue
        offset_in_line = raw_line.find(stripped)
        segments.append((stripped, line_start + offset_in_line))
    return segments


def _find_best_segment(segments: List[Tuple[str, int]], anchors: List[str]) -> Optional[Tuple[str, int]]:
    for text, start in segments:
        lowered = text.lower()
        if any(anchor.lower() in lowered for anchor in anchors):
            return text, start
    return None


def _guess_employment_type(source_text: str) -> Optional[str]:
    for keyword, normalized_value in _EMPLOYMENT_TYPE_KEYWORDS:
        if keyword in source_text:
            return normalized_value
    return None


class MockExtractionProvider:
    name = "mock"

    def extract(self, source_text: str, expected_occupation: Optional[str] = None) -> dict:
        segments = _split_segments(source_text)
        fields = []
        for field_name in FIELD_NAMES:
            rules = get_field_rules(field_name)
            match = _find_best_segment(segments, rules.anchors)
            if match is None:
                fields.append({"field": field_name, "status": "absent"})
                continue
            text, start = match
            fields.append(
                {
                    "field": field_name,
                    "status": "confirmed",
                    "evidence_text": text,
                    "start": start,
                    "end": start + len(text),
                }
            )
        return {
            "occupation": expected_occupation,
            "employment_type": _guess_employment_type(source_text),
            "fields": fields,
        }
