"""Real capital-area listing + home-region matching + private-text
resolution for the inline Jeonbuk comparison agent.

Kept entirely separate from `app.datasets.loader` / `app.services.matching`
(the synthetic-fixture-oriented, occupation-fuzzy-match path used by the
existing `/postings/match` endpoint) so nothing about that already-tested
behavior changes.

`find_home_region_matches` returns up to three home-region comparison
candidates for one capital-area posting: postings with the same normalized
occupation and employment_type as the query, from the current real 10:10
batch. The order is a deterministic display order, not a similarity
ranking -- the acquisition track's pre-linked pair
(`data/intake/real_matched_pairs.jsonl`) comes first when it exists and
still qualifies, then any other same-group home-region postings follow in
the batch's collection order. Nothing here claims a returned candidate is
the most similar or best-fit local alternative, and duties/skills are never
used to choose or order candidates (see `REAL_DATASET_DESCRIPTION` below).

Every function here is read-only over `data/intake/**` (public, tracked)
and `data/private/intake_raw/**` (gitignored, real posting text). Nothing
here writes to either location.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..errors import NoMatchFoundError, PrivateDataUnavailableError
from ..models.listing import PostingListItem, PostingListResponse
from ..models.match import MatchCandidate, MatchResponse
from .matching import DATASET_DESCRIPTION as SYNTHETIC_DATASET_DESCRIPTION  # noqa: F401  (kept distinct, not reused)

_REPO_ROOT = Path(__file__).resolve().parents[3]

MAX_HOME_REGION_CANDIDATES = 3

REAL_DATASET_DESCRIPTION = (
    "These comparison postings come from a real 10:10 MVP dataset (see REAL_DATA_ACQUISITION_HANDOFF.md). "
    "The first candidate is the pre-linked record, followed by other home-region postings with the same "
    "normalized occupation and employment type in deterministic collection order. The order is not a "
    "similarity ranking, and the candidates are not claimed to be the best or only local alternatives, nor "
    "that the underlying occupation sample represents the whole regional labor market."
)


def home_region() -> str:
    from ..datasets.loader import home_region as _home_region

    return _home_region()


def _real_postings_path() -> Path:
    override = os.environ.get("REAL_POSTINGS_PATH")
    return Path(override) if override else _REPO_ROOT / "data" / "intake" / "real_postings.jsonl"


def _real_matched_pairs_path() -> Path:
    override = os.environ.get("REAL_MATCHED_PAIRS_PATH")
    return Path(override) if override else _REPO_ROOT / "data" / "intake" / "real_matched_pairs.jsonl"


def _private_intake_raw_dir() -> Path:
    override = os.environ.get("PRIVATE_INTAKE_RAW_DIR")
    return Path(override) if override else _REPO_ROOT / "data" / "private" / "intake_raw"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@lru_cache(maxsize=8)
def _load_real_postings_by_id(path_str: str) -> dict[str, dict]:
    return {rec["posting_id"]: rec for rec in _read_jsonl(Path(path_str)) if rec.get("posting_id")}


@lru_cache(maxsize=8)
def _load_real_pairs(path_str: str) -> list[dict]:
    return _read_jsonl(Path(path_str))


def clear_real_postings_cache() -> None:
    """Test-only escape hatch so *_PATH env var overrides take effect mid-suite."""
    _load_real_postings_by_id.cache_clear()
    _load_real_pairs.cache_clear()


def private_text_available(posting_id: str) -> bool:
    """Computed live from the filesystem -- never trusts the public
    dataset's static `full_text_available_privately` claim, which only
    means "a private copy existed on *some* machine at intake time".
    """
    return (_private_intake_raw_dir() / f"{posting_id}.json").is_file()


def _to_list_item(record: dict) -> PostingListItem:
    return PostingListItem(
        posting_id=record["posting_id"],
        company_name=record.get("company_name"),
        region=record.get("region_group", "metro"),
        municipality=record.get("municipality"),
        occupation=record["occupation"],
        employment_type=record["employment_type"],
        source_url=record.get("source_id_url"),
        collection_date=record.get("collection_date"),
        is_synthetic=bool(record.get("synthetic_test_fixture")),
        private_text_available=private_text_available(record["posting_id"]),
    )


def list_capital_area_postings() -> PostingListResponse:
    """Every real, capital-area ('metro') posting from the curated batch,
    public metadata only -- never full_text (redistributable: false for
    every record in this batch; see REAL_DATA_ACQUISITION_HANDOFF.md).
    """
    postings_by_id = _load_real_postings_by_id(str(_real_postings_path()))
    items = [_to_list_item(r) for r in postings_by_id.values() if r.get("region_group") == "metro"]
    items.sort(key=lambda item: item.posting_id)
    return PostingListResponse(
        home_region=home_region(),
        postings=items,
        dataset_description=REAL_DATASET_DESCRIPTION,
    )


def _is_eligible_home_candidate(record: dict, *, occupation: str, employment_type: str) -> bool:
    """Every condition a home-region comparison candidate must satisfy.

    Applied uniformly to the pre-linked pair and to every group-fallback
    candidate alike -- there is no separate, looser check for the pre-linked
    one. Never a similarity/relevance judgement: occupation and
    employment_type are compared as the normalized strings already present
    in the intake data, not re-derived or fuzzy-matched.
    """
    return (
        record.get("region_group", "").strip().lower() == home_region()
        and record.get("occupation") == occupation
        and record.get("employment_type") == employment_type
        and not record.get("synthetic_test_fixture", False)
    )


def _to_match_candidate(record: dict) -> MatchCandidate:
    # Both occupation and employment_type are hard filter conditions (see
    # _is_eligible_home_candidate), so every returned candidate matches on
    # both -- there is no such thing as a "mismatch_fields" entry here.
    return MatchCandidate(
        posting_id=record["posting_id"],
        source_id=record.get("source_name"),
        source_url=record.get("source_id_url"),
        region=record.get("region_group", home_region()),
        municipality=record.get("municipality"),
        occupation=record["occupation"],
        employment_type=record["employment_type"],
        company_name=record.get("company_name"),
        source_text=None,  # never leak real text through the match/listing layer
        is_synthetic=bool(record.get("synthetic_test_fixture")),
        matching_fields=["occupation", "employment_type"],
        mismatch_fields=[],
        description=REAL_DATASET_DESCRIPTION,
    )


def find_home_region_matches(metro_posting_id: str) -> MatchResponse:
    """Up to MAX_HOME_REGION_CANDIDATES home-region comparison candidates
    for one capital-area posting, scoped to the server's configured home
    region.

    Candidate order (deterministic, never a similarity ranking):
      1. The acquisition track's pre-linked pair
         (data/intake/real_matched_pairs.jsonl), if it exists and still
         satisfies every eligibility condition.
      2. Any other home-region postings with the same normalized
         occupation + employment_type, in the intake file's collection
         order, filling up to MAX_HOME_REGION_CANDIDATES and skipping
         anything already added.

    A metro posting outside the current batch, or one with zero eligible
    home-region postings in its occupation/employment_type group, raises
    NoMatchFoundError -- candidates are never padded with a posting from a
    different group, region, or the synthetic fixture path.
    """
    postings_by_id = _load_real_postings_by_id(str(_real_postings_path()))
    metro_record = postings_by_id.get(metro_posting_id)
    if metro_record is None or metro_record.get("region_group") != "metro":
        raise NoMatchFoundError(
            f"no capital-area posting found for posting_id={metro_posting_id!r}",
            details={"posting_id": metro_posting_id},
        )

    occupation = metro_record["occupation"]
    employment_type = metro_record["employment_type"]

    ordered_ids: list[str] = []

    # Step 1: the pre-linked pair, if any, comes first -- but only if it
    # still passes every eligibility condition (region, group, synthetic
    # flag). A pair that fails one of these is simply skipped here, not
    # substituted with anything; step 2 never re-adds it either, since it
    # applies the exact same check.
    pairs = _load_real_pairs(str(_real_matched_pairs_path()))
    for pair in pairs:
        if pair.get("metro_posting_id") != metro_posting_id:
            continue
        home_id = pair.get("jeonbuk_posting_id")
        home_record = postings_by_id.get(home_id) if home_id else None
        if home_record is not None and _is_eligible_home_candidate(
            home_record, occupation=occupation, employment_type=employment_type
        ):
            ordered_ids.append(home_record["posting_id"])

    # Step 2: remaining same-group home-region postings, in the order they
    # appear in the intake file -- not sorted by any notion of fit.
    for record in postings_by_id.values():
        if len(ordered_ids) >= MAX_HOME_REGION_CANDIDATES:
            break
        posting_id = record.get("posting_id")
        if posting_id in ordered_ids:
            continue
        if _is_eligible_home_candidate(record, occupation=occupation, employment_type=employment_type):
            ordered_ids.append(posting_id)

    if not ordered_ids:
        raise NoMatchFoundError(
            f"no {home_region()} posting matched to posting_id={metro_posting_id!r}",
            details={"posting_id": metro_posting_id, "home_region": home_region()},
        )

    candidates = [_to_match_candidate(postings_by_id[pid]) for pid in ordered_ids[:MAX_HOME_REGION_CANDIDATES]]

    return MatchResponse(
        query_occupation=occupation,
        query_employment_type=employment_type,
        candidates=candidates,
        dataset_description=REAL_DATASET_DESCRIPTION,
    )


def resolve_private_text(posting_id: str) -> tuple[str, Optional[str]]:
    """Returns (full_text, occupation). Raises PrivateDataUnavailableError
    (never a bare FileNotFoundError, never an invented placeholder text) if
    this machine has no private copy for posting_id right now.
    """
    path = _private_intake_raw_dir() / f"{posting_id}.json"
    if not path.is_file():
        raise PrivateDataUnavailableError(
            f"no private full text available for posting_id={posting_id!r} on this machine",
            details={"posting_id": posting_id},
        )
    with path.open(encoding="utf-8") as f:
        record = json.load(f)
    full_text = record.get("full_text")
    if not full_text:
        raise PrivateDataUnavailableError(
            f"private record for posting_id={posting_id!r} has empty full_text",
            details={"posting_id": posting_id},
        )
    return full_text, record.get("occupation")
