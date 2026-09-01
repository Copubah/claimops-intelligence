"""Claim repository ports and adapters."""

from .claims import ClaimRepository
from .memory import InMemoryClaimRepository

__all__ = ["ClaimRepository", "InMemoryClaimRepository"]

