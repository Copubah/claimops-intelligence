from __future__ import annotations

import pytest

from claimops.api.app import create_claim_repository
from claimops.repositories.memory import InMemoryClaimRepository


def test_memory_repository_is_safe_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAIMOPS_REPOSITORY", raising=False)
    repository = create_claim_repository([{"claim_id": "CLM-00001"}])
    assert isinstance(repository, InMemoryClaimRepository)


def test_unknown_repository_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAIMOPS_REPOSITORY", "unsupported")
    with pytest.raises(RuntimeError, match="Unsupported CLAIMOPS_REPOSITORY"):
        create_claim_repository()


def test_dynamodb_requires_table_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAIMOPS_REPOSITORY", "dynamodb")
    monkeypatch.delenv("CLAIMOPS_TABLE_NAME", raising=False)
    with pytest.raises(RuntimeError, match="CLAIMOPS_TABLE_NAME"):
        create_claim_repository()

