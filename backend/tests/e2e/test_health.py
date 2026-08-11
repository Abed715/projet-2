import httpx
import pytest

pytestmark = pytest.mark.e2e


def test_health_endpoint_responds_ok_from_a_real_server_process(backend_base_url: str) -> None:
    response = httpx.get(f"{backend_base_url}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_correlation_id_is_echoed_from_a_real_server_process(backend_base_url: str) -> None:
    response = httpx.get(f"{backend_base_url}/health", headers={"x-correlation-id": "e2e-corr"})

    assert response.headers["x-correlation-id"] == "e2e-corr"
