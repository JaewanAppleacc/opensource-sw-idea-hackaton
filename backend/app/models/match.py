from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import StrictModel


class MatchCandidate(StrictModel):
    posting_id: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    region: str
    municipality: Optional[str] = None
    occupation: str
    employment_type: str
    company_name: Optional[str] = None
    source_text: Optional[str] = Field(
        default=None,
        description="Posting text when the configured source permits runtime display; may be null.",
    )
    is_synthetic: bool = False
    matching_fields: List[str]
    mismatch_fields: List[str]
    description: str = Field(
        ...,
        description="Plain statement that this candidate comes from a finite curated dataset, not a claim of best fit.",
    )


class MatchRequest(StrictModel):
    occupation: str = Field(..., min_length=1)
    employment_type: Optional[str] = None
    posting_id: Optional[str] = None


class MatchResponse(StrictModel):
    query_occupation: str
    query_employment_type: Optional[str] = None
    candidates: List[MatchCandidate]
    dataset_description: str
