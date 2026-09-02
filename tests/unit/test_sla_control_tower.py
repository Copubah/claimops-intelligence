from datetime import UTC, datetime, timedelta

from claimops.repositories.memory import InMemoryClaimRepository
from claimops.services.sla import SlaControlTowerService


NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


def claim(claim_id: str, minutes: int, *, partner: str = "AfriCredit", status: str = "Pending") -> dict:
    return {
        "claim_id": claim_id, "status": status, "stage": "Assessment", "partner": partner,
        "assigned_agent": None, "sla_deadline": (NOW + timedelta(minutes=minutes)).isoformat(),
        "sla_status": "HEALTHY", "updated_at": NOW.isoformat(),
    }


def test_snapshot_summarizes_open_claims_and_excludes_final_claims() -> None:
    repository = InMemoryClaimRepository([
        claim("CLM-10001", 90), claim("CLM-10002", 45), claim("CLM-10003", 10),
        claim("CLM-10004", -15), claim("CLM-10005", -20, status="Closed"),
    ])
    result = SlaControlTowerService(repository).snapshot(as_of=NOW)
    assert result["total_open"] == 4
    assert result["summary"] == {"healthy": 1, "watch": 1, "at_risk": 1, "breached": 1, "unknown": 0}
    assert [item["status"] for item in result["items"]] == ["BREACHED", "AT_RISK", "WATCH", "HEALTHY"]
    assert result["items"][0]["breached_by_seconds"] == 900


def test_snapshot_filters_without_changing_portfolio_summary() -> None:
    repository = InMemoryClaimRepository([
        claim("CLM-10001", -30, partner="AfriCredit"),
        claim("CLM-10002", -10, partner="MobiFund"),
        claim("CLM-10003", 20, partner="AfriCredit"),
    ])
    result = SlaControlTowerService(repository).snapshot(status="BREACHED", partner="africredit", as_of=NOW)
    assert result["total_open"] == 3
    assert result["summary"]["breached"] == 2
    assert result["total_matching"] == 1
    assert result["items"][0]["claim_id"] == "CLM-10001"
