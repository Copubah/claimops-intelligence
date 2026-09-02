from fastapi import Request

from claimops.services.claims import ClaimService
from claimops.services.actions import ActionService
from claimops.services.sla import SlaControlTowerService


async def get_claim_service(request: Request) -> ClaimService:
    return request.app.state.claim_service


async def get_action_service(request: Request) -> ActionService:
    return request.app.state.action_service


async def get_sla_service(request: Request) -> SlaControlTowerService:
    return request.app.state.sla_service
