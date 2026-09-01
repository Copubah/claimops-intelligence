#!/usr/bin/env python3
"""Generate deterministic, fictional ClaimOps insurance claim data."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

PARTNERS = ("AfriCredit", "MobiFund", "FarmTrust", "QuickFinance", "Horizon Bank")
PRODUCTS = ("Family Health", "Income Guard", "Hospital Cash", "Accident Assist")
CLAIM_TYPES = ("Medical", "Accident", "Hospitalization", "Income Protection")
AGENTS = (
    "Agent Amina",
    "Agent Baraka",
    "Agent Chao",
    "Agent Deka",
    "Agent Eshe",
    "Agent Femi",
    "Agent Gita",
    "Agent Hamisi",
)
FACILITIES = tuple(f"Fictional Facility {letter}" for letter in "ABCDEFGH")
STAGES = ("Submitted", "Document Review", "Verification", "Assessment", "Approval", "Payment", "Closed")
DOCUMENTS = ("Identification", "Invoice", "Discharge summary", "Medical report", "Claim form", "Supporting documents")
REQUIRED_DOCUMENTS = {
    "Medical": ("Identification", "Invoice", "Medical report", "Claim form"),
    "Accident": ("Identification", "Invoice", "Medical report", "Claim form", "Supporting documents"),
    "Hospitalization": ("Identification", "Invoice", "Discharge summary", "Medical report", "Claim form"),
    "Income Protection": ("Identification", "Claim form", "Supporting documents"),
}
REJECTION_REASONS = (
    "Incomplete documentation",
    "Benefit not covered",
    "Policy inactive",
    "Duplicate submission",
    "Eligibility requirements not met",
)
RISK_RULES = (
    ("duplicate_document_fingerprint", "Duplicate document fingerprint", 25),
    ("date_inconsistency", "Date inconsistency", 20),
    ("unusual_claim_frequency", "Unusual claim frequency", 18),
    ("duplicate_invoice_reference", "Duplicate invoice reference", 22),
    ("document_metadata_anomaly", "Document metadata anomaly", 15),
    ("amount_anomaly", "Amount anomaly", 13),
    ("unusual_facility_pattern", "Unusual facility pattern", 16),
)
FINAL_STATUSES = frozenset(("Approved", "Rejected", "Closed"))


def iso(value: datetime) -> str:
    """Return a UTC ISO-8601 timestamp with a Z suffix."""
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sla_status(deadline: datetime | None, as_of: datetime) -> str:
    """Classify an SLA using the documented ClaimOps thresholds."""
    if deadline is None:
        return "UNKNOWN"
    remaining_minutes = (deadline - as_of).total_seconds() / 60
    if remaining_minutes < 0:
        return "BREACHED"
    if remaining_minutes < 30:
        return "AT_RISK"
    if remaining_minutes <= 60:
        return "WATCH"
    return "HEALTHY"


def weighted_choice(rng: random.Random, values: Iterable[tuple[str, float]]) -> str:
    choices, weights = zip(*values)
    return rng.choices(choices, weights=weights, k=1)[0]


def make_risk_assessment(rng: random.Random, force_high: bool) -> tuple[int, list[dict[str, Any]], str]:
    signal_count = rng.choices((0, 1, 2, 3, 4), weights=(44, 29, 16, 8, 3), k=1)[0]
    if force_high:
        signal_count = rng.randint(4, 5)
    selected = rng.sample(RISK_RULES, k=min(signal_count, len(RISK_RULES)))
    signals = [{"rule_id": rule_id, "explanation": explanation, "points": points} for rule_id, explanation, points in selected]
    score = min(100, sum(signal["points"] for signal in signals))
    recommendation = "MANUAL_REVIEW" if score >= 60 else "REVIEW_IF_NEEDED" if score >= 30 else "NO_ADDITIONAL_REVIEW"
    return score, signals, recommendation


def make_missing_documents(
    rng: random.Random,
    created_at: datetime,
    as_of: datetime,
    forced: bool,
    required_documents: tuple[str, ...],
) -> tuple[list[str], list[dict[str, Any]]]:
    missing_count = rng.choices((0, 1, 2, 3), weights=(70, 20, 8, 2), k=1)[0]
    if forced:
        missing_count = max(1, missing_count)
    names = rng.sample(required_documents, k=min(missing_count, len(required_documents)))
    follow_ups: list[dict[str, Any]] = []
    for name in names:
        requested_at = min(as_of, created_at + timedelta(hours=rng.randint(1, 30)))
        reminders = rng.randint(0, 3)
        last_reminder = requested_at + timedelta(hours=24 * reminders) if reminders else None
        next_follow_up = (last_reminder or requested_at) + timedelta(hours=24)
        follow_ups.append(
            {
                "document_type": name,
                "date_requested": iso(requested_at),
                "reminder_count": reminders,
                "last_reminder": iso(min(last_reminder, as_of)) if last_reminder else None,
                "next_follow_up": iso(max(next_follow_up, as_of + timedelta(hours=1))),
                "status": "REMINDER_SENT" if reminders else "REQUESTED",
            }
        )
    return names, follow_ups


def generate_claims(count: int = 2000, seed: int = 20260831, as_of: datetime | None = None) -> list[dict[str, Any]]:
    """Return deterministic synthetic claims; no real people or claim data are used."""
    if count < 1:
        raise ValueError("count must be at least 1")
    rng = random.Random(seed)
    reference = (as_of or datetime(2026, 8, 31, 12, tzinfo=UTC)).astimezone(UTC)
    claims: list[dict[str, Any]] = []

    for index in range(1, count + 1):
        claim_id = f"CLM-{28000 + index:05d}"
        created_at = reference - timedelta(minutes=rng.randint(5, 90 * 24 * 60))
        partner = rng.choice(PARTNERS)
        claim_type = rng.choice(CLAIM_TYPES)
        product = rng.choice(PRODUCTS)

        # Deliberate operational patterns: FarmTrust documentation delays,
        # MobiFund rejection pressure, and a Document Review bottleneck.
        stage_weights = (8, 30 if partner == "FarmTrust" else 22, 16, 15, 10, 8, 21)
        stage = rng.choices(STAGES, weights=stage_weights, k=1)[0]
        if stage == "Closed":
            final_weights = (("Approved", 60), ("Rejected", 40)) if partner == "MobiFund" else (("Approved", 75), ("Rejected", 25))
            status = weighted_choice(rng, final_weights)
        else:
            status = weighted_choice(rng, (("Pending", 72), ("In Review", 21), ("Escalated", 7)))

        duration_hours = max(1, int((reference - created_at).total_seconds() / 3600))
        final = status in FINAL_STATUSES
        tat_hours = round(rng.uniform(2, min(240, max(3, duration_hours))), 2) if final else None
        updated_at = min(reference, created_at + timedelta(hours=tat_hours or rng.uniform(1, min(72, duration_hours))))

        if final:
            deadline = created_at + timedelta(hours=rng.choice((24, 48, 72)))
            current_sla = "HEALTHY" if updated_at <= deadline else "BREACHED"
        else:
            forced_band = index % 20
            if forced_band == 0:
                deadline = reference - timedelta(minutes=rng.randint(1, 720))
            elif forced_band == 1:
                deadline = reference + timedelta(minutes=rng.randint(1, 29))
            elif forced_band == 2:
                deadline = reference + timedelta(minutes=rng.randint(30, 60))
            else:
                deadline_band = weighted_choice(rng, (("BREACHED", 10), ("AT_RISK", 8), ("WATCH", 12), ("HEALTHY", 70)))
                if deadline_band == "BREACHED":
                    deadline = reference - timedelta(minutes=rng.randint(1, 720))
                elif deadline_band == "AT_RISK":
                    deadline = reference + timedelta(minutes=rng.randint(1, 29))
                elif deadline_band == "WATCH":
                    deadline = reference + timedelta(minutes=rng.randint(30, 60))
                else:
                    deadline = reference + timedelta(minutes=rng.randint(61, 72 * 60))
            current_sla = sla_status(deadline, reference)

        force_docs = partner == "FarmTrust" and index % 3 == 0
        required_documents = REQUIRED_DOCUMENTS[claim_type]
        missing_documents, document_follow_up = make_missing_documents(
            rng, created_at, reference, force_docs and not final, required_documents
        )
        submitted_documents = [document for document in required_documents if document not in missing_documents]
        force_risk = index % 37 == 0
        risk_score, risk_signals, risk_recommendation = make_risk_assessment(rng, force_risk)
        assigned_agent = None if (not final and index % 17 == 0) else rng.choices(AGENTS, weights=(24, 20, 15, 12, 9, 8, 7, 5), k=1)[0]
        rejection_reason = rng.choice(REJECTION_REASONS) if status == "Rejected" else None
        approval_status = status.upper().replace(" ", "_") if final else "PENDING"
        qa_score = rng.randint(72, 100) if final and index % 3 == 0 else None
        amount = round(rng.lognormvariate(8.2, 0.75), 2)

        claims.append(
            {
                "claim_id": claim_id,
                "created_at": iso(created_at),
                "updated_at": iso(updated_at),
                "partner": partner,
                "product": product,
                "claim_type": claim_type,
                "status": status,
                "stage": stage,
                "amount": amount,
                "currency": "KES",
                "assigned_agent": assigned_agent,
                "facility": rng.choice(FACILITIES),
                "sla_deadline": iso(deadline),
                "sla_status": current_sla,
                "required_documents": list(required_documents),
                "submitted_documents": submitted_documents,
                "missing_documents": missing_documents,
                "documentation_status": "COMPLETE" if not missing_documents else "INCOMPLETE",
                "document_follow_up": document_follow_up,
                "risk_score": risk_score,
                "risk_level": "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW",
                "risk_signals": risk_signals,
                "risk_recommendation": risk_recommendation,
                "rejection_reason": rejection_reason,
                "approval_status": approval_status,
                "tat_hours": tat_hours,
                "qa_score": qa_score,
                "data_classification": "SYNTHETIC",
            }
        )
    return claims


def write_json(claims: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(claims, indent=2) + "\n", encoding="utf-8")


def write_csv(claims: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=claims[0].keys())
        writer.writeheader()
        for claim in claims:
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value for key, value in claim.items()})


def summarize(claims: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "claims": len(claims),
        "partners": dict(sorted(Counter(claim["partner"] for claim in claims).items())),
        "stages": dict(sorted(Counter(claim["stage"] for claim in claims).items())),
        "sla_statuses": dict(sorted(Counter(claim["sla_status"] for claim in claims).items())),
        "missing_document_claims": sum(bool(claim["missing_documents"]) for claim in claims),
        "complete_document_claims": sum(claim["documentation_status"] == "COMPLETE" for claim in claims),
        "high_risk_claims": sum(claim["risk_level"] == "HIGH" for claim in claims),
        "rejected_claims": sum(claim["status"] == "Rejected" for claim in claims),
        "unassigned_open_claims": sum(claim["assigned_agent"] is None and claim["status"] not in FINAL_STATUSES for claim in claims),
        "synthetic_only": all(claim["data_classification"] == "SYNTHETIC" for claim in claims),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--as-of", default="2026-08-31T12:00:00+00:00", help="ISO-8601 reference time")
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output", type=Path, default=Path("data/generated/claims.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    as_of = datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
    if as_of.tzinfo is None:
        raise SystemExit("--as-of must include a timezone offset")
    claims = generate_claims(count=args.count, seed=args.seed, as_of=as_of)
    (write_json if args.format == "json" else write_csv)(claims, args.output)
    print(json.dumps(summarize(claims), indent=2))
    print(f"Wrote {len(claims)} synthetic claims to {args.output}")


if __name__ == "__main__":
    main()
