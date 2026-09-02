from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from claimops import __version__
from claimops.api.routes import router
from claimops.domain.errors import ClaimNotFoundError, InvalidActionError, InvalidCursorError, VersionConflictError
from claimops.repositories.memory import InMemoryClaimRepository
from claimops.repositories.claims import ClaimRepository
from claimops.repositories.dynamodb import DynamoClaimRepository
from claimops.services.claims import ClaimService
from claimops.services.actions import ActionService
from claimops.services.sla import SlaControlTowerService


def load_local_claims() -> list[dict[str, Any]]:
    path = Path(os.getenv("CLAIMOPS_DATA_PATH", "data/generated/claims.json"))
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("CLAIMOPS_DATA_PATH must contain a JSON array")
        return payload
    try:
        from scripts.generate_claims import generate_claims
    except ImportError as error:
        raise RuntimeError(
            "Synthetic data is unavailable. Run scripts/generate_claims.py or set CLAIMOPS_DATA_PATH."
        ) from error
    return generate_claims(count=2000, seed=20260831)


def create_app(claims: Iterable[Mapping[str, Any]] | None = None) -> FastAPI:
    application = FastAPI(
        title="ClaimOps Intelligence API",
        description="Operational claims API backed exclusively by fictional synthetic data.",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    repository = create_claim_repository(claims)
    application.state.claim_service = ClaimService(repository)
    application.state.action_service = ActionService(repository)
    application.state.sla_service = SlaControlTowerService(repository)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID", "X-Actor-Email", "Idempotency-Key"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @application.exception_handler(ClaimNotFoundError)
    async def claim_not_found(request: Request, error: ClaimNotFoundError) -> JSONResponse:
        return error_response(request, 404, "CLAIM_NOT_FOUND", str(error))

    @application.exception_handler(InvalidCursorError)
    async def invalid_cursor(request: Request, error: InvalidCursorError) -> JSONResponse:
        return error_response(request, 400, "INVALID_CURSOR", str(error))

    @application.exception_handler(InvalidActionError)
    async def invalid_action(request: Request, error: InvalidActionError) -> JSONResponse:
        return error_response(request, 400, "INVALID_ACTION", str(error))

    @application.exception_handler(VersionConflictError)
    async def version_conflict(request: Request, error: VersionConflictError) -> JSONResponse:
        return error_response(request, 409, "VERSION_CONFLICT", str(error))

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        details = [
            {"location": ".".join(str(part) for part in item["loc"]), "message": item["msg"], "type": item["type"]}
            for item in error.errors()
        ]
        return error_response(request, 422, "VALIDATION_ERROR", "Request validation failed", details)

    application.include_router(router)
    return application


def create_claim_repository(claims: Iterable[Mapping[str, Any]] | None = None) -> ClaimRepository:
    if claims is not None:
        return InMemoryClaimRepository(claims)
    adapter = os.getenv("CLAIMOPS_REPOSITORY", "memory").strip().lower()
    if adapter == "memory":
        return InMemoryClaimRepository(load_local_claims())
    if adapter == "dynamodb":
        import boto3

        table_name = os.getenv("CLAIMOPS_TABLE_NAME", "").strip()
        if not table_name:
            raise RuntimeError("CLAIMOPS_TABLE_NAME is required when CLAIMOPS_REPOSITORY=dynamodb")
        region = os.getenv("CLAIMOPS_AWS_REGION", "af-south-1")
        return DynamoClaimRepository(boto3.client("dynamodb", region_name=region), table_name)
    raise RuntimeError(f"Unsupported CLAIMOPS_REPOSITORY: {adapter}")


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id, "details": details}},
        headers={"X-Request-ID": request_id},
    )


app = create_app()
