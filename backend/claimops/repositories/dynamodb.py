from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Protocol

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

SCHEMA_VERSION = 1
CLAIM_INDEX = "GSI1"
METADATA_FIELDS = {
    "PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "GSI3PK", "GSI3SK",
    "GSI4PK", "GSI4SK", "GSI5PK", "GSI5SK", "entity_type", "schema_version",
}


class DynamoDBClient(Protocol):
    def get_item(self, **kwargs: Any) -> Mapping[str, Any]: ...

    def query(self, **kwargs: Any) -> Mapping[str, Any]: ...

    def transact_write_items(self, **kwargs: Any) -> Mapping[str, Any]: ...


def claim_to_item(claim: Mapping[str, Any]) -> dict[str, Any]:
    """Map an application claim into the executable single-table shape."""
    claim_id = str(claim["claim_id"])
    created_at = str(claim["created_at"])
    updated_at = str(claim["updated_at"])
    deadline = str(claim["sla_deadline"])
    status = str(claim["status"])
    stage = str(claim["stage"])
    partner = str(claim["partner"])
    item = _to_decimal(dict(claim))
    item.update(
        {
            "PK": f"CLAIM#{claim_id}",
            "SK": "META",
            "entity_type": "CLAIM",
            "schema_version": SCHEMA_VERSION,
            "version": int(claim.get("version", 1)),
            "GSI1PK": "CLAIMS",
            "GSI1SK": f"{created_at}#{claim_id}",
            "GSI2PK": f"SLA#{claim['sla_status']}",
            "GSI2SK": f"{deadline}#{claim_id}",
            "GSI4PK": f"PARTNER#{partner}",
            "GSI4SK": f"{status}#{created_at}#{claim_id}",
            "GSI5PK": f"STAGE#{stage}#{status}",
            "GSI5SK": f"{updated_at}#{claim_id}",
        }
    )
    if claim.get("assigned_agent"):
        item["GSI3PK"] = f"AGENT#{claim['assigned_agent']}"
        item["GSI3SK"] = f"{status}#{updated_at}#{claim_id}"
    return item


def item_to_claim(item: Mapping[str, Any]) -> dict[str, Any]:
    if item.get("entity_type") != "CLAIM" or item.get("SK") != "META":
        raise ValueError("DynamoDB item is not a claim metadata entity")
    claim = {key: value for key, value in item.items() if key not in METADATA_FIELDS}
    return _from_decimal(claim)


def serialize_item(item: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    serializer = TypeSerializer()
    return {key: serializer.serialize(value) for key, value in item.items()}


def deserialize_item(item: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    deserializer = TypeDeserializer()
    return {key: deserializer.deserialize(value) for key, value in item.items()}


class DynamoClaimRepository:
    """Read-only DynamoDB adapter; command writes arrive in Phase 7."""

    def __init__(self, client: DynamoDBClient, table_name: str) -> None:
        if not table_name.strip():
            raise ValueError("table_name is required")
        self._client = client
        self._table_name = table_name

    def get(self, claim_id: str) -> Mapping[str, Any] | None:
        response = self._client.get_item(
            TableName=self._table_name,
            Key=serialize_item({"PK": f"CLAIM#{claim_id}", "SK": "META"}),
            ConsistentRead=True,
        )
        raw_item = response.get("Item")
        return item_to_claim(deserialize_item(raw_item)) if raw_item else None

    def list_all(self) -> Sequence[Mapping[str, Any]]:
        """Query the all-claims index, consuming each DynamoDB result page."""
        claims: list[Mapping[str, Any]] = []
        exclusive_start_key: Mapping[str, Any] | None = None
        while True:
            request: dict[str, Any] = {
                "TableName": self._table_name,
                "IndexName": CLAIM_INDEX,
                "KeyConditionExpression": "#gsi_pk = :claims",
                "ExpressionAttributeNames": {"#gsi_pk": "GSI1PK"},
                "ExpressionAttributeValues": {":claims": {"S": "CLAIMS"}},
                "ScanIndexForward": False,
            }
            if exclusive_start_key:
                request["ExclusiveStartKey"] = exclusive_start_key
            response = self._client.query(**request)
            claims.extend(item_to_claim(deserialize_item(item)) for item in response.get("Items", []))
            exclusive_start_key = response.get("LastEvaluatedKey")
            if not exclusive_start_key:
                break
        return claims

    def commit_action(
        self, claim: Mapping[str, Any], event: Mapping[str, Any], expected_version: int
    ) -> Mapping[str, Any]:
        from botocore.exceptions import ClientError
        from claimops.domain.errors import VersionConflictError

        claim_item = serialize_item(claim_to_item(claim))
        audit_item = serialize_item(
            {
                **dict(event),
                "PK": f"CLAIM#{claim['claim_id']}",
                "SK": f"EVENT#{event['timestamp']}#{event['event_id']}",
                "entity_type": "AUDIT_EVENT",
                "schema_version": SCHEMA_VERSION,
                "created_at": event["timestamp"],
                "updated_at": event["timestamp"],
            }
        )
        try:
            self._client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": claim_item,
                            "ConditionExpression": "#version = :expected",
                            "ExpressionAttributeNames": {"#version": "version"},
                            "ExpressionAttributeValues": {":expected": {"N": str(expected_version)}},
                        }
                    },
                    {"Put": {"TableName": self._table_name, "Item": audit_item}},
                ]
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "TransactionCanceledException":
                current = self.get(str(claim["claim_id"]))
                actual = int(current.get("version", 1)) if current else expected_version
                raise VersionConflictError(expected_version, actual) from error
            raise
        return dict(claim)

    def list_audit_events(self, claim_id: str) -> Sequence[Mapping[str, Any]]:
        response = self._client.query(
            TableName=self._table_name,
            KeyConditionExpression="#pk = :pk AND begins_with(#sk, :event)",
            ExpressionAttributeNames={"#pk": "PK", "#sk": "SK"},
            ExpressionAttributeValues={":pk": {"S": f"CLAIM#{claim_id}"}, ":event": {"S": "EVENT#"}},
            ScanIndexForward=False,
        )
        events = []
        for raw in response.get("Items", []):
            item = deserialize_item(raw)
            events.append({key: _from_decimal(value) for key, value in item.items() if key not in METADATA_FIELDS})
        return events


def _to_decimal(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_decimal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_decimal(item) for item in value]
    return value


def _from_decimal(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {key: _from_decimal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_from_decimal(item) for item in value]
    return value
