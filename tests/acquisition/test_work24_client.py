import pytest
from conftest import FIXTURES_DIR
from acquisition_utils import CredentialOrConfigUnavailableError
from work24_client import assert_live_mode_available, load_endpoint_config, run_dry_run

SAMPLE_KEY = "TEST_ONLY_WORK24_CREDENTIAL_VALUE"


def unverified_config():
    return {"verified": False}


def verified_config():
    return {
        "verified": True,
        "auth_param_name": "authKey",
        "region_param_name": "region",
        "occupation_param_name": "occupation",
        "employment_type_param_name": "empType",
        "start_date_param_name": "startDate",
        "end_date_param_name": "endDate",
        "start_page_param_name": "startPage",
        "display_count_param_name": "display",
        "base_url": "https://example.invalid",
        "list_endpoint_path": "list",
        "response_format": "json",
    }


def test_shipped_config_is_unverified_by_default():
    config = load_endpoint_config()
    assert config["verified"] is False
    assert config["public_spec_verified"] is True
    assert config["base_url"] == "https://www.work24.go.kr"
    assert config["response_format"] == "xml"


def test_missing_key_and_unverified_config_raises_with_both_reasons(monkeypatch):
    monkeypatch.delenv("WORK24_SERVICE_KEY", raising=False)
    with pytest.raises(CredentialOrConfigUnavailableError) as exc_info:
        assert_live_mode_available(unverified_config())
    message = str(exc_info.value)
    assert "WORK24_SERVICE_KEY" in message
    assert "not verified" in message


def test_present_key_but_unverified_config_still_blocks(monkeypatch):
    monkeypatch.setenv("WORK24_SERVICE_KEY", SAMPLE_KEY)
    with pytest.raises(CredentialOrConfigUnavailableError) as exc_info:
        assert_live_mode_available(unverified_config())
    assert SAMPLE_KEY not in str(exc_info.value)


def test_verified_config_and_present_key_succeeds(monkeypatch):
    monkeypatch.setenv("WORK24_SERVICE_KEY", SAMPLE_KEY)
    key = assert_live_mode_available(verified_config())
    assert key == SAMPLE_KEY


def test_live_mode_never_touches_network_without_credentials(monkeypatch):
    monkeypatch.delenv("WORK24_SERVICE_KEY", raising=False)

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("network call attempted without verified credentials/config")

    monkeypatch.setattr("urllib.request.urlopen", _fail_if_called)
    with pytest.raises(CredentialOrConfigUnavailableError):
        assert_live_mode_available(unverified_config())


def test_dry_run_normalizes_fixture_without_network():
    records = run_dry_run(FIXTURES_DIR / "work24_sample_response.json", "jeonbuk", unverified_config())
    assert len(records) == 1
    rec = records[0]
    assert rec["posting_id"] == "W-TEST-001"
    assert rec["region_group"] == "jeonbuk"
    assert rec["occupation"] == "생산직(제조 조립원)"
    assert rec["synthetic_test_fixture"] is False
