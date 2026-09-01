from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx


ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from claimops.api.app import create_app  # noqa: E402
from scripts.generate_claims import generate_claims  # noqa: E402


AS_OF = datetime(2026, 8, 31, 12, tzinfo=UTC)
CLAIMS = generate_claims(120, seed=20260831, as_of=AS_OF)


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app(CLAIMS))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_health_and_request_id() -> None:
    response = request("GET", "/health", headers={"X-Request-ID": "test-request-123"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "claimops-api", "version": "0.1.0"}
    assert response.headers["X-Request-ID"] == "test-request-123"


def test_list_claims_is_paginated() -> None:
    first = request("GET", "/api/v1/claims", params={"limit": 10})
    assert first.status_code == 200
    payload = first.json()
    assert len(payload["items"]) == 10
    assert payload["total"] == 120
    assert payload["next_cursor"]
    second = request("GET", "/api/v1/claims", params={"limit": 10, "cursor": payload["next_cursor"]})
    assert second.status_code == 200
    assert {item["claim_id"] for item in payload["items"]}.isdisjoint(
        item["claim_id"] for item in second.json()["items"]
    )


def test_filters_are_combined_case_insensitively() -> None:
    target = next(claim for claim in CLAIMS if claim["missing_documents"])
    response = request(
        "GET", "/api/v1/claims",
        params={
            "partner": target["partner"].lower(),
            "sla_status": target["sla_status"],
            "missing_document": target["missing_documents"][0].lower(),
            "limit": 100,
        },
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item["partner"] == target["partner"]
        assert item["sla_status"] == target["sla_status"]
        assert target["missing_documents"][0] in item["missing_documents"]


def test_document_completeness_is_explicit_and_filterable() -> None:
    complete = request("GET", "/api/v1/claims", params={"documentation_status": "COMPLETE", "limit": 100})
    incomplete = request("GET", "/api/v1/claims", params={"documentation_status": "INCOMPLETE", "limit": 100})
    assert complete.status_code == 200
    assert incomplete.status_code == 200
    assert complete.json()["total"] > 0
    assert incomplete.json()["total"] > 0
    for claim in complete.json()["items"]:
        assert claim["documentation_status"] == "COMPLETE"
        assert claim["missing_documents"] == []
        assert set(claim["submitted_documents"]) == set(claim["required_documents"])
    for claim in incomplete.json()["items"]:
        assert claim["documentation_status"] == "INCOMPLETE"
        assert claim["missing_documents"]


def test_claim_detail_and_case_normalization() -> None:
    claim_id = CLAIMS[0]["claim_id"]
    response = request("GET", f"/api/v1/claims/{claim_id.lower()}")
    assert response.status_code == 200
    assert response.json()["claim_id"] == claim_id
    assert response.json()["data_classification"] == "SYNTHETIC"


def test_missing_claim_has_structured_error() -> None:
    response = request("GET", "/api/v1/claims/CLM-99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CLAIM_NOT_FOUND"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_invalid_cursor_has_structured_error() -> None:
    response = request("GET", "/api/v1/claims", params={"cursor": "not-a-cursor"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CURSOR"


def test_invalid_limit_and_period_are_rejected() -> None:
    response = request("GET", "/api/v1/claims", params={"limit": 101})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    response = request(
        "GET", "/api/v1/claims",
        params={"created_from": "2026-09-01T00:00:00Z", "created_to": "2026-08-01T00:00:00Z"},
    )
    assert response.status_code == 422


def test_empty_filter_result_is_valid() -> None:
    response = request("GET", "/api/v1/claims", params={"partner": "Nonexistent Fictional Partner"})
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None, "total": 0, "limit": 25}
