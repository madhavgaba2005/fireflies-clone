"""The error envelope is uniform for domain, validation, routing and unexpected errors."""

from collections.abc import Iterator

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.errors import ConflictError, NotFoundError


@pytest.fixture
def error_client(app: FastAPI) -> Iterator[TestClient]:
    router = APIRouter()

    @router.get("/boom/not-found")
    def not_found() -> None:
        raise NotFoundError("Meeting 42 not found", code="meeting_not_found")

    @router.get("/boom/conflict")
    def conflict() -> None:
        raise ConflictError("Already exists", details={"field": "name"})

    @router.get("/boom/validate/{item_id}")
    def validate(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @router.get("/boom/crash")
    def crash() -> None:
        raise RuntimeError("secret stack detail")

    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_domain_not_found(error_client: TestClient) -> None:
    response = error_client.get("/boom/not-found")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "meeting_not_found", "message": "Meeting 42 not found", "details": None}
    }


def test_domain_conflict_keeps_details(error_client: TestClient) -> None:
    response = error_client.get("/boom/conflict")
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "conflict",
        "message": "Already exists",
        "details": {"field": "name"},
    }


def test_validation_error_lists_fields(error_client: TestClient) -> None:
    response = error_client.get("/boom/validate/not-a-number")
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["path", "item_id"]


def test_unknown_route_uses_envelope(error_client: TestClient) -> None:
    response = error_client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_wrong_method_uses_envelope(error_client: TestClient) -> None:
    response = error_client.delete("/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unexpected_error_hides_internals(error_client: TestClient) -> None:
    response = error_client.get("/boom/crash")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret" not in response.text
