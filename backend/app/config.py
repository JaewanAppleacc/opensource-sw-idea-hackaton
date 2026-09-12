"""Runtime settings sourced from environment variables.

Kept intentionally tiny: this is not a general settings framework, just the
handful of knobs the pipeline needs (which provider to use, which rubric
version is active). No secrets are read here beyond the provider API key,
and nothing here is ever logged.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

_REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env_file() -> None:
    """Loads a real, untracked `.env` at the repo root if one exists.

    Never overrides an already-set OS environment variable (override=False,
    so an explicit `export FOO=bar` before starting the process still wins)
    and is a silent no-op when no `.env` exists (the default for a fresh
    clone -- nothing about this changes behavior without a local `.env`
    file). Never logs or prints the values it loads; python-dotenv's
    default verbose=False is left as-is.
    """
    load_dotenv(_REPO_ROOT / ".env", override=False)


# Runs at import time so every entry point (uvicorn, pytest, scripts) that
# eventually imports this module picks up a local .env the same way,
# instead of each one accidentally depending on whatever the invoking shell
# happened to have exported.
load_env_file()


class Settings(BaseModel):
    llm_provider: str = "mock"
    anthropic_model: str = "claude-sonnet-5"
    nvidia_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    rubric_version: str = "v1"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        llm_provider=os.environ.get("LLM_PROVIDER", "mock"),
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        nvidia_model=os.environ.get("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct"),
        rubric_version=os.environ.get("RUBRIC_VERSION", "v1"),
    )


def clear_settings_cache() -> None:
    """Test-only escape hatch so env var overrides take effect mid-suite."""
    get_settings.cache_clear()
