from __future__ import annotations

from ..errors import ProviderUnavailableError
from ..config import get_settings
from .base import ExtractionProvider
from .mock_provider import MockExtractionProvider

SUPPORTED_PROVIDERS = ("mock", "anthropic", "nvidia")


def get_provider() -> ExtractionProvider:
    settings = get_settings()
    if settings.llm_provider == "mock":
        return MockExtractionProvider()
    if settings.llm_provider == "anthropic":
        from .anthropic_provider import AnthropicExtractionProvider

        return AnthropicExtractionProvider(model=settings.anthropic_model)
    if settings.llm_provider == "nvidia":
        from .nvidia_provider import NvidiaExtractionProvider

        return NvidiaExtractionProvider(model=settings.nvidia_model)
    # Fail closed: an unrecognized LLM_PROVIDER (typo or otherwise) must never
    # silently resolve to the mock provider -- that would let a
    # misconfigured deployment believe it is running a real LLM check when
    # it is actually offline and deterministic.
    raise ProviderUnavailableError(
        f"unknown LLM_PROVIDER: {settings.llm_provider!r} (expected one of: {', '.join(SUPPORTED_PROVIDERS)})"
    )
