from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class ClaimRepository(Protocol):
    """Persistence boundary consumed by claim application services."""

    def list_all(self) -> Sequence[Mapping[str, Any]]: ...

    def get(self, claim_id: str) -> Mapping[str, Any] | None: ...

    def commit_action(
        self, claim: Mapping[str, Any], event: Mapping[str, Any], expected_version: int
    ) -> Mapping[str, Any]: ...

    def list_audit_events(self, claim_id: str) -> Sequence[Mapping[str, Any]]: ...
