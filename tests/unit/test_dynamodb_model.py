from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from claimops.repositories.dynamodb import (
    DynamoClaimRepository,
    claim_to_item,
    deserialize_item,
    item_to_claim,
    serialize_item,
)
from scripts.generate_claims import generate_claims


AS_OF = datetime(2026, 8, 31, 12, tzinfo=UTC)


class FakeDynamoClient:
    def __init__(self, pages: list[list[dict[str, Any]]] | None = None, item: dict[str, Any] | None = None) -> None:
        self.pages = pages or []
        self.item = item
        self.query_calls: list[dict[str, Any]] = []
        self.get_calls: list[dict[str, Any]] = []

    def get_item(self, **kwargs: Any) -> dict[str, Any]:
        self.get_calls.append(kwargs)
        return {"Item": self.item} if self.item else {}

    def query(self, **kwargs: Any) -> dict[str, Any]:
        self.query_calls.append(kwargs)
        index = len(self.query_calls) - 1
        response: dict[str, Any] = {"Items": self.pages[index]}
        if index < len(self.pages) - 1:
            response["LastEvaluatedKey"] = {"PK": {"S": "cursor"}, "SK": {"S": "cursor"}}
        return response


def synthetic_claims(count: int = 3) -> list[dict[str, Any]]:
    return generate_claims(count=count, seed=17, as_of=AS_OF)


def test_claim_item_keys_cover_supported_access_patterns() -> None:
    claim = synthetic_claims(1)[0]
    item = claim_to_item(claim)
    assert item["PK"] == f"CLAIM#{claim['claim_id']}"
    assert item["SK"] == "META"
    assert item["GSI1PK"] == "CLAIMS"
    assert item["GSI2PK"] == f"SLA#{claim['sla_status']}"
    assert item["GSI4PK"] == f"PARTNER#{claim['partner']}"
    assert item["GSI5PK"] == f"STAGE#{claim['stage']}#{claim['status']}"
    if claim["assigned_agent"]:
        assert item["GSI3PK"] == f"AGENT#{claim['assigned_agent']}"
    assert item["entity_type"] == "CLAIM"
    assert item["schema_version"] == 1


def test_round_trip_preserves_application_claim() -> None:
    claim = synthetic_claims(1)[0]
    wire_item = serialize_item(claim_to_item(claim))
    restored = item_to_claim(deserialize_item(wire_item))
    assert restored == claim


def test_unassigned_claim_uses_sparse_agent_index() -> None:
    claim = synthetic_claims(1)[0]
    claim["assigned_agent"] = None
    item = claim_to_item(claim)
    assert "GSI3PK" not in item
    assert "GSI3SK" not in item


def test_non_claim_item_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a claim"):
        item_to_claim({"PK": "PARTNER#X", "SK": "PROFILE", "entity_type": "PARTNER"})


def test_repository_get_uses_consistent_base_table_read() -> None:
    claim = synthetic_claims(1)[0]
    client = FakeDynamoClient(item=serialize_item(claim_to_item(claim)))
    repository = DynamoClaimRepository(client, "claimops-test")
    assert repository.get(claim["claim_id"]) == claim
    assert client.get_calls[0]["ConsistentRead"] is True
    assert deserialize_item(client.get_calls[0]["Key"])["PK"] == f"CLAIM#{claim['claim_id']}"


def test_repository_returns_none_for_missing_claim() -> None:
    assert DynamoClaimRepository(FakeDynamoClient(), "claimops-test").get("CLM-99999") is None


def test_repository_consumes_query_pages_without_scan() -> None:
    claims = synthetic_claims(3)
    pages = [
        [serialize_item(claim_to_item(claim)) for claim in claims[:2]],
        [serialize_item(claim_to_item(claims[2]))],
    ]
    client = FakeDynamoClient(pages=pages)
    restored = DynamoClaimRepository(client, "claimops-test").list_all()
    assert restored == claims
    assert len(client.query_calls) == 2
    assert client.query_calls[0]["IndexName"] == "GSI1"
    assert "ExclusiveStartKey" not in client.query_calls[0]
    assert client.query_calls[1]["ExclusiveStartKey"]


def test_table_name_is_required() -> None:
    with pytest.raises(ValueError, match="table_name"):
        DynamoClaimRepository(FakeDynamoClient(), " ")

