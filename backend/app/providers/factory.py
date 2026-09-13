from __future__ import annotations

from ..errors import ProviderUnavailableError
from ..config import get_settings
from .base import ExtractionProvider, FreeTextExtractionProvider
from .mock_provider import MockExtractionProvider

SUPPORTED_PROVIDERS = ("mock", "anthropic", "nvidia")
SUPPORTED_HYBRID_SLM_PROVIDERS = ("mock", "nvidia_gpt_oss")


def get_free_text_provider() -> FreeTextExtractionProvider:
    """Provider for the hybrid pipeline's four-field sLLM step only --
    entirely independent of `get_provider()`/LLM_PROVIDER above, which is
    the legacy six-field path. Fails closed on an unrecognized
    HYBRID_SLM_PROVIDER value, same reasoning as `get_provider()`.
    """
    settings = get_settings()
    if settings.hybrid_slm_provider == "mock":
        return MockExtractionProvider()
    if settings.hybrid_slm_provider == "nvidia_gpt_oss":
        from .gpt_oss_provider import GptOssFreeTextProvider

        return GptOssFreeTextProvider(model=settings.gpt_oss_model)
    raise ProviderUnavailableError(
        f"unknown HYBRID_SLM_PROVIDER: {settings.hybrid_slm_provider!r} "
        f"(expected one of: {', '.join(SUPPORTED_HYBRID_SLM_PROVIDERS)})"
    )


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
