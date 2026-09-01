from typing import Annotated

from fastapi import APIRouter, Depends, Query

from claimops.api.dependencies import get_claim_service
from claimops.api.schemas import ClaimDetailResponse, ClaimListResponse, ClaimQuery, ErrorResponse, HealthResponse
from claimops.domain.types import ClaimFilters
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
