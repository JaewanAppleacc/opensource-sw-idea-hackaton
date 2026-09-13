from __future__ import annotations

from typing import Optional, Protocol


class FreeTextExtractionProvider(Protocol):
    """Narrow interface for the hybrid pipeline's sLLM step (TASK "Work24
    Structured Data + sLLM Hybrid Audit Pipeline" section 3).

    `extract_free_text` returns a plain dict shaped like
    `app.providers.raw.RawFreeTextExtraction` -- exactly the four free-text
    fields (duties, tools_or_skills, training_or_mentoring, probation_terms),
    never salary or employment_type. Implementations must never be given,
    and must never need, company contact/address details -- the hybrid
    pipeline only ever passes `source_text` and `expected_occupation`, the
    same two arguments as `ExtractionProvider.extract`.

    Every `ExtractionProvider` implementation in this codebase (mock,
    Anthropic, NVIDIA) already reports 6 fields end-to-end; this is a
    *separate*, additive interface for the narrower hybrid path, not a
    replacement for the existing one.
    """

    name: str

    def extract_free_text(self, source_text: str, expected_occupation: Optional[str] = None) -> dict:
        ...


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
