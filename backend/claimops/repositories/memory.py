from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from threading import RLock
from typing import Any


class InMemoryClaimRepository:
    """Thread-safe local adapter used for development and contract tests."""

    def __init__(self, claims: Iterable[Mapping[str, Any]]) -> None:
        records = [deepcopy(dict(claim)) for claim in claims]
        self._by_id = {str(claim["claim_id"]): claim for claim in records}
        self._audit_events: list[dict[str, Any]] = []
        self._lock = RLock()

    def list_all(self) -> Sequence[Mapping[str, Any]]:
        with self._lock:
            return tuple(deepcopy(claim) for claim in self._by_id.values())

    def get(self, claim_id: str) -> Mapping[str, Any] | None:
        with self._lock:
            claim = self._by_id.get(claim_id)
            return deepcopy(claim) if claim else None

    def commit_action(
        self, claim: Mapping[str, Any], event: Mapping[str, Any], expected_version: int
    ) -> Mapping[str, Any]:
        from claimops.domain.errors import ClaimNotFoundError, VersionConflictError

        claim_id = str(claim["claim_id"])
        with self._lock:
            current = self._by_id.get(claim_id)
            if current is None:
                raise ClaimNotFoundError(claim_id)
            actual_version = int(current.get("version", 1))
            if actual_version != expected_version:
                raise VersionConflictError(expected_version, actual_version)
            updated = deepcopy(dict(claim))
            updated["version"] = actual_version + 1
            self._by_id[claim_id] = updated
            self._audit_events.append(deepcopy(dict(event)))
            return deepcopy(updated)

    def list_audit_events(self, claim_id: str) -> Sequence[Mapping[str, Any]]:
        with self._lock:
            events = [deepcopy(event) for event in self._audit_events if event["claim_id"] == claim_id]
        return tuple(sorted(events, key=lambda event: event["timestamp"], reverse=True))
