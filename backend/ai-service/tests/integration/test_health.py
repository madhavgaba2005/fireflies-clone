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


def test_kafka_mode_starts_the_consumer_and_shuts_down_cleanly() -> None:
    """With an unreachable broker the consumer keeps retrying in the background; the app still
    serves requests and stops promptly."""
    from app.config import Settings
    from app.main import create_app

    settings = Settings(  # type: ignore[call-arg]
        _env_file=None, kafka_bootstrap_servers="127.0.0.1:1", processing_mode="kafka"
    )
    with TestClient(create_app(settings)) as kafka_client:
        assert kafka_client.get("/health").json()["processing_mode"] == "kafka"
