"""Real structured-output provider backed by NVIDIA's OpenAI-compatible NIM
API (https://integrate.api.nvidia.com/v1/chat/completions).

Added as an explicit, user-approved exception to the "no new integrated
API" rule for the P0 integration branch -- purely as an alternate real-LLM
path for the same single-posting audit pipeline while the project's
Anthropic account had insufficient credit. It reuses the exact same system
prompt, JSON tool schema, and evidence-validation pipeline as the Anthropic
provider (see anthropic_provider.py) so results are directly comparable;
this file does not add any new product feature, endpoint, or scope.

Only used when LLM_PROVIDER=nvidia and an API key is configured (via
NVIDIA_API_KEY, or NVIDIA_API for compatibility with how the key happened
to be stored). Any missing key, missing dependency, or request failure
raises ProviderUnavailableError -- it is never silently downgraded to a
posting status.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from ..errors import ProviderUnavailableError
from .anthropic_provider import EXTRACTION_SYSTEM_PROMPT, _EXTRACTION_JSON_SCHEMA, _build_user_prompt, _scrub_secret

try:  # pragma: no cover - exercised only when the optional dependency is installed
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_TOOL_NAME = "submit_posting_audit"
DEFAULT_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
REQUEST_TIMEOUT_SECONDS = 30


def _read_api_key(explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    return os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_API")


class NvidiaExtractionProvider:
    name = "nvidia"

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        self._api_key = _read_api_key(api_key)
        self._model = model

    def extract(self, source_text: str, expected_occupation: Optional[str] = None) -> dict:
        if httpx is None:
            raise ProviderUnavailableError("the 'httpx' package is not installed")
        if not self._api_key:
            raise ProviderUnavailableError("NVIDIA_API_KEY (or NVIDIA_API) is not configured")

        body: dict[str, Any] = {
            "model": self._model,
            "temperature": 0,
            "max_tokens": 2000,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(source_text, expected_occupation)},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": NVIDIA_TOOL_NAME,
                        "description": "Submit the structured six-field audit extracted from the posting text.",
                        "parameters": _EXTRACTION_JSON_SCHEMA,
                    },
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": NVIDIA_TOOL_NAME}},
        }

        try:
            response = httpx.post(
                NVIDIA_API_BASE_URL,
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json=body,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001 - any client/network failure means "unavailable"
            # Never echo headers/body (they may echo the Authorization header
            # back in some proxies) -- only the exception's own message, and
            # scrub the key from it defensively even so.
            raise ProviderUnavailableError(
                f"nvidia request failed: {_scrub_secret(str(exc), self._api_key)}"
            ) from exc

        try:
            tool_calls = payload["choices"][0]["message"]["tool_calls"]
            arguments = tool_calls[0]["function"]["arguments"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailableError(
                "nvidia response did not include the expected tool call"
            ) from exc

        if isinstance(arguments, str):
            try:
                return json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ProviderUnavailableError(f"nvidia tool call arguments were not valid JSON: {exc}") from exc
        return dict(arguments)
