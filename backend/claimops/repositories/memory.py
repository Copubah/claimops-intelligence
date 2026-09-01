from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from types import MappingProxyType
from typing import Any


class InMemoryClaimRepository:
    """Read-only adapter used for local development and contract tests."""

    def __init__(self, claims: Iterable[Mapping[str, Any]]) -> None:
        records = [deepcopy(dict(claim)) for claim in claims]
        self._claims = tuple(MappingProxyType(record) for record in records)
        self._by_id = {str(claim["claim_id"]): claim for claim in self._claims}

    def list_all(self) -> Sequence[Mapping[str, Any]]:
        return self._claims

    def get(self, claim_id: str) -> Mapping[str, Any] | None:
        return self._by_id.get(claim_id)

