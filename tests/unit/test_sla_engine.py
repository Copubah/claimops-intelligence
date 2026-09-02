from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from claimops.domain.sla import SlaConfig, SlaEngine, SlaStatus


NOW = datetime(2026, 8, 31, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (timedelta(minutes=60, seconds=1), SlaStatus.HEALTHY),
        (timedelta(minutes=60), SlaStatus.WATCH),
        (timedelta(minutes=30), SlaStatus.WATCH),
        (timedelta(minutes=29, seconds=59), SlaStatus.AT_RISK),
        (timedelta(0), SlaStatus.AT_RISK),
        (timedelta(microseconds=-1), SlaStatus.BREACHED),
    ],
)
def test_exact_threshold_boundaries(offset: timedelta, expected: SlaStatus) -> None:
    result = SlaEngine().evaluate(NOW + offset, NOW)
    assert result.status == expected


def test_missing_deadline_is_unknown() -> None:
    result = SlaEngine().evaluate(None, NOW)
    assert result.status == SlaStatus.UNKNOWN
    assert result.deadline is None
    assert result.remaining_seconds == 0
    assert result.breached_by_seconds == 0


def test_remaining_and_breach_durations_are_non_negative() -> None:
    healthy = SlaEngine().evaluate(NOW + timedelta(minutes=90), NOW)
    breached = SlaEngine().evaluate(NOW - timedelta(minutes=12), NOW)
    assert healthy.remaining_seconds == 5400
    assert healthy.breached_by_seconds == 0
    assert breached.remaining_seconds == 0
    assert breached.breached_by_seconds == 720


def test_iso_timestamp_and_timezone_offset_are_normalized() -> None:
    deadline = "2026-08-31T15:00:00+03:00"
    result = SlaEngine().evaluate(deadline, NOW.astimezone(timezone(timedelta(hours=3))))
    assert result.status == SlaStatus.AT_RISK
    assert result.deadline == NOW
    assert result.evaluated_at == NOW


@pytest.mark.parametrize("field", ["deadline", "as_of"])
def test_naive_datetimes_are_rejected(field: str) -> None:
    naive = datetime(2026, 8, 31, 12)
    with pytest.raises(ValueError, match="timezone-aware"):
        SlaEngine().evaluate(naive if field == "deadline" else NOW, naive if field == "as_of" else NOW)


def test_malformed_deadline_is_rejected() -> None:
    with pytest.raises(ValueError, match="ISO-8601"):
        SlaEngine().evaluate("not-a-date", NOW)


def test_custom_thresholds_and_configuration_validation() -> None:
    engine = SlaEngine(SlaConfig(at_risk_minutes=15, watch_minutes=45))
    assert engine.evaluate(NOW + timedelta(minutes=20), NOW).status == SlaStatus.WATCH
    assert engine.evaluate(NOW + timedelta(minutes=10), NOW).status == SlaStatus.AT_RISK
    assert SlaConfig.from_environment(
        {"CLAIMOPS_SLA_AT_RISK_MINUTES": "20", "CLAIMOPS_SLA_WATCH_MINUTES": "50"}
    ) == SlaConfig(20, 50)
    with pytest.raises(ValueError, match="greater"):
        SlaConfig(at_risk_minutes=60, watch_minutes=60)
    with pytest.raises(ValueError, match="negative"):
        SlaConfig(at_risk_minutes=-1, watch_minutes=60)


def test_claim_transition_requires_alert_only_on_new_exposure() -> None:
    claim = {
        "claim_id": "CLM-28001",
        "status": "Pending",
        "sla_status": "WATCH",
        "sla_deadline": (NOW + timedelta(minutes=10)).isoformat(),
        "updated_at": NOW.isoformat(),
    }
    transition = SlaEngine().evaluate_claim(claim, NOW)
    assert transition.changed is True
    assert transition.previous_status == SlaStatus.WATCH
    assert transition.evaluation.status == SlaStatus.AT_RISK
    assert transition.alert_required is True
    claim["sla_status"] = "AT_RISK"
    assert SlaEngine().evaluate_claim(claim, NOW).alert_required is False


def test_final_claim_uses_completion_time_and_never_alerts() -> None:
    claim = {
        "claim_id": "CLM-28002",
        "status": "Approved",
        "sla_status": "BREACHED",
        "sla_deadline": "2026-08-31T12:00:00Z",
        "updated_at": "2026-08-31T11:59:00Z",
    }
    transition = SlaEngine().evaluate_claim(claim, NOW + timedelta(days=3))
    assert transition.evaluation.status == SlaStatus.AT_RISK
    assert transition.evaluation.is_final is True
    assert transition.alert_required is False


def test_batch_defaults_to_open_claims_and_keeps_missing_sla() -> None:
    claims = [
        {"claim_id": "CLM-1", "status": "Pending", "sla_status": None, "sla_deadline": None},
        {
            "claim_id": "CLM-2", "status": "Rejected", "sla_status": "HEALTHY",
            "sla_deadline": NOW.isoformat(), "updated_at": NOW.isoformat(),
        },
    ]
    transitions = SlaEngine().evaluate_claims(claims, NOW)
    assert len(transitions) == 1
    assert transitions[0].evaluation.status == SlaStatus.UNKNOWN
    assert len(SlaEngine().evaluate_claims(claims, NOW, include_final=True)) == 2

