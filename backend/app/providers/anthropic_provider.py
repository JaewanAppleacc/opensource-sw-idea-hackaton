"""Real structured-output provider backed by the Anthropic API.

Only used when LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY is set. Uses a
forced tool call so the model's response is structured JSON rather than
free-form prose, matching the RawExtraction wire schema. Any missing
dependency, missing key, or request failure raises ProviderUnavailableError
-- it is never silently downgraded to a posting status.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from ..errors import ProviderUnavailableError
from ..models.common import FIELD_NAMES

try:  # pragma: no cover - exercised only when the optional dependency is installed
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore[assignment]

EXTRACTION_SYSTEM_PROMPT = (
    "You audit a single job posting's text for six fields: salary, duties, "
    "tools_or_skills, training_or_mentoring, probation_terms, employment_type. "
    "For each field, decide confirmed/vague/absent. For confirmed or vague you "
    "MUST quote an exact, verbatim substring of the posting text as evidence_text, "
    "plus its character start and end offsets into that exact text. Never "
    "paraphrase or invent evidence. For absent, do not include any evidence. "
    "Never output a stability/growth/risk/culture judgement about the employer. "
    "Call the submit_posting_audit tool exactly once with your answer."
)

_FIELD_ENTRY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["field", "status"],
    "properties": {
        "field": {"type": "string", "enum": list(FIELD_NAMES)},
        "status": {"type": "string", "enum": ["confirmed", "vague", "absent"]},
        "evidence_text": {"type": "string"},
        "start": {"type": "integer"},
        "end": {"type": "integer"},
    },
}

_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["fields"],
    "properties": {
        "occupation": {"type": ["string", "null"]},
        "employment_type": {"type": ["string", "null"]},
        "fields": {
            "type": "array",
            "minItems": 6,
            "maxItems": 6,
            "items": _FIELD_ENTRY_SCHEMA,
        },
    },
}


def _build_user_prompt(source_text: str, expected_occupation: Optional[str]) -> str:
    occupation_hint = f"Expected occupation (unverified hint): {expected_occupation}\n" if expected_occupation else ""
    return f"{occupation_hint}Posting text (use exact offsets into this string):\n\n{source_text}"


def _scrub_secret(message: str, secret: Optional[str]) -> str:
    """Defense in depth: some client/network exceptions could in principle
    echo the configured key (e.g. inside a malformed-URL or connection
    error). Never trust the SDK's error formatting alone to keep it out of
    a message that flows into the API's error response.
    """
    if secret:
        message = message.replace(secret, "[REDACTED]")
    return message


class AnthropicExtractionProvider:
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-5") -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if anthropic is None:
            raise ProviderUnavailableError("the 'anthropic' package is not installed")
        if not self._api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not configured")
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def extract(self, source_text: str, expected_occupation: Optional[str] = None) -> dict:
        client = self._get_client()
        tool = {
            "name": "submit_posting_audit",
            "description": "Submit the structured six-field audit extracted from the posting text.",
            "input_schema": _EXTRACTION_JSON_SCHEMA,
        }
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=2000,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[tool],
                tool_choice={"type": "tool", "name": "submit_posting_audit"},
                messages=[{"role": "user", "content": _build_user_prompt(source_text, expected_occupation)}],
            )
        except Exception as exc:  # noqa: BLE001 - any client/network failure means "unavailable"
            raise ProviderUnavailableError(
                f"anthropic request failed: {_scrub_secret(str(exc), self._api_key)}"
            ) from exc

        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise ProviderUnavailableError("anthropic response did not include the expected tool_use block")
