"""Experimental free-text-only sLLM provider: NVIDIA-hosted GPT-OSS-20B,
used only by the hybrid pipeline's four-field extraction step (TASK
"Work24 Structured Data + sLLM Hybrid Audit Pipeline" section 4).

Deliberately NOT a drop-in replacement for `NvidiaExtractionProvider`
(nvidia_provider.py), which is a separate, existing, six-field, forced
tool-call experiment kept exactly as it was. This provider:

  - Sends only the four free-text fields' worth of prompt (never salary or
    employment_type, never company contact/address details -- the caller
    only ever passes source_text + expected_occupation, same as every
    other provider in this codebase).
  - Uses a plain chat completion with `response_format: json_object` --
    explicitly NOT a forced tool call. GPT-OSS models on NVIDIA's
    OpenAI-compatible endpoint were observed, in the experiment TASK
    section 4 refers to, not to support forced tool-calling the way the
    six-field Anthropic/NVIDIA-Nemotron path does.
  - Sends `reasoning_effort: "low"` (a GPT-OSS-specific request field) and
    a short, hard timeout -- this is a demo-time sanity check, not a
    production extraction path.
  - Never retries internally. A retry-on-schema-failure loop already
    exists one layer up, in `app.services.hybrid_audit_pipeline` (same
    MAX_ATTEMPTS=2 budget as the legacy pipeline) -- adding a second retry
    loop here would let a single logical "analyze" request make up to 4
    live calls, which the task brief explicitly forbids ("실패 시 1회
    이상 반복 재시도 금지").
  - Raises ProviderUnavailableError -- never returns a fabricated payload,
    and never silently substitutes the mock provider's output -- for any
    missing key, missing dependency, timeout, or malformed response.

LLM_PROVIDER=mock remains the default for every demo/test in this
repository; this provider is only ever constructed when something
explicitly asks for it (see app.config.get_settings().hybrid_slm_provider,
env var HYBRID_SLM_PROVIDER).
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from ..errors import ProviderUnavailableError
from .anthropic_provider import _scrub_secret  # shared secret-redaction helper, provider-agnostic

try:  # pragma: no cover - exercised only when the optional dependency is installed
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"
REQUEST_TIMEOUT_SECONDS = 15  # TASK section 4: "timeout 15초 이하"

_SYSTEM_PROMPT = (
    "You audit a single job posting's free text for exactly four fields: "
    "duties, tools_or_skills, training_or_mentoring, probation_terms. "
    "Never report salary or employment_type -- those come from a separate, "
    "structured registry and are not part of your job. For each of the four "
    "fields, decide confirmed, vague, or absent. For confirmed or vague you "
    "MUST quote an exact, verbatim substring of the posting text as "
    "evidence_text, plus its character start and end offsets into that exact "
    "text. Never paraphrase or invent evidence. For absent, evidence_text/"
    "start/end must all be null. Never output a company stability, growth, "
    "or risk judgement. Respond with ONLY a JSON object of this exact shape "
    'and no other keys: {"fields": ['
    '{"field": "duties", "status": "confirmed|vague|absent", '
    '"evidence_text": "...or null", "start": 0, "end": 0}, '
    "... one entry for each of the four fields, each exactly once]}"
)


def _build_user_prompt(source_text: str, expected_occupation: Optional[str]) -> str:
    occupation_hint = f"Expected occupation (unverified hint): {expected_occupation}\n" if expected_occupation else ""
    return f"{occupation_hint}Posting text (use exact offsets into this string):\n\n{source_text}"


def _read_api_key(explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    return os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_API")


class GptOssFreeTextProvider:
    """`FreeTextExtractionProvider` -- see app.providers.base."""

    name = "nvidia_gpt_oss"

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        self._api_key = _read_api_key(api_key)
        self._model = model

    def extract_free_text(self, source_text: str, expected_occupation: Optional[str] = None) -> dict:
        if httpx is None:
            raise ProviderUnavailableError("the 'httpx' package is not installed")
        if not self._api_key:
            raise ProviderUnavailableError("NVIDIA_API_KEY (or NVIDIA_API) is not configured")

        body: dict[str, Any] = {
            "model": self._model,
            "temperature": 0,
            "max_tokens": 1200,
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(source_text, expected_occupation)},
            ],
        }

        try:
            response = httpx.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json=body,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001 - any client/network/timeout failure means "unavailable"
            # Explicit, typed failure -- never silently falls back to the
            # mock provider (TASK: "실패하면 Mock provider로 조용히 성공하지
            # 말고 provider 상태를 명시").
            raise ProviderUnavailableError(
                f"nvidia gpt-oss request failed: {_scrub_secret(str(exc), self._api_key)}"
            ) from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailableError("nvidia gpt-oss response did not include the expected message content") from exc

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderUnavailableError(f"nvidia gpt-oss response content was not valid JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise ProviderUnavailableError("nvidia gpt-oss response content was not a JSON object")
        return parsed
