from __future__ import annotations

from ..config import get_settings
from .base import ExtractionProvider
from .mock_provider import MockExtractionProvider


def get_provider() -> ExtractionProvider:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from .anthropic_provider import AnthropicExtractionProvider

        return AnthropicExtractionProvider(model=settings.anthropic_model)
    return MockExtractionProvider()
