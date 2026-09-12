"""Public capital-area posting listing (inline-jeonbuk-agent feature).

Deliberately excludes `full_text` entirely -- unlike `MatchCandidate`,
which carries a nullable `source_text` for datasets that do permit runtime
display (the synthetic fixture), every real posting in this batch has
`redistributable: false`, so this model has no field for it at all. Only
already-public metadata (company name, region, occupation, employment
type, source URL, collection date) is exposed.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import StrictModel


class PostingListItem(StrictModel):
    posting_id: str
    company_name: Optional[str] = None
    region: str
    municipality: Optional[str] = None
    occupation: str
    employment_type: str
    source_url: Optional[str] = None
    collection_date: Optional[str] = None
    is_synthetic: bool = False
    private_text_available: bool = Field(
        ...,
        description=(
            "Computed at request time from whether data/private/intake_raw/<id>.json "
            "actually exists on this machine right now -- not a static claim carried "
            "over from the public dataset row."
        ),
    )


class PostingListResponse(StrictModel):
    home_region: str = Field(..., description="The server-configured home region this deployment is scoped to.")
    postings: List[PostingListItem]
    dataset_description: str


class HomeRegionMatchRequest(StrictModel):
    """Client supplies only which capital-area posting it's looking at --
    never a region. The home region is always the server-configured value
    (see app.datasets.loader.home_region()); there is no field here a
    client could set to request a different one.
    """

    metro_posting_id: str = Field(..., min_length=1)


class AnalyzeByIdRequest(StrictModel):
    posting_id: str = Field(..., min_length=1)
    expected_occupation: Optional[str] = None
