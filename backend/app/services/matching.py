"""Curated Jeonbuk posting matching.

No vector database, no live scraping: this reads the finite local dataset
via app.datasets.loader and matches on explicit occupation (required) and
employment type (optional, used to rank and to report mismatches). Never
claims a returned candidate is the best posting available in Jeonbuk.
"""
from __future__ import annotations

from typing import List, Optional

from ..datasets.loader import JeonbukPostingRecord, load_jeonbuk_dataset
from ..errors import NoMatchFoundError
from ..models.match import MatchCandidate

DATASET_DESCRIPTION = (
    "This candidate is drawn from a small, finite curated Jeonbuk posting dataset for this MVP demo. "
    "It is not a claim that this is the best or only matching posting available in Jeonbuk."
)


def find_matches(occupation: str, employment_type: Optional[str] = None, limit: int = 3) -> List[MatchCandidate]:
    dataset = load_jeonbuk_dataset()
    occupation_norm = occupation.strip().lower()

    scored: list[tuple[int, JeonbukPostingRecord]] = []
    for record in dataset:
        if record.occupation.strip().lower() != occupation_norm:
            continue
        score = 1  # occupation match
        if employment_type and record.employment_type.strip().lower() == employment_type.strip().lower():
            score += 1
        scored.append((score, record))

    if not scored:
        raise NoMatchFoundError(
            f"no curated Jeonbuk posting found for occupation={occupation!r}",
            details={"occupation": occupation, "employment_type": employment_type},
        )

    scored.sort(key=lambda pair: (-pair[0], pair[1].posting_id))
    top = scored[:limit]

    candidates: List[MatchCandidate] = []
    for _score, record in top:
        matching_fields = ["occupation"]
        mismatch_fields: List[str] = []
        if employment_type:
            if record.employment_type.strip().lower() == employment_type.strip().lower():
                matching_fields.append("employment_type")
            else:
                mismatch_fields.append("employment_type")

        candidates.append(
            MatchCandidate(
                posting_id=record.posting_id,
                source_id=record.source_id,
                source_url=record.source_url,
                region=record.region,
                municipality=record.municipality,
                occupation=record.occupation,
                employment_type=record.employment_type,
                matching_fields=matching_fields,
                mismatch_fields=mismatch_fields,
                description=DATASET_DESCRIPTION,
            )
        )
    return candidates
