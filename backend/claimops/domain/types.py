from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ClaimFilters:
    partner: str | None = None
    product: str | None = None
    claim_type: str | None = None
    status: str | None = None
    stage: str | None = None
    assigned_agent: str | None = None
    sla_status: str | None = None
    risk_level: str | None = None
    documentation_status: str | None = None
    minimum_risk_score: int | None = None
    missing_document: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
