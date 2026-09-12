from __future__ import annotations

from fastapi import APIRouter

from ...models.match import MatchRequest, MatchResponse
from ...models.posting import PostingAnalysis, PostingInput
from ...providers.factory import get_provider
from ...services.audit_pipeline import analyze_posting
from ...services.matching import DATASET_DESCRIPTION, find_matches

router = APIRouter()


@router.post("/postings/analyze", response_model=PostingAnalysis)
def analyze(posting: PostingInput) -> PostingAnalysis:
    provider = get_provider()
    return analyze_posting(posting, provider)


@router.post("/postings/match", response_model=MatchResponse)
def match(request: MatchRequest) -> MatchResponse:
    candidates = find_matches(request.occupation, request.employment_type)
    return MatchResponse(
        query_occupation=request.occupation,
        query_employment_type=request.employment_type,
        candidates=candidates,
        dataset_description=DATASET_DESCRIPTION,
    )
