class ClaimOpsError(Exception):
    """Base class for expected domain and application errors."""


class ClaimNotFoundError(ClaimOpsError):
    def __init__(self, claim_id: str) -> None:
        self.claim_id = claim_id
        super().__init__(f"Claim {claim_id} was not found")


class InvalidCursorError(ClaimOpsError):
    def __init__(self) -> None:
        super().__init__("The pagination cursor is invalid or expired")

