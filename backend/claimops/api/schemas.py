from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskSignalResponse(BaseModel):
    rule_id: str
    explanation: str
    points: int = Field(ge=0, le=100)


class DocumentFollowUpResponse(BaseModel):
    document_type: str
    date_requested: datetime
    reminder_count: int = Field(ge=0)
    last_reminder: datetime | None
    next_follow_up: datetime
    status: str


class ClaimSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    claim_id: str = Field(pattern=r"^CLM-\d{5,}$")
    created_at: datetime
    updated_at: datetime
    partner: str
    product: str
    claim_type: str
    status: str
    stage: str
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    assigned_agent: str | None
    sla_deadline: datetime
    sla_status: Literal["HEALTHY", "WATCH", "AT_RISK", "BREACHED", "UNKNOWN"]
    missing_documents: list[str]
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    approval_status: str
    tat_hours: float | None = Field(default=None, ge=0)


class ClaimDetailResponse(ClaimSummaryResponse):
    facility: str
    document_follow_up: list[DocumentFollowUpResponse]
    risk_signals: list[RiskSignalResponse]
    risk_recommendation: str
    rejection_reason: str | None
    qa_score: int | None = Field(default=None, ge=0, le=100)
    data_classification: Literal["SYNTHETIC"]


class ClaimListResponse(BaseModel):
    items: list[ClaimSummaryResponse]
    next_cursor: str | None
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class ClaimQuery(BaseModel):
    partner: str | None = None
    product: str | None = None
    claim_type: str | None = None
    status: str | None = None
    stage: str | None = None
    assigned_agent: str | None = None
    sla_status: Literal["HEALTHY", "WATCH", "AT_RISK", "BREACHED"] | None = None
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None = None
    minimum_risk_score: int | None = Field(default=None, ge=0, le=100)
    missing_document: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    limit: int = Field(default=25, ge=1, le=100)
    cursor: str | None = None

    @model_validator(mode="after")
    def validate_period(self) -> "ClaimQuery":
        if self.created_from and self.created_to and self.created_from > self.created_to:
            raise ValueError("created_from must not be after created_to")
        return self


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

