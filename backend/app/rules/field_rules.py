"""Loader and evaluator for the deterministic per-field audit rules.

Rules live in field_rules.yaml (or a path supplied via FIELD_RULES_PATH) so
the data track's rubric can later replace them without touching pipeline
code. `evaluate_confirmed` never invents or rewrites evidence text -- it
only classifies evidence the provider already pointed at in the source.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_INTEGRATED_RULES_PATH = _REPO_ROOT / "data" / "rubric" / "runtime_rules.yaml"
_BACKEND_FALLBACK_RULES_PATH = Path(__file__).with_name("field_rules.yaml")
_DEFAULT_RULES_PATH = (
    _INTEGRATED_RULES_PATH if _INTEGRATED_RULES_PATH.exists() else _BACKEND_FALLBACK_RULES_PATH
)


def _rules_path() -> Path:
    override = os.environ.get("FIELD_RULES_PATH")
    return Path(override) if override else _DEFAULT_RULES_PATH


@dataclass(frozen=True)
class FieldRule:
    field: str
    anchors: List[str] = field(default_factory=list)
    vague_markers: List[str] = field(default_factory=list)
    relevance_keywords: List[str] = field(default_factory=list)
    confirmed_rule: str = "specific_keywords"
    min_length: int = 0
    specific_keywords: List[str] = field(default_factory=list)
    unit_keywords: List[str] = field(default_factory=list)
    amount_pattern: Optional[str] = None
    duration_pattern: Optional[str] = None
    condition_keywords: List[str] = field(default_factory=list)


@lru_cache(maxsize=8)
def _load_raw(path_str: str) -> dict:
    with open(path_str, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def rules_version() -> str:
    return _load_raw(str(_rules_path()))["version"]


def get_field_rules(field_name: str) -> FieldRule:
    raw = _load_raw(str(_rules_path()))["fields"][field_name]
    return FieldRule(field=field_name, **raw)


def clear_rules_cache() -> None:
    """Test-only escape hatch so FIELD_RULES_PATH overrides take effect mid-suite."""
    _load_raw.cache_clear()


def _contains_any(lowered_text: str, keywords: List[str]) -> bool:
    return any(keyword.lower() in lowered_text for keyword in keywords)


def evaluate_confirmed(field_name: str, evidence_text: str) -> Tuple[bool, bool, str]:
    """Classify a candidate evidence span against this field's deterministic rule.

    Returns (is_relevant, meets_confirmed_criteria, reason_code).
    is_relevant=False means the evidence has no bearing on this field at all
    (the pipeline downgrades such fields all the way to "absent").
    """
    rules = get_field_rules(field_name)
    lowered = evidence_text.lower()
    is_relevant = _contains_any(lowered, rules.relevance_keywords)

    if not is_relevant:
        return False, False, "no_relevant_keyword"

    if _contains_any(lowered, rules.vague_markers):
        return True, False, "vague_marker_matched"

    if rules.confirmed_rule == "amount_and_unit":
        ok = bool(rules.amount_pattern and re.search(rules.amount_pattern, evidence_text))
        return True, ok, "amount_with_unit" if ok else "missing_amount_or_unit"

    if rules.confirmed_rule == "duration_and_condition":
        has_duration = bool(rules.duration_pattern and re.search(rules.duration_pattern, evidence_text))
        has_condition = _contains_any(lowered, rules.condition_keywords)
        ok = has_duration and has_condition
        return True, ok, "duration_with_condition" if ok else "missing_duration_or_condition"

    if rules.confirmed_rule == "specific_keywords":
        has_specific = _contains_any(lowered, rules.specific_keywords)
        long_enough = len(evidence_text) >= rules.min_length
        ok = has_specific and long_enough
        return True, ok, "specific_detail_present" if ok else "too_generic"

    return True, False, "unknown_confirmed_rule"
