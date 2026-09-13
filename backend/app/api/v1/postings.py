from __future__ import annotations

from fastapi import APIRouter

from ...models.listing import AnalyzeByIdRequest, HomeRegionMatchRequest, PostingListResponse
from ...models.match import MatchRequest, MatchResponse
from ...models.posting import PostingAnalysis, PostingInput
from ...providers.factory import get_free_text_provider, get_provider
from ...services.audit_pipeline import analyze_posting
from ...services.hybrid_audit_pipeline import analyze_posting_hybrid
from ...services.matching import DATASET_DESCRIPTION, find_matches
from ...services.real_postings import (
    find_home_region_matches,
    list_capital_area_postings,
    resolve_private_text,
)
from ...services.work24_structured_loader import load_work24_structured_posting

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


@router.get("/postings/home-region-listing", response_model=PostingListResponse)
def home_region_listing() -> PostingListResponse:
    """Public metadata for every real capital-area posting in the curated
    batch (never full_text). See app.services.real_postings module docstring.
    """
    return list_capital_area_postings()


@router.post("/postings/home-region-matches", response_model=MatchResponse)
def home_region_matches(request: HomeRegionMatchRequest) -> MatchResponse:
    """Real curated-pair candidates for one capital-area posting, scoped to
    the server-configured home region only -- the request has no field a
    client could use to ask for a different region.
    """
    return find_home_region_matches(request.metro_posting_id)


@router.post("/postings/analyze-by-id", response_model=PostingAnalysis)
def analyze_by_id(request: AnalyzeByIdRequest) -> PostingAnalysis:
    """Resolves posting_id -> private full text server-side (never returned
    to the client raw), then picks one of two pipelines:

      - A `Work24StructuredPosting` fixture exists for this posting_id ->
        the hybrid pipeline (`analyze_posting_hybrid`): salary/employment_type
        come deterministically from that record, the remaining four fields
        from an sLLM's free-text extraction.
      - No such record exists (every posting outside the current tiny
        research-persona demo set) -> the exact same
        `analyze_posting()` six-field pipeline as /postings/analyze,
        completely unchanged from before this feature existed.

    Raises PrivateDataUnavailableError (503) if this machine has no private
    copy for posting_id right now, in either case.
    """
    full_text, private_occupation = resolve_private_text(request.posting_id)
    posting_input = PostingInput(
        posting_id=request.posting_id,
        source_text=full_text,
        expected_occupation=request.expected_occupation or private_occupation,
    )

    structured = load_work24_structured_posting(request.posting_id)
    if structured is not None:
        return analyze_posting_hybrid(posting_input, structured, get_free_text_provider())

    return analyze_posting(posting_input, get_provider())
