from __future__ import annotations

import httpx
import pytest

from app.errors import ProviderUnavailableError
from app.providers.factory import get_free_text_provider
from app.providers.gpt_oss_provider import DEFAULT_MODEL, REQUEST_TIMEOUT_SECONDS, GptOssFreeTextProvider


def test_missing_key_raises_provider_unavailable(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API", raising=False)
    provider = GptOssFreeTextProvider()
    with pytest.raises(ProviderUnavailableError) as exc_info:
        provider.extract_free_text("일부 채용 공고 본문")
    assert "NVIDIA_API_KEY" in str(exc_info.value)


def test_falls_back_to_nvidia_api_env_var(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_API", "test-key-do-not-leak")
    provider = GptOssFreeTextProvider()
    assert provider._api_key == "test-key-do-not-leak"


def test_default_model_is_gpt_oss_20b():
    assert DEFAULT_MODEL == "openai/gpt-oss-20b"


def test_timeout_is_15_seconds_or_less():
    assert REQUEST_TIMEOUT_SECONDS <= 15


def test_request_never_forces_a_tool_call_and_uses_low_reasoning_effort(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-do-not-leak")
    provider = GptOssFreeTextProvider()
    captured: dict = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"fields": ['
                                '{"field": "duties", "status": "absent"},'
                                '{"field": "tools_or_skills", "status": "absent"},'
                                '{"field": "training_or_mentoring", "status": "absent"},'
                                '{"field": "probation_terms", "status": "absent"}'
                                "]}"
                            )
                        }
                    }
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        captured["headers"] = headers
        return _FakeResponse()

    monkeypatch.setattr("app.providers.gpt_oss_provider.httpx.post", fake_post)
    result = provider.extract_free_text("일부 채용 공고 본문")

    assert captured["url"] == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert "tools" not in captured["json"]
    assert "tool_choice" not in captured["json"]
    assert captured["json"]["reasoning_effort"] == "low"
    assert captured["json"]["model"] == DEFAULT_MODEL
    assert captured["timeout"] <= 15
    assert "test-key-do-not-leak" not in str(captured["headers"]) or captured["headers"]["Authorization"].endswith(
        "test-key-do-not-leak"
    )
    assert {f["field"] for f in result["fields"]} == {
        "duties",
        "tools_or_skills",
        "training_or_mentoring",
        "probation_terms",
    }


def test_timeout_raises_provider_unavailable_without_retrying(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-do-not-leak")
    provider = GptOssFreeTextProvider()
    calls = {"count": 0}

    def raise_timeout(*args, **kwargs):
        calls["count"] += 1
        raise httpx.TimeoutException("simulated timeout")

    monkeypatch.setattr("app.providers.gpt_oss_provider.httpx.post", raise_timeout)

    with pytest.raises(ProviderUnavailableError):
        provider.extract_free_text("일부 채용 공고 본문")
    assert calls["count"] == 1  # never retries internally -- TASK: "1회 이상 반복 재시도 금지"


def test_failure_message_never_leaks_the_api_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "super-secret-key-value")
    provider = GptOssFreeTextProvider()

    def raise_with_key_in_message(*args, **kwargs):
        raise RuntimeError("connection failed for key super-secret-key-value")

    monkeypatch.setattr("app.providers.gpt_oss_provider.httpx.post", raise_with_key_in_message)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        provider.extract_free_text("일부 채용 공고 본문")
    assert "super-secret-key-value" not in str(exc_info.value)


def test_malformed_json_content_raises_provider_unavailable(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-do-not-leak")
    provider = GptOssFreeTextProvider()

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "not valid json"}}]}

    monkeypatch.setattr("app.providers.gpt_oss_provider.httpx.post", lambda *a, **k: _FakeResponse())
    with pytest.raises(ProviderUnavailableError):
        provider.extract_free_text("일부 채용 공고 본문")


def test_factory_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("HYBRID_SLM_PROVIDER", raising=False)
    from app.config import clear_settings_cache
    from app.providers.mock_provider import MockExtractionProvider

    clear_settings_cache()
    try:
        provider = get_free_text_provider()
        assert isinstance(provider, MockExtractionProvider)
    finally:
        clear_settings_cache()


def test_factory_routes_to_gpt_oss_provider(monkeypatch):
    monkeypatch.setenv("HYBRID_SLM_PROVIDER", "nvidia_gpt_oss")
    monkeypatch.setenv("NVIDIA_MODEL", "openai/gpt-oss-20b")
    from app.config import clear_settings_cache

    clear_settings_cache()
    try:
        provider = get_free_text_provider()
        assert isinstance(provider, GptOssFreeTextProvider)
        assert provider._model == "openai/gpt-oss-20b"
    finally:
        clear_settings_cache()


def test_factory_fails_closed_on_unknown_hybrid_provider(monkeypatch):
    monkeypatch.setenv("HYBRID_SLM_PROVIDER", "typo-provider")
    from app.config import clear_settings_cache

    clear_settings_cache()
    try:
        with pytest.raises(ProviderUnavailableError):
            get_free_text_provider()
    finally:
        clear_settings_cache()
