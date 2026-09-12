"""Evidence-span validation harness.

Substring existence alone is not enough: evidence must sit at the exact
offsets the provider claimed, in the exact source text. This catches both
fabricated evidence (text that does not appear at all) and correct text
reported at the wrong offsets.
"""
from __future__ import annotations


class EvidenceMismatchError(Exception):
    pass


def validate_evidence_span(source_text: str, evidence_text: str, start: int, end: int) -> None:
    if start < 0 or end > len(source_text) or end <= start:
        raise EvidenceMismatchError(
            f"evidence offsets [{start}, {end}) are out of bounds for a text of length {len(source_text)}"
        )
    actual = source_text[start:end]
    if actual != evidence_text:
        raise EvidenceMismatchError(
            f"evidence text does not match source at the given offsets: expected {evidence_text!r}, got {actual!r}"
        )
