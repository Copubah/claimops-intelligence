from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Mapping

from claimops.domain.errors import ClaimNotFoundError, InvalidActionError
from claimops.repositories.claims import ClaimRepository


@dataclass(frozen=True, slots=True)
class ActionCommand:
    action: str
    expected_version: int
    owner: str | None = None
    documents: tuple[str, ...] = ()
    note: str | None = None
    resolution: str | None = None


@dataclass(frozen=True, slots=True)
class ActionResult:
    claim: dict[str, Any]
    audit_event: dict[str, Any]
    replayed: bool = False


class ActionService:
    def __init__(self, repository: ClaimRepository, clock=None) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._idempotency: dict[tuple[str, str], tuple[str, ActionResult]] = {}
        self._lock = RLock()

    def action_queue(self, limit: int = 100, priority_filter: str | None = None) -> dict[str, Any]:
        now = self._clock()
        items = []
        for source in self._repository.list_all():
            claim = dict(source)
            if claim["status"] in {"Approved", "Rejected", "Closed"}:
                continue
            classified = self._classify(claim)
            if classified is None:
                continue
            item_priority, issue, recommendation = classified
            created = datetime.fromisoformat(str(claim["created_at"]).replace("Z", "+00:00"))
            items.append(
                {
                    "priority": item_priority,
                    "claim_id": claim["claim_id"],
                    "issue": issue,
                    "stage": claim["stage"],
                    "age_hours": round(max(0, (now - created).total_seconds() / 3600), 1),
                    "sla_status": claim["sla_status"],
                    "sla_deadline": claim["sla_deadline"],
                    "owner": claim.get("assigned_agent"),
                    "partner": claim["partner"],
                    "recommended_action": recommendation,
                    "version": int(claim.get("version", 1)),
                }
            )
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        items.sort(key=lambda item: (order[item["priority"]], item["sla_deadline"], -item["age_hours"]))
        selected = [item for item in items if priority_filter is None or item["priority"] == priority_filter]
        return {
            "items": selected[:limit],
            "total": len(items),
            "critical": sum(item["priority"] == "CRITICAL" for item in items),
            "high": sum(item["priority"] == "HIGH" for item in items),
        }

    def execute(
        self,
        claim_id: str,
        command: ActionCommand,
        actor: str,
        idempotency_key: str,
    ) -> ActionResult:
        normalized_id = claim_id.upper()
        fingerprint = self._fingerprint(command, actor)
        key = (normalized_id, idempotency_key)
        with self._lock:
            replay = self._idempotency.get(key)
            if replay:
                if replay[0] != fingerprint:
                    raise InvalidActionError("Idempotency key was already used for a different action")
                previous_result = replay[1]
                return ActionResult(deepcopy(previous_result.claim), deepcopy(previous_result.audit_event), True)

            existing = self._repository.get(normalized_id)
            if existing is None:
                raise ClaimNotFoundError(normalized_id)
            before = dict(existing)
            after = deepcopy(before)
            changed = self._apply(after, command, actor)
            timestamp = self._clock().astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            after["updated_at"] = timestamp
            after["version"] = command.expected_version + 1
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "actor": actor,
                "action": command.action,
                "claim_id": normalized_id,
                "previous_value": {field: before.get(field) for field in changed},
                "new_value": {field: after.get(field) for field in changed},
            }
            updated = dict(self._repository.commit_action(after, event, command.expected_version))
            result = ActionResult(updated, event)
            self._idempotency[key] = (fingerprint, result)
            return result

    @staticmethod
    def _classify(claim: Mapping[str, Any]) -> tuple[str, str, str] | None:
        if claim["sla_status"] == "BREACHED":
            return "CRITICAL", "SLA breached", "Escalate"
        if int(claim.get("risk_score", 0)) >= 60 and claim.get("risk_review_status") != "REVIEWED":
            return "CRITICAL", "Risk signals require review", "Mark reviewed"
        if claim["sla_status"] == "AT_RISK":
            return "HIGH", "SLA at risk", "Escalate"
        if claim.get("assigned_agent") is None:
            return "HIGH", "Claim is unassigned", "Assign"
        if claim.get("missing_documents"):
            return "HIGH", f"Missing {claim['missing_documents'][0]}", "Request documents"
        if claim["sla_status"] == "WATCH":
            return "MEDIUM", "SLA watch window", "Add follow-up"
        return None

    def _apply(self, claim: dict[str, Any], command: ActionCommand, actor: str) -> tuple[str, ...]:
        action = command.action
        if action in {"ASSIGN", "REASSIGN"}:
            claim["assigned_agent"] = command.owner
            return ("assigned_agent",)
        if action == "ESCALATE":
            claim["status"] = "Escalated"
            return ("status",)
        if action == "REQUEST_DOCUMENTS":
            required = set(claim["required_documents"])
            invalid = set(command.documents) - required
            if invalid:
                raise InvalidActionError(f"Documents are not required for this claim: {', '.join(sorted(invalid))}")
            missing = list(dict.fromkeys([*claim["missing_documents"], *command.documents]))
            claim["missing_documents"] = missing
            claim["submitted_documents"] = [item for item in claim["required_documents"] if item not in missing]
            claim["documentation_status"] = "INCOMPLETE"
            return ("submitted_documents", "missing_documents", "documentation_status")
        if action in {"ADD_NOTE", "ADD_FOLLOW_UP"}:
            note = {
                "type": "FOLLOW_UP" if action == "ADD_FOLLOW_UP" else "NOTE",
                "text": command.note,
                "actor": actor,
                "timestamp": self._clock().astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            }
            claim.setdefault("notes", []).append(note)
            return ("notes",)
        if action == "RESOLVE":
            claim["status"] = command.resolution
            claim["stage"] = "Closed"
            claim["approval_status"] = str(command.resolution).upper()
            return ("status", "stage", "approval_status")
        if action == "MARK_REVIEWED":
            claim["risk_review_status"] = "REVIEWED"
            return ("risk_review_status",)
        raise InvalidActionError(f"Unsupported action: {action}")

    @staticmethod
    def _fingerprint(command: ActionCommand, actor: str) -> str:
        payload = {"command": asdict(command), "actor": actor}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=list).encode()).hexdigest()
