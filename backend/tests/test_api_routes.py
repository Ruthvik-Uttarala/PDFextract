from __future__ import annotations

from app.core.config import Settings
from app.main import create_app


def test_health_route() -> None:
    app = create_app(Settings(), testing=True)
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"service": "pdfextract-backend", "status": "ok"}


def test_ready_route_reports_dependency_errors(monkeypatch) -> None:
    app = create_app(Settings(), testing=True)
    client = app.test_client()

    monkeypatch.setattr("app.services.database_service.ping_postgres", lambda _settings: None)
    monkeypatch.setattr("app.services.storage_service.ping_storage", lambda _settings: None)
    monkeypatch.setattr("app.services.kafka_service.ping_kafka", lambda _settings: None)

    response = client.get("/api/ready")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ready"
    assert payload["checks"]["postgres"]["ok"] is True
    assert payload["checks"]["minio"]["ok"] is True
    assert payload["checks"]["kafka"]["ok"] is True


def test_me_requires_bearer_token() -> None:
    app = create_app(Settings(firebase_project_id="demo"), testing=True)
    client = app.test_client()
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_returns_verified_claims(monkeypatch) -> None:
    app = create_app(Settings(firebase_project_id="demo"), testing=True)
    client = app.test_client()

    monkeypatch.setattr(
        "app.services.firebase_service.verify_bearer_token",
        lambda _settings, _token: {
            "uid": "uid-123",
            "email": "user@example.com",
            "name": "User",
            "picture": "https://example.com/avatar.png",
            "role": "user",
        },
    )

    response = client.get("/api/me", headers={"Authorization": "Bearer test-token"})
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["uid"] == "uid-123"
    assert payload["email"] == "user@example.com"
    assert payload["role"] == "user"
