from __future__ import annotations


def test_health_reports_status_provider_mode_and_dataset_without_secrets(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["provider_mode"] == "mock"
    assert body["dataset_available"] is True
    assert "rubric_version" in body

    dumped = str(body)
    assert "ANTHROPIC_API_KEY" not in dumped
    assert "sk-" not in dumped  # no leaked API-key-shaped secret


def test_local_frontend_origin_receives_cors_header(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
