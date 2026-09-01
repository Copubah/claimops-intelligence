from fastapi import Request

from claimops.services.claims import ClaimService


async def get_claim_service(request: Request) -> ClaimService:
    return request.app.state.claim_service
