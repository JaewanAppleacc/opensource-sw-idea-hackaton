"""Real capital-area listing + home-region matching + private-text
resolution for the inline Jeonbuk comparison agent.

Kept entirely separate from `app.datasets.loader` / `app.services.matching`
(the synthetic-fixture-oriented, occupation-fuzzy-match path used by the
existing `/postings/match` endpoint) so nothing about that already-tested
behavior changes.

**What this module's pairing actually is (be precise about this -- see
TASK "데모 매칭 표현 정직화").** `data/intake/real_matched_pairs.jsonl` is
produced once, offline, by `scripts/acquisition/pair_postings.py`: postings
are grouped by an exact match on their recorded `occupation` and
`employment_type` string values (no similarity scoring, no semantic
comparison, no normalization/canonicalization step -- just Python
dict-key equality on the two fields as collected), and within each group,
jeonbuk and metro records are paired 1:1 in the order they appear in
`data/intake/real_postings.jsonl` (i.e. collection order). This is a
deterministic, pre-computed lookup table, not an automatic "find the most
similar posting" engine -- there is no ranking, no scoring, and (in the
current single-occupation MVP batch) no more than one jeonbuk candidate is
ever returned for a given metro posting. It is not a claim that the
returned posting is the most similar, best, or only local alternative --
only that it shares the same recorded occupation and employment type and
was next in the same collection batch. See `REAL_DATASET_DESCRIPTION`
below for the exact wording surfaced to API responses, and
`docs/architecture/CURRENT_SYSTEM_FLOW.md` for how this differs from what
a real 고용24 integration (official `jobsCd`/`empTpCd`-based candidate
retrieval) would look like.

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

# Korean, not English: unlike other module-level docstrings/constants in
# this file, this specific string is rendered directly to end users on a
# Korean-language screen (JeonbukCandidateList.tsx, AiJobRecommendPage.tsx)
# -- see TASK "데모 매칭 표현 정직화" section 5 for the exact honesty
# requirements this text must satisfy.
REAL_DATASET_DESCRIPTION = (
    "이 데이터는 실제 수도권·전북 채용공고 10:10 표본에서 가져왔습니다. 수집 시 기록된 모집직종·고용형태가 "
    "같은 공고끼리, 유사도 검색이나 사람의 선별 없이 수집 순서에 따라 결정론적으로 1:1 연결했습니다. "
    "가장 유사하거나 최적의 후보, 유일한 지역 대안이라는 의미는 아니며, 이 직종 표본이 전체 지역 "
    "노동시장을 대표한다는 뜻도 아닙니다."
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
    """Every real, capital-area ('metro') posting from the acquired 10:10
    batch, public metadata only -- never full_text (redistributable: false
    for every record in this batch; see REAL_DATA_ACQUISITION_HANDOFF.md).
    """
    postings_by_id = _load_real_postings_by_id(str(_real_postings_path()))
    items = [_to_list_item(r) for r in postings_by_id.values() if r.get("region_group") == "metro"]
    items.sort(key=lambda item: item.posting_id)
    return PostingListResponse(
        home_region=home_region(),
        postings=items,
        dataset_description=REAL_DATASET_DESCRIPTION,
    )


def find_home_region_matches(metro_posting_id: str) -> MatchResponse:
    """Deterministic pair-table lookup (never a similarity search or
    human-curated "best match" choice -- see this module's docstring),
    scoped to the server's configured home region. A metro posting whose
    paired counterpart is not in the home region (not possible in the
    current single-region batch, but checked explicitly so this stays
    correct once a second region pack exists) is treated as no match
    rather than ever returning a candidate from an unconfigured region.
    In the current dataset this returns at most one candidate -- there is
    no ranking or multi-candidate selection logic here.
    """
    postings_by_id = _load_real_postings_by_id(str(_real_postings_path()))
    metro_record = postings_by_id.get(metro_posting_id)
    if metro_record is None or metro_record.get("region_group") != "metro":
        raise NoMatchFoundError(
            f"no capital-area posting found for posting_id={metro_posting_id!r}",
            details={"posting_id": metro_posting_id},
        )

    pairs = _load_real_pairs(str(_real_matched_pairs_path()))
    candidates: list[MatchCandidate] = []
    for pair in pairs:
        if pair.get("metro_posting_id") != metro_posting_id:
            continue
        home_id = pair.get("jeonbuk_posting_id")
        home_record = postings_by_id.get(home_id) if home_id else None
        if home_record is None:
            continue
        if home_record.get("region_group", "").strip().lower() != home_region():
            # Server-side region-pack enforcement: never surface a
            # candidate outside the configured home region, even if a
            # (currently hypothetical) future pairs file contained one.
            continue

        matching_fields = ["occupation"]
        mismatch_fields: list[str] = []
        if home_record.get("employment_type") == metro_record.get("employment_type"):
            matching_fields.append("employment_type")
        else:
            mismatch_fields.append("employment_type")

        candidates.append(
            MatchCandidate(
                posting_id=home_record["posting_id"],
                source_id=home_record.get("source_name"),
                source_url=home_record.get("source_id_url"),
                region=home_record.get("region_group", home_region()),
                municipality=home_record.get("municipality"),
                occupation=home_record["occupation"],
                employment_type=home_record["employment_type"],
                company_name=home_record.get("company_name"),
                source_text=None,  # never leak real text through the match/listing layer
                is_synthetic=bool(home_record.get("synthetic_test_fixture")),
                matching_fields=matching_fields,
                mismatch_fields=mismatch_fields,
                description=REAL_DATASET_DESCRIPTION,
            )
        )

    if not candidates:
        raise NoMatchFoundError(
            f"no {home_region()} posting matched to posting_id={metro_posting_id!r}",
            details={"posting_id": metro_posting_id, "home_region": home_region()},
        )

    return MatchResponse(
        query_occupation=metro_record["occupation"],
        query_employment_type=metro_record.get("employment_type"),
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
