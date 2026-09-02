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
    required_documents: list[str]
    submitted_documents: list[str]
    missing_documents: list[str]
    documentation_status: Literal["COMPLETE", "INCOMPLETE"]
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    approval_status: str
    tat_hours: float | None = Field(default=None, ge=0)
    version: int = Field(ge=1)


class ClaimDetailResponse(ClaimSummaryResponse):
    facility: str
    document_follow_up: list[DocumentFollowUpResponse]
    risk_signals: list[RiskSignalResponse]
    risk_recommendation: str
    rejection_reason: str | None
    qa_score: int | None = Field(default=None, ge=0, le=100)
    data_classification: Literal["SYNTHETIC"]
    risk_review_status: str
    notes: list[dict[str, Any]]


class ClaimActionRequest(BaseModel):
    action: Literal[
        "ASSIGN", "REASSIGN", "ESCALATE", "REQUEST_DOCUMENTS", "ADD_FOLLOW_UP",
        "ADD_NOTE", "RESOLVE", "MARK_REVIEWED",
    ]
    expected_version: int = Field(ge=1)
    owner: str | None = Field(default=None, min_length=2, max_length=80)
    documents: list[str] = Field(default_factory=list, max_length=10)
    note: str | None = Field(default=None, min_length=2, max_length=500)
    resolution: Literal["Approved", "Rejected", "Closed"] | None = None

    @model_validator(mode="after")
    def validate_action_fields(self) -> "ClaimActionRequest":
        if self.action in {"ASSIGN", "REASSIGN"} and not self.owner:
            raise ValueError("owner is required for assignment actions")
        if self.action == "REQUEST_DOCUMENTS" and not self.documents:
            raise ValueError("documents are required for REQUEST_DOCUMENTS")
        if self.action in {"ADD_NOTE", "ADD_FOLLOW_UP"} and not self.note:
            raise ValueError("note is required for note and follow-up actions")
        if self.action == "RESOLVE" and not self.resolution:
            raise ValueError("resolution is required for RESOLVE")
        return self


class AuditEventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    actor: str
    action: str
    claim_id: str
    previous_value: dict[str, Any]
    new_value: dict[str, Any]


class ClaimActionResponse(BaseModel):
    claim: ClaimDetailResponse
    audit_event: AuditEventResponse
    replayed: bool = False


class ActionItemResponse(BaseModel):
    priority: Literal["CRITICAL", "HIGH", "MEDIUM"]
    claim_id: str
    issue: str
    stage: str
    age_hours: float = Field(ge=0)
    sla_status: str
    sla_deadline: datetime
    owner: str | None
    partner: str
    recommended_action: str
    version: int


class ActionQueueResponse(BaseModel):
    items: list[ActionItemResponse]
    total: int
    critical: int
    high: int


class SlaItemResponse(BaseModel):
    claim_id: str
    status: Literal["HEALTHY", "WATCH", "AT_RISK", "BREACHED", "UNKNOWN"]
    deadline: datetime | None
    remaining_seconds: float = Field(ge=0)
    breached_by_seconds: float = Field(ge=0)
    stage: str
    assigned_agent: str | None
    partner: str


class SlaSummaryResponse(BaseModel):
    healthy: int = Field(ge=0)
    watch: int = Field(ge=0)
    at_risk: int = Field(ge=0)
    breached: int = Field(ge=0)
    unknown: int = Field(ge=0)


class SlaThresholdsResponse(BaseModel):
    at_risk_minutes: int = Field(ge=0)
    watch_minutes: int = Field(gt=0)


class SlaControlTowerResponse(BaseModel):
    evaluated_at: datetime
    thresholds: SlaThresholdsResponse
    summary: SlaSummaryResponse
    total_open: int = Field(ge=0)
    total_matching: int = Field(ge=0)
    items: list[SlaItemResponse]


class ClaimListResponse(BaseModel):
    items: list[ClaimSummaryResponse]
    next_cursor: str | None
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class ClaimQuery(BaseModel):
    search: str | None = Field(default=None, min_length=2, max_length=80)
    partner: str | None = None
    product: str | None = None
    claim_type: str | None = None
    status: str | None = None
    stage: str | None = None
    assigned_agent: str | None = None
    sla_status: Literal["HEALTHY", "WATCH", "AT_RISK", "BREACHED"] | None = None
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None = None
    documentation_status: Literal["COMPLETE", "INCOMPLETE"] | None = None
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
