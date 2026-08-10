from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.core.exceptions import NotFoundError


def test_health_check_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_correlation_id_is_echoed_in_response_headers() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"x-correlation-id": "test-corr-id"})

    assert response.headers["x-correlation-id"] == "test-corr-id"


def test_correlation_id_is_generated_when_absent() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.headers["x-correlation-id"]  # non-empty


def test_jarvis_error_is_mapped_to_json_response() -> None:
    app = create_app()

    @app.get("/boom")
    async def boom() -> None:
        raise NotFoundError("thing not found", details={"id": "1"})

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "NotFoundError"
    assert body["message"] == "thing not found"
    assert body["details"] == {"id": "1"}
