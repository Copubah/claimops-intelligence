from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Query

from claimops.api.dependencies import get_action_service, get_claim_service
from claimops.api.schemas import (
    ActionQueueResponse,
    ClaimActionRequest,
    ClaimActionResponse,
    ClaimDetailResponse,
    ClaimListResponse,
    ClaimQuery,
    ErrorResponse,
    HealthResponse,
)
from claimops.domain.types import ClaimFilters
from claimops.services.actions import ActionCommand, ActionService
from claimops.services.claims import ClaimService

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="claimops-api", version="0.1.0")


@router.get(
    "/api/v1/claims",
    response_model=ClaimListResponse,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    tags=["claims"],
)
async def list_claims(
    query: Annotated[ClaimQuery, Query()],
    service: Annotated[ClaimService, Depends(get_claim_service)],
) -> ClaimListResponse:
    filters = ClaimFilters(
        search=query.search,
        partner=query.partner,
        product=query.product,
        claim_type=query.claim_type,
        status=query.status,
        stage=query.stage,
        assigned_agent=query.assigned_agent,
        sla_status=query.sla_status,
        risk_level=query.risk_level,
        documentation_status=query.documentation_status,
        minimum_risk_score=query.minimum_risk_score,
        missing_document=query.missing_document,
        created_from=query.created_from,
        created_to=query.created_to,
    )
    page = service.list_claims(filters=filters, limit=query.limit, cursor=query.cursor)
    return ClaimListResponse(items=page.items, next_cursor=page.next_cursor, total=page.total, limit=query.limit)


@router.get(
    "/api/v1/claims/{claim_id}",
    response_model=ClaimDetailResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["claims"],
)
async def get_claim(claim_id: str, service: Annotated[ClaimService, Depends(get_claim_service)]) -> ClaimDetailResponse:
    return ClaimDetailResponse.model_validate(service.get_claim(claim_id))


@router.get("/api/v1/actions", response_model=ActionQueueResponse, tags=["actions"])
async def list_actions(
    service: Annotated[ActionService, Depends(get_action_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    priority: Annotated[Literal["CRITICAL", "HIGH", "MEDIUM"] | None, Query()] = None,
) -> ActionQueueResponse:
    return ActionQueueResponse.model_validate(service.action_queue(limit, priority))


@router.post(
    "/api/v1/claims/{claim_id}/actions",
    response_model=ClaimActionResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    tags=["actions"],
)
async def execute_action(
    claim_id: str,
    payload: ClaimActionRequest,
    service: Annotated[ActionService, Depends(get_action_service)],
    actor: Annotated[str, Header(alias="X-Actor-Email", min_length=5, max_length=120)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=120)],
) -> ClaimActionResponse:
    result = service.execute(
        claim_id,
        ActionCommand(
            action=payload.action,
            expected_version=payload.expected_version,
            owner=payload.owner,
            documents=tuple(payload.documents),
            note=payload.note,
            resolution=payload.resolution,
        ),
        actor=actor,
        idempotency_key=idempotency_key,
    )
    return ClaimActionResponse(claim=result.claim, audit_event=result.audit_event, replayed=result.replayed)
