from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from claimops.domain.sla import SlaEngine, SlaStatus
from claimops.repositories.claims import ClaimRepository


class SlaControlTowerService:
    """Build a current, read-only SLA operations view for open claims."""

    def __init__(self, repository: ClaimRepository, engine: SlaEngine | None = None) -> None:
        self._repository = repository
        self._engine = engine or SlaEngine()

    def snapshot(self, *, status: SlaStatus | None = None, partner: str | None = None,
                 limit: int = 100, as_of: datetime | None = None) -> dict[str, Any]:
        evaluated_at = as_of or datetime.now(UTC)
        rows: list[dict[str, Any]] = []
        counts: Counter[str] = Counter()
        claims = {str(claim["claim_id"]): claim for claim in self._repository.list_all()}

        for transition in self._engine.evaluate_claims(claims.values(), evaluated_at):
            claim = claims[transition.claim_id]
            evaluation = transition.evaluation
            counts[evaluation.status.value] += 1
            if status is not None and evaluation.status != status:
                continue
            if partner and str(claim.get("partner", "")).casefold() != partner.casefold():
                continue
            rows.append({
                "claim_id": transition.claim_id,
                "status": evaluation.status.value,
                "deadline": evaluation.deadline,
                "remaining_seconds": evaluation.remaining_seconds,
                "breached_by_seconds": evaluation.breached_by_seconds,
                "stage": claim.get("stage"),
                "assigned_agent": claim.get("assigned_agent"),
                "partner": claim.get("partner"),
            })

        urgency = {"BREACHED": 0, "AT_RISK": 1, "WATCH": 2, "HEALTHY": 3, "UNKNOWN": 4}
        rows.sort(key=lambda row: (urgency[row["status"]], row["deadline"] or datetime.max.replace(tzinfo=UTC)))
        return {
            "evaluated_at": evaluated_at,
            "thresholds": {"at_risk_minutes": self._engine.config.at_risk_minutes,
                           "watch_minutes": self._engine.config.watch_minutes},
            "summary": {value.value.lower(): counts[value.value] for value in SlaStatus},
            "total_open": sum(counts.values()),
            "total_matching": len(rows),
            "items": rows[:limit],
        }
