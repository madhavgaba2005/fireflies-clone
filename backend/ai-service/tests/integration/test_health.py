from fastapi.testclient import TestClient


def test_liveness_reports_mode_and_provider(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI Processing Service",
        "processing_mode": "kafka",
        "summary_provider": "mock",
    }


def test_openapi_docs_are_served(client: TestClient) -> None:
    assert client.get("/openapi.json").json()["info"]["title"] == "AI Processing Service"
