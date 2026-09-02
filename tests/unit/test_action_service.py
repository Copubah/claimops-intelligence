from __future__ import annotations

from datetime import UTC, datetime

import pytest

from claimops.domain.errors import InvalidActionError, VersionConflictError
from claimops.repositories.memory import InMemoryClaimRepository
from claimops.services.actions import ActionCommand, ActionService
from scripts.generate_claims import generate_claims


NOW = datetime(2026, 8, 31, 12, tzinfo=UTC)
ACTOR = "manager@example.test"


def service_with_claim(claim: dict) -> tuple[ActionService, InMemoryClaimRepository]:
    repository = InMemoryClaimRepository([claim])
    return ActionService(repository, clock=lambda: NOW), repository


def open_claim() -> dict:
    return next(claim for claim in generate_claims(100, seed=22, as_of=NOW) if claim["status"] not in {"Approved", "Rejected", "Closed"})


@pytest.mark.parametrize("action", ["ASSIGN", "REASSIGN"])
def test_assignment_actions_update_owner_and_audit(action: str) -> None:
    claim = open_claim()
    service, repository = service_with_claim(claim)
    result = service.execute(
        claim["claim_id"], ActionCommand(action, claim["version"], owner="Agent Hamisi"), ACTOR, f"key-{action}"
    )
    assert result.claim["assigned_agent"] == "Agent Hamisi"
    assert result.claim["version"] == 2
    assert result.audit_event["actor"] == ACTOR
    assert repository.list_audit_events(claim["claim_id"])[0]["action"] == action


def test_idempotent_retry_does_not_repeat_audit_event() -> None:
    claim = open_claim()
    service, repository = service_with_claim(claim)
    command = ActionCommand("ESCALATE", claim["version"])
    first = service.execute(claim["claim_id"], command, ACTOR, "same-key")
    second = service.execute(claim["claim_id"], command, ACTOR, "same-key")
    assert second.replayed is True
    assert second.audit_event["event_id"] == first.audit_event["event_id"]
    assert len(repository.list_audit_events(claim["claim_id"])) == 1


def test_idempotency_key_cannot_be_reused_for_other_action() -> None:
    claim = open_claim()
    service, _ = service_with_claim(claim)
    service.execute(claim["claim_id"], ActionCommand("ESCALATE", 1), ACTOR, "same-key")
    with pytest.raises(InvalidActionError, match="different action"):
        service.execute(claim["claim_id"], ActionCommand("MARK_REVIEWED", 2), ACTOR, "same-key")


def test_stale_version_is_rejected() -> None:
    claim = open_claim()
    service, _ = service_with_claim(claim)
    with pytest.raises(VersionConflictError):
        service.execute(claim["claim_id"], ActionCommand("ESCALATE", 99), ACTOR, "stale-key")


def test_request_documents_recalculates_completeness() -> None:
    claim = open_claim()
    claim["missing_documents"] = []
    claim["submitted_documents"] = list(claim["required_documents"])
    claim["documentation_status"] = "COMPLETE"
    service, _ = service_with_claim(claim)
    requested = claim["required_documents"][0]
    result = service.execute(
        claim["claim_id"], ActionCommand("REQUEST_DOCUMENTS", 1, documents=(requested,)), ACTOR, "docs-key-1"
    )
    assert result.claim["documentation_status"] == "INCOMPLETE"
    assert requested in result.claim["missing_documents"]
    assert requested not in result.claim["submitted_documents"]


def test_note_follow_up_review_and_resolution_actions() -> None:
    claim = open_claim()
    service, _ = service_with_claim(claim)
    result = service.execute(claim["claim_id"], ActionCommand("ADD_NOTE", 1, note="Reviewed invoice"), ACTOR, "note-key1")
    assert result.claim["notes"][0]["type"] == "NOTE"
    result = service.execute(claim["claim_id"], ActionCommand("ADD_FOLLOW_UP", 2, note="Call partner tomorrow"), ACTOR, "follow-key")
    assert result.claim["notes"][1]["type"] == "FOLLOW_UP"
    result = service.execute(claim["claim_id"], ActionCommand("MARK_REVIEWED", 3), ACTOR, "review-key")
    assert result.claim["risk_review_status"] == "REVIEWED"
    result = service.execute(claim["claim_id"], ActionCommand("RESOLVE", 4, resolution="Approved"), ACTOR, "resolve1")
    assert result.claim["status"] == "Approved"
    assert result.claim["stage"] == "Closed"


def test_action_queue_prioritizes_critical_before_high() -> None:
    claims = generate_claims(200, seed=20260831, as_of=NOW)
    service = ActionService(InMemoryClaimRepository(claims), clock=lambda: NOW)
    queue = service.action_queue(100)
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    priorities = [order[item["priority"]] for item in queue["items"]]
    assert priorities == sorted(priorities)
    assert queue["total"] >= len(queue["items"])
    assert queue["critical"] > 0
    high = service.action_queue(20, "HIGH")
    assert high["items"]
    assert all(item["priority"] == "HIGH" for item in high["items"])
