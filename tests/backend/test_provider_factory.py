from __future__ import annotations

import pytest
from app.config import clear_settings_cache
from app.errors import ProviderUnavailableError
from app.providers.anthropic_provider import AnthropicExtractionProvider
from app.providers.factory import get_provider
from app.providers.mock_provider import MockExtractionProvider
from app.providers.nvidia_provider import NvidiaExtractionProvider


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    clear_settings_cache()
    yield
    clear_settings_cache()


def _set_provider(monkeypatch, value: str | None) -> None:
    if value is None:
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("LLM_PROVIDER", value)
    clear_settings_cache()


def test_unset_provider_defaults_to_mock(monkeypatch):
    _set_provider(monkeypatch, None)
    assert isinstance(get_provider(), MockExtractionProvider)


def test_explicit_mock_selects_mock(monkeypatch):
    _set_provider(monkeypatch, "mock")
    assert isinstance(get_provider(), MockExtractionProvider)


def test_anthropic_selects_anthropic_provider(monkeypatch):
    _set_provider(monkeypatch, "anthropic")
    provider = get_provider()
    assert isinstance(provider, AnthropicExtractionProvider)


def test_nvidia_selects_nvidia_provider(monkeypatch):
    _set_provider(monkeypatch, "nvidia")
    provider = get_provider()
    assert isinstance(provider, NvidiaExtractionProvider)


@pytest.mark.parametrize("bad_value", ["Anthropic", "nvidia ", "openai", "anthropic-v2", "MOCK", ""])
def test_unknown_or_mistyped_provider_fails_closed_not_mock(monkeypatch, bad_value):
    _set_provider(monkeypatch, bad_value)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        get_provider()
    # Must name the bad value so a misconfiguration is diagnosable, and must
    # never silently resolve to the mock provider.
    assert repr(bad_value) in str(exc_info.value) or bad_value in str(exc_info.value)


def test_anthropic_missing_key_is_typed_failure_not_absent(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicExtractionProvider(api_key=None)
    with pytest.raises(ProviderUnavailableError):
        provider.extract("일부 채용 공고 본문")


def test_anthropic_error_message_never_contains_the_configured_key(monkeypatch):
    fake_key = "sk-ant-test-do-not-leak-0000000000"
    provider = AnthropicExtractionProvider(api_key=fake_key)

    class _FakeMessages:
        def create(self, **kwargs):
            # Worst-case: the underlying client/network exception happens to
            # embed the key (e.g. in a malformed-request echo). Our own
            # error message must still not contain it.
            raise RuntimeError(f"connection refused while calling with key {fake_key}")

    class _FakeClient:
        messages = _FakeMessages()

    provider._client = _FakeClient()  # bypass real SDK construction
    with pytest.raises(ProviderUnavailableError) as exc_info:
        provider.extract("일부 채용 공고 본문")
    message = str(exc_info.value)
    assert "anthropic request failed" in message
    assert fake_key not in message


def test_nvidia_error_message_never_contains_the_configured_key(monkeypatch):
    fake_key = "nvapi-test-do-not-leak-0000000000"
    provider = NvidiaExtractionProvider(api_key=fake_key)

    def _fake_post(*args, **kwargs):
        raise RuntimeError(f"connection refused while calling with key {fake_key}")

    monkeypatch.setattr("app.providers.nvidia_provider.httpx.post", _fake_post)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        provider.extract("일부 채용 공고 본문")
    message = str(exc_info.value)
    assert "nvidia request failed" in message
    assert fake_key not in message
