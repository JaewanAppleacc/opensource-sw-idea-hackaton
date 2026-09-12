from __future__ import annotations


def _payload():
    return {
        "metropolitan": {
            "label": "metropolitan",
            "monthly_income_after_tax": 3200000,
            "monthly_housing_cost": 900000,
            "monthly_other_living_cost": 700000,
            "deposit": 50000000,
        },
        "jeonbuk": {
            "label": "jeonbuk",
            "monthly_income_after_tax": 2700000,
            "monthly_housing_cost": 400000,
            "monthly_other_living_cost": 600000,
            "deposit": 10000000,
        },
    }


def test_finance_compare_is_deterministic_over_http(client):
    first = client.post("/api/v1/finance/compare", json=_payload())
    second = client.post("/api/v1/finance/compare", json=_payload())
    assert first.status_code == 200
    assert first.json() == second.json()


def test_finance_compare_response_shape(client):
    response = client.post("/api/v1/finance/compare", json=_payload())
    body = response.json()

    assert body["options"]["jeonbuk"]["monthly_surplus"] == 1_700_000
    assert body["options"]["metropolitan"]["monthly_surplus"] == 1_600_000
    assert body["crossover"]["varied_variable"] == "monthly_housing_cost"
    assert body["crossover"]["varied_option"] == "jeonbuk"


def test_finance_compare_rejects_negative_income(client):
    payload = _payload()
    payload["jeonbuk"]["monthly_income_after_tax"] = -1
    response = client.post("/api/v1/finance/compare", json=payload)
    assert response.status_code == 422
