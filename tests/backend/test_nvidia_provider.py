from __future__ import annotations

import pytest
from app.errors import ProviderUnavailableError
from app.providers.factory import get_provider
from app.providers.nvidia_provider import NvidiaExtractionProvider


def test_missing_key_raises_provider_unavailable(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API", raising=False)
    provider = NvidiaExtractionProvider()
    with pytest.raises(ProviderUnavailableError) as exc_info:
        provider.extract("일부 채용 공고 본문")
    assert "NVIDIA_API_KEY" in str(exc_info.value)


def test_falls_back_to_nvidia_api_env_var(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_API", "test-key-do-not-log")
    provider = NvidiaExtractionProvider()
    assert provider._api_key == "test-key-do-not-log"


def test_factory_routes_to_nvidia_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
    from app.config import clear_settings_cache

    clear_settings_cache()
    try:
        provider = get_provider()
        assert isinstance(provider, NvidiaExtractionProvider)
        assert provider._model == "meta/llama-3.3-70b-instruct"
    finally:
        clear_settings_cache()


def test_malformed_response_raises_provider_unavailable(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-do-not-log")
    provider = NvidiaExtractionProvider()

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {}}]}  # no tool_calls

    monkeypatch.setattr("app.providers.nvidia_provider.httpx.post", lambda *a, **k: _FakeResponse())
    with pytest.raises(ProviderUnavailableError):
        provider.extract("일부 채용 공고 본문")
