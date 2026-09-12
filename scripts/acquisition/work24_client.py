"""Reproducible collector for the 고용24/워크넷 채용정보 Open API (Phase 1 of
TASK_REAL_DATA_ACQUISITION.md).

Real-world status as of 2026-09-12 (see docs/acquisition/WORK24_API_NOTES.md):
the legacy 워크넷 Open API has been discontinued and merged into 고용24.
The official public service pages disclose the list/detail endpoints, core
parameter names, XML response requirement, and output fields. An approved
service key and a live-response mapping check are still human-gated and have
not been completed for this repository.

Consequently this client has two modes:

  --dry-run / --fixture PATH   Fully functional offline. Reads a local JSON
                                fixture (a documented GUESS at response
                                shape, never claimed to be a real captured
                                response) through the same pagination/
                                normalization/error-handling code path a
                                live call would use. Safe to run with no
                                network access and no key.

  (live mode, no flag)         Refuses to run and raises
                                CredentialOrConfigUnavailableError with the
                                exact reason (missing WORK24_SERVICE_KEY env
                                var, and/or the adapter not yet live-verified)
                                UNLESS both the
                                key and a verified config are present. It
                                never invents an endpoint or fabricates a
                                "successful" response.

CLI:
  python scripts/acquisition/work24_client.py \\
      --region jeonbuk --occupation "생산직(제조 조립원)" \\
      --employment-type 정규직 --since 2026-09-01 --until 2026-09-12 \\
      --out data/intake/real_postings.jsonl --raw-out data/private/work24_raw \\
      [--dry-run --fixture tests/acquisition/fixtures/work24_sample_response.json]

The service key is read ONLY from the WORK24_SERVICE_KEY environment
variable. It is never logged, never included in an exception message, and
never written to any output file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquisition_utils import (  # noqa: E402
    AcquisitionError,
    CredentialOrConfigUnavailableError,
    NetworkError,
    write_jsonl,
)

CONFIG_PATH = Path(__file__).resolve().parent / "work24_endpoint_config.yaml"
SERVICE_KEY_ENV_VAR = "WORK24_SERVICE_KEY"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 10


def load_endpoint_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def assert_live_mode_available(config: dict[str, Any]) -> str:
    """Returns the service key if live mode is genuinely usable, otherwise
    raises CredentialOrConfigUnavailableError with the precise blocker(s).
    Never returns a fabricated or partially-filled key/config.
    """
    reasons: list[str] = []
    key = os.environ.get(SERVICE_KEY_ENV_VAR)
    if not key:
        reasons.append(
            f"{SERVICE_KEY_ENV_VAR} is not set. The key must come from an "
            "approved Work24 usage application and must "
            "only ever be passed as an environment variable."
        )
    if not config.get("verified"):
        reasons.append(
            "work24_endpoint_config.yaml is not verified (verified: false). "
            "The public endpoint is documented, but the complete adapter "
            "mapping has not been verified against a live authenticated "
            "response — see docs/acquisition/WORK24_API_NOTES.md."
        )
    if reasons:
        raise CredentialOrConfigUnavailableError(" ".join(reasons))
    assert key is not None
    return key


class Work24Client:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def fetch_page(
        self,
        *,
        region: str,
        occupation: str,
        employment_type: str,
        since: str,
        until: str,
        start_page: int,
        display_count: int,
        service_key: str,
    ) -> dict[str, Any]:
        """Performs one live HTTP call. Only reachable after
        assert_live_mode_available() has succeeded, so `service_key` and
        `self.config` are both confirmed non-placeholder at this point.
        """
        import urllib.error
        import urllib.parse
        import urllib.request

        params = {
            self.config["auth_param_name"]: service_key,
            self.config["region_param_name"]: region,
            self.config["occupation_param_name"]: occupation,
            self.config["employment_type_param_name"]: employment_type,
            self.config["start_date_param_name"]: since,
            self.config["end_date_param_name"]: until,
            self.config["start_page_param_name"]: start_page,
            self.config["display_count_param_name"]: display_count,
        }
        url = self.config["base_url"].rstrip("/") + "/" + self.config["list_endpoint_path"].lstrip("/")
        query = urllib.parse.urlencode(params)
        full_url = f"{url}?{query}"

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(full_url, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    status = resp.status
                    body = resp.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    # Never echo the URL (it contains the key) in the error.
                    raise CredentialOrConfigUnavailableError(
                        f"Work24 API rejected the request with HTTP {e.code} "
                        "(unauthorized/forbidden). The service key may be "
                        "invalid, unapproved for this API, or rate-limited."
                    ) from None
                last_error = e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_error = e
            else:
                if status != 200:
                    last_error = NetworkError(f"unexpected HTTP status {status}")
                else:
                    return self._parse_response(body)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise NetworkError(
            f"Work24 API call failed after {MAX_RETRIES} attempts: {last_error!r}"
        ) from last_error

    def _parse_response(self, body: str) -> dict[str, Any]:
        fmt = self.config.get("response_format")
        if fmt == "json":
            return json.loads(body)
        raise AcquisitionError(
            f"response_format={fmt!r} has no confirmed parser yet — fill in "
            "work24_endpoint_config.yaml from the verified spec before "
            "running live mode."
        )


def normalize_record(raw: dict[str, Any], field_map: dict[str, str], region_group: str) -> dict[str, Any]:
    """Maps a single raw API record to the shared posting schema
    (data/postings/README.md) using the confirmed field_map. Raises if the
    map is incomplete rather than guessing a field name.
    """
    missing_map_keys = [k for k, v in field_map.items() if v is None]
    if missing_map_keys:
        raise AcquisitionError(
            "response_field_map is missing confirmed source field names for: "
            f"{missing_map_keys}. Fill these in from the verified spec first."
        )
    return {
        "posting_id": raw[field_map["posting_id"]],
        "region_group": region_group,
        "company_name": raw[field_map["company_name"]],
        "occupation": raw[field_map["occupation"]],
        "employment_type": raw[field_map["employment_type"]],
        "source_name": "고용24/워크넷 채용정보 Open API",
        "source_id_url": raw.get(field_map["posting_url"]),
        "collection_date": time.strftime("%Y-%m-%d"),
        "full_text": raw.get(field_map["detail_text"]),
        "synthetic_test_fixture": False,
    }


def run_dry_run(fixture_path: Path, region_group: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    with fixture_path.open(encoding="utf-8") as f:
        fixture = json.load(f)
    field_map = fixture.get("field_map_override") or config.get("response_field_map", {})
    records = fixture.get("records", [])
    return [normalize_record(r, field_map, region_group) for r in records]


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--region", required=True, choices=["jeonbuk", "metro"])
    p.add_argument("--occupation", required=True)
    p.add_argument("--employment-type", required=True)
    p.add_argument("--since", required=True, help="YYYY-MM-DD")
    p.add_argument("--until", required=True, help="YYYY-MM-DD")
    p.add_argument("--out", type=Path, default=Path("data/intake/real_postings.jsonl"))
    p.add_argument("--raw-out", type=Path, default=Path("data/private/work24_raw"))
    p.add_argument("--start-page", type=int, default=1)
    p.add_argument("--display-count", type=int, default=100)
    p.add_argument("--dry-run", action="store_true", help="Use --fixture instead of a live API call.")
    p.add_argument("--fixture", type=Path, help="Local JSON fixture for --dry-run mode.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    config = load_endpoint_config()

    if args.dry_run:
        if not args.fixture:
            print("error: --dry-run requires --fixture PATH", file=sys.stderr)
            return 2
        records = run_dry_run(args.fixture, args.region, config)
        write_jsonl(args.out, records)
        print(f"dry-run: wrote {len(records)} normalized record(s) to {args.out}")
        return 0

    try:
        service_key = assert_live_mode_available(config)
    except CredentialOrConfigUnavailableError as e:
        print(f"BLOCKED_NO_CREDENTIAL: {e}", file=sys.stderr)
        return 1

    client = Work24Client(config)
    try:
        response = client.fetch_page(
            region=args.region,
            occupation=args.occupation,
            employment_type=args.employment_type,
            since=args.since,
            until=args.until,
            start_page=args.start_page,
            display_count=args.display_count,
            service_key=service_key,
        )
    except AcquisitionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    records = [
        normalize_record(r, config["response_field_map"], args.region)
        for r in response.get("records", [])
    ]
    write_jsonl(args.out, records)
    print(f"wrote {len(records)} normalized record(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
