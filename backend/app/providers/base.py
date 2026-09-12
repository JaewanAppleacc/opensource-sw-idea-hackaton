from __future__ import annotations

from typing import Optional, Protocol


class ExtractionProvider(Protocol):
    """Narrow interface every structured-extraction provider implements.

    `extract` returns a plain dict shaped like `app.providers.raw.RawExtraction`
    (occupation, employment_type, six field entries). It must never fabricate
    evidence: any evidence_text/start/end it returns is checked against the
    literal source text downstream and rejected if it does not match exactly.

    Implementations should raise `app.errors.ProviderUnavailableError` for
    configuration/connectivity problems (missing key, missing dependency,
    network failure) rather than returning a malformed payload -- that keeps
    "the provider is down" distinct from "the extraction was low quality",
    which the pipeline retries once.
    """

    name: str

    def extract(self, source_text: str, expected_occupation: Optional[str] = None) -> dict:
        ...
