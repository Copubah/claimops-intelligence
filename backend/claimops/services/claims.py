from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from claimops.domain.errors import ClaimNotFoundError, InvalidCursorError
from claimops.domain.types import ClaimFilters
from claimops.repositories.claims import ClaimRepository


@dataclass(frozen=True, slots=True)
class ClaimPage:
    items: list[dict[str, Any]]
    next_cursor: str | None
    total: int


class ClaimService:
    def __init__(self, repository: ClaimRepository) -> None:
        self._repository = repository

    def list_claims(self, filters: ClaimFilters, limit: int, cursor: str | None = None) -> ClaimPage:
        claims = [dict(claim) for claim in self._repository.list_all() if self._matches(claim, filters)]
        claims.sort(key=lambda claim: (claim["created_at"], claim["claim_id"]), reverse=True)
        offset = self._decode_cursor(cursor) if cursor else 0
        if offset > len(claims):
            raise InvalidCursorError()
        page_items = claims[offset:offset + limit]
        next_offset = offset + len(page_items)
        next_cursor = self._encode_cursor(next_offset) if next_offset < len(claims) else None
        return ClaimPage(items=page_items, next_cursor=next_cursor, total=len(claims))

    def get_claim(self, claim_id: str) -> dict[str, Any]:
        claim = self._repository.get(claim_id.upper())
        if claim is None:
            raise ClaimNotFoundError(claim_id.upper())
        return dict(claim)

    @staticmethod
    def _matches(claim: Mapping[str, Any], filters: ClaimFilters) -> bool:
        exact_filters = {
            "partner": filters.partner,
            "product": filters.product,
            "claim_type": filters.claim_type,
            "status": filters.status,
            "stage": filters.stage,
            "assigned_agent": filters.assigned_agent,
            "sla_status": filters.sla_status,
            "risk_level": filters.risk_level,
        }
        for field, expected in exact_filters.items():
            if expected is not None and str(claim.get(field, "")).casefold() != expected.casefold():
                return False
        if filters.minimum_risk_score is not None and int(claim.get("risk_score", 0)) < filters.minimum_risk_score:
            return False
        if filters.missing_document is not None:
            missing = [str(document).casefold() for document in claim.get("missing_documents", [])]
            if filters.missing_document.casefold() not in missing:
                return False
        created_at = datetime.fromisoformat(str(claim["created_at"]).replace("Z", "+00:00"))
        if filters.created_from is not None and created_at < filters.created_from:
            return False
        if filters.created_to is not None and created_at > filters.created_to:
            return False
        return True

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(f"claims:{offset}".encode()).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> int:
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode()).decode()
            prefix, raw_offset = decoded.split(":", maxsplit=1)
            if prefix != "claims":
                raise ValueError
            offset = int(raw_offset)
            if offset < 0:
                raise ValueError
            return offset
        except (ValueError, UnicodeDecodeError, binascii.Error) as error:
            raise InvalidCursorError() from error

