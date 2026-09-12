"""Runtime settings sourced from environment variables.

Kept intentionally tiny: this is not a general settings framework, just the
handful of knobs the pipeline needs (which provider to use, which rubric
version is active). No secrets are read here beyond the provider API key,
and nothing here is ever logged.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    llm_provider: str = "mock"
    anthropic_model: str = "claude-sonnet-5"
    rubric_version: str = "v1"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        llm_provider=os.environ.get("LLM_PROVIDER", "mock"),
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        rubric_version=os.environ.get("RUBRIC_VERSION", "v1"),
    )


def clear_settings_cache() -> None:
    """Test-only escape hatch so env var overrides take effect mid-suite."""
    get_settings.cache_clear()
