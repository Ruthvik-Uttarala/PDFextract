from app.main import create_app


def test_health_endpoint() -> None:
    client = create_app().test_client()
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_me_requires_token() -> None:
    client = create_app().test_client()
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.get_json()["error"] == "missing_bearer_token"
