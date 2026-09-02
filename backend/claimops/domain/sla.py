from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class SlaStatus(StrEnum):
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    AT_RISK = "AT_RISK"
    BREACHED = "BREACHED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SlaConfig:
    at_risk_minutes: int = 30
    watch_minutes: int = 60

    def __post_init__(self) -> None:
        if self.at_risk_minutes < 0:
            raise ValueError("at_risk_minutes must not be negative")
        if self.watch_minutes <= self.at_risk_minutes:
            raise ValueError("watch_minutes must be greater than at_risk_minutes")

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "SlaConfig":
        values = environment if environment is not None else os.environ
        return cls(
            at_risk_minutes=int(values.get("CLAIMOPS_SLA_AT_RISK_MINUTES", "30")),
            watch_minutes=int(values.get("CLAIMOPS_SLA_WATCH_MINUTES", "60")),
        )


@dataclass(frozen=True, slots=True)
class SlaEvaluation:
    status: SlaStatus
    deadline: datetime | None
    evaluated_at: datetime
    remaining_seconds: float
    breached_by_seconds: float
    is_final: bool = False


@dataclass(frozen=True, slots=True)
class SlaTransition:
    claim_id: str
    previous_status: SlaStatus | None
    evaluation: SlaEvaluation
    changed: bool
    alert_required: bool


class SlaEngine:
    def __init__(self, config: SlaConfig | None = None) -> None:
        self.config = config or SlaConfig()

    def evaluate(
        self,
        deadline: datetime | str | None,
        as_of: datetime,
        *,
        is_final: bool = False,
    ) -> SlaEvaluation:
        evaluated_at = _aware_utc(as_of, "as_of")
        parsed_deadline = _parse_deadline(deadline)
        if parsed_deadline is None:
            return SlaEvaluation(SlaStatus.UNKNOWN, None, evaluated_at, 0.0, 0.0, is_final)
        delta_seconds = (parsed_deadline - evaluated_at).total_seconds()
        if delta_seconds < 0:
            status = SlaStatus.BREACHED
        elif delta_seconds < self.config.at_risk_minutes * 60:
            status = SlaStatus.AT_RISK
        elif delta_seconds <= self.config.watch_minutes * 60:
            status = SlaStatus.WATCH
        else:
            status = SlaStatus.HEALTHY
        return SlaEvaluation(
            status=status,
            deadline=parsed_deadline,
            evaluated_at=evaluated_at,
            remaining_seconds=round(max(0.0, delta_seconds), 3),
            breached_by_seconds=round(max(0.0, -delta_seconds), 3),
            is_final=is_final,
        )

    def evaluate_claim(self, claim: Mapping[str, Any], as_of: datetime) -> SlaTransition:
        claim_id = str(claim["claim_id"])
        final = str(claim.get("status")) in {"Approved", "Rejected", "Closed"}
        evaluation_time = _parse_timestamp(claim.get("updated_at"), "updated_at") if final else as_of
        evaluation = self.evaluate(claim.get("sla_deadline"), evaluation_time, is_final=final)
        raw_previous = claim.get("sla_status")
        try:
            previous = SlaStatus(str(raw_previous)) if raw_previous else None
        except ValueError:
            previous = None
        changed = previous != evaluation.status
        return SlaTransition(
            claim_id=claim_id,
            previous_status=previous,
            evaluation=evaluation,
            changed=changed,
            alert_required=changed and not final and evaluation.status in {SlaStatus.AT_RISK, SlaStatus.BREACHED},
        )

    def evaluate_claims(
        self,
        claims: Iterable[Mapping[str, Any]],
        as_of: datetime,
        *,
        include_final: bool = False,
    ) -> list[SlaTransition]:
        transitions = []
        for claim in claims:
            final = str(claim.get("status")) in {"Approved", "Rejected", "Closed"}
            if final and not include_final:
                continue
            transitions.append(self.evaluate_claim(claim, as_of))
        return transitions


def _parse_deadline(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _aware_utc(value, "deadline")
    if isinstance(value, str):
        try:
            return _aware_utc(datetime.fromisoformat(value.replace("Z", "+00:00")), "deadline")
        except ValueError as error:
            raise ValueError("deadline must be a valid ISO-8601 timestamp") from error
    raise TypeError("deadline must be a datetime, ISO-8601 string, or None")


def _parse_timestamp(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        return _aware_utc(value, field)
    if isinstance(value, str):
        try:
            return _aware_utc(datetime.fromisoformat(value.replace("Z", "+00:00")), field)
        except ValueError as error:
            raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from error
    raise ValueError(f"{field} is required for finalized claims")


def _aware_utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)

