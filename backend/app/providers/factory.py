from __future__ import annotations

from ..config import get_settings
from .base import ExtractionProvider
from .mock_provider import MockExtractionProvider


def get_provider() -> ExtractionProvider:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from .anthropic_provider import AnthropicExtractionProvider

        return AnthropicExtractionProvider(model=settings.anthropic_model)
    if settings.llm_provider == "nvidia":
        from .nvidia_provider import NvidiaExtractionProvider

        return NvidiaExtractionProvider(model=settings.nvidia_model)
    return MockExtractionProvider()
