#!/usr/bin/env python3
"""Build the Phase 4 overview fixture from deterministic synthetic claims."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from generate_claims import FINAL_STATUSES, STAGES, generate_claims, iso

SLA_ORDER = ("HEALTHY", "WATCH", "AT_RISK", "BREACHED")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def priority_for(claim: dict[str, Any]) -> tuple[str, str, str]:
    if claim["sla_status"] == "BREACHED":
        return "CRITICAL", "SLA breached", "Escalate and resolve the delayed stage"
    if claim["risk_score"] >= 60:
        return "CRITICAL", "Additional risk review required", "Complete manual review"
    if claim["sla_status"] == "AT_RISK":
        return "HIGH", "SLA at risk", "Prioritize before the deadline"
    if claim["assigned_agent"] is None:
        return "HIGH", "Claim is unassigned", "Assign an available agent"
    return "HIGH", f"Missing {claim['missing_documents'][0]}", "Request missing documentation"


def build_overview(claims: list[dict[str, Any]], as_of: datetime) -> dict[str, Any]:
    reference = as_of.astimezone(UTC)
    today = reference.date()
    final = [claim for claim in claims if claim["status"] in FINAL_STATUSES]
    open_claims = [claim for claim in claims if claim["status"] not in FINAL_STATUSES]
    approved = [claim for claim in final if claim["status"] == "Approved"]
    rejected = [claim for claim in final if claim["status"] == "Rejected"]
    received_today = [claim for claim in claims if parse_timestamp(claim["created_at"]).date() == today]
    finalized_today = [claim for claim in final if parse_timestamp(claim["updated_at"]).date() == today]
    completed_tat = [claim["tat_hours"] for claim in final if claim["tat_hours"] is not None]
    compliant = sum(claim["sla_status"] != "BREACHED" for claim in claims)

    metrics = {
        "received_today": len(received_today),
        "finalized_today": len(finalized_today),
        "pending": len(open_claims),
        "approved": len(approved),
        "rejected": len(rejected),
        "approval_rate": safe_rate(len(approved), len(final)),
        "average_tat_hours": round(sum(completed_tat) / len(completed_tat), 1) if completed_tat else 0.0,
        "sla_compliance": safe_rate(compliant, len(claims)),
        "sla_at_risk": sum(claim["sla_status"] == "AT_RISK" for claim in open_claims),
        "sla_breached": sum(claim["sla_status"] == "BREACHED" for claim in open_claims),
        "missing_documents": sum(bool(claim["missing_documents"]) for claim in open_claims),
        "documents_complete": sum(claim["documentation_status"] == "COMPLETE" for claim in open_claims),
        "risk_review": sum(claim["risk_score"] >= 60 for claim in open_claims),
        "unassigned": sum(claim["assigned_agent"] is None for claim in open_claims),
        "active_escalations": sum(claim["status"] == "Escalated" for claim in open_claims),
    }

    volume_trend = []
    for days_ago in range(13, -1, -1):
        target = today - timedelta(days=days_ago)
        volume_trend.append(
            {
                "date": target.strftime("%d %b"),
                "received": sum(parse_timestamp(claim["created_at"]).date() == target for claim in claims),
                "finalized": sum(parse_timestamp(claim["updated_at"]).date() == target for claim in final),
            }
        )

    sla_counts = Counter(claim["sla_status"] for claim in open_claims)
    sla_distribution = [{"status": status, "value": sla_counts[status]} for status in SLA_ORDER]
    stage_counts = Counter(claim["stage"] for claim in open_claims)
    pipeline = [{"stage": stage, "value": stage_counts[stage]} for stage in STAGES if stage != "Closed"]

    actionable = [
        claim for claim in open_claims
        if claim["sla_status"] in {"BREACHED", "AT_RISK"}
        or claim["risk_score"] >= 60
        or claim["assigned_agent"] is None
        or claim["missing_documents"]
    ]
    severity = {"BREACHED": 0, "AT_RISK": 1, "WATCH": 2, "HEALTHY": 3}
    actionable.sort(key=lambda claim: (severity[claim["sla_status"]], -claim["risk_score"], claim["sla_deadline"]))
    attention = []
    for claim in actionable[:7]:
        priority, issue, recommendation = priority_for(claim)
        attention.append(
            {
                "priority": priority,
                "claim_id": claim["claim_id"],
                "issue": issue,
                "stage": claim["stage"],
                "partner": claim["partner"],
                "owner": claim["assigned_agent"] or "Unassigned",
                "recommended_action": recommendation,
            }
        )

    return {
        "generated_at": iso(reference),
        "reference_date": today.isoformat(),
        "data_classification": "SYNTHETIC",
        "metrics": metrics,
        "volume_trend": volume_trend,
        "sla_distribution": sla_distribution,
        "pipeline": pipeline,
        "attention": attention,
    }


def write_fixture(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    as_of = datetime(2026, 8, 31, 12, tzinfo=UTC)
    claims = generate_claims(count=2000, seed=20260831, as_of=as_of)
    output = Path("frontend/public/data/overview.json")
    write_fixture(build_overview(claims, as_of), output)
    print(f"Wrote synthetic overview fixture to {output}")


if __name__ == "__main__":
    main()
