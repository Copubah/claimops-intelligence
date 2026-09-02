from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


SCRIPT = Path(__file__).parents[2] / "scripts" / "generate_claims.py"
SPEC = importlib.util.spec_from_file_location("generate_claims", SCRIPT)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class SyntheticClaimsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.as_of = datetime(2026, 8, 31, 12, tzinfo=UTC)

    def test_sla_threshold_edges(self) -> None:
        self.assertEqual(generator.sla_status(self.as_of + timedelta(minutes=61), self.as_of), "HEALTHY")
        self.assertEqual(generator.sla_status(self.as_of + timedelta(minutes=60), self.as_of), "WATCH")
        self.assertEqual(generator.sla_status(self.as_of + timedelta(minutes=30), self.as_of), "WATCH")
        self.assertEqual(generator.sla_status(self.as_of + timedelta(minutes=29, seconds=59), self.as_of), "AT_RISK")
        self.assertEqual(generator.sla_status(self.as_of, self.as_of), "AT_RISK")
        self.assertEqual(generator.sla_status(self.as_of - timedelta(seconds=1), self.as_of), "BREACHED")
        self.assertEqual(generator.sla_status(None, self.as_of), "UNKNOWN")

    def test_generation_is_deterministic(self) -> None:
        first = generator.generate_claims(50, seed=7, as_of=self.as_of)
        second = generator.generate_claims(50, seed=7, as_of=self.as_of)
        self.assertEqual(first, second)

    def test_required_fields_and_unique_ids(self) -> None:
        claims = generator.generate_claims(2000, as_of=self.as_of)
        required = {
            "claim_id", "created_at", "updated_at", "partner", "product", "claim_type",
            "status", "stage", "amount", "assigned_agent", "sla_deadline", "sla_status",
            "required_documents", "submitted_documents", "missing_documents", "documentation_status",
            "risk_score", "rejection_reason", "approval_status",
            "tat_hours", "qa_score", "version", "risk_review_status", "notes",
        }
        self.assertEqual(len(claims), 2000)
        self.assertEqual(len({claim["claim_id"] for claim in claims}), 2000)
        self.assertTrue(all(required <= claim.keys() for claim in claims))
        self.assertTrue(all(claim["data_classification"] == "SYNTHETIC" for claim in claims))

    def test_operational_variation_is_present(self) -> None:
        claims = generator.generate_claims(2000, as_of=self.as_of)
        sla_states = {claim["sla_status"] for claim in claims}
        self.assertTrue({"HEALTHY", "WATCH", "AT_RISK", "BREACHED"} <= sla_states)
        self.assertTrue(any(claim["missing_documents"] for claim in claims))
        self.assertTrue(any(claim["documentation_status"] == "COMPLETE" for claim in claims))
        self.assertTrue(any(claim["documentation_status"] == "INCOMPLETE" for claim in claims))
        for claim in claims:
            self.assertEqual(
                set(claim["required_documents"]),
                set(claim["submitted_documents"]) | set(claim["missing_documents"]),
            )
            self.assertFalse(set(claim["submitted_documents"]) & set(claim["missing_documents"]))
        self.assertTrue(any(claim["risk_score"] >= 60 and claim["risk_signals"] for claim in claims))
        self.assertTrue(any(claim["status"] == "Rejected" and claim["rejection_reason"] for claim in claims))
        self.assertTrue(any(claim["assigned_agent"] is None for claim in claims))
        self.assertGreater(sum(claim["stage"] == "Document Review" for claim in claims), 300)

    def test_risk_score_matches_explanation(self) -> None:
        claims = generator.generate_claims(300, as_of=self.as_of)
        for claim in claims:
            expected = min(100, sum(signal["points"] for signal in claim["risk_signals"]))
            self.assertEqual(claim["risk_score"], expected)

    def test_invalid_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "count"):
            generator.generate_claims(0, as_of=self.as_of)


if __name__ == "__main__":
    unittest.main()
