from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("build_overview_fixture", ROOT / "scripts" / "build_overview_fixture.py")
assert SPEC and SPEC.loader
overview = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(overview)


class OverviewFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.as_of = datetime(2026, 8, 31, 12, tzinfo=UTC)

    def test_safe_rate_handles_zero_denominator(self) -> None:
        self.assertEqual(overview.safe_rate(4, 0), 0.0)
        self.assertEqual(overview.safe_rate(3, 4), 75.0)

    def test_empty_period_produces_zero_metrics(self) -> None:
        payload = overview.build_overview([], self.as_of)
        self.assertTrue(all(value == 0 or value == 0.0 for value in payload["metrics"].values()))
        self.assertEqual(len(payload["volume_trend"]), 14)
        self.assertEqual(payload["attention"], [])
        self.assertEqual(payload["data_classification"], "SYNTHETIC")

    def test_baseline_snapshot_has_operational_content(self) -> None:
        claims = overview.generate_claims(2000, seed=20260831, as_of=self.as_of)
        payload = overview.build_overview(claims, self.as_of)
        self.assertEqual(payload["metrics"]["pending"] + payload["metrics"]["approved"] + payload["metrics"]["rejected"], 2000)
        self.assertGreater(payload["metrics"]["sla_breached"], 0)
        self.assertGreater(payload["metrics"]["missing_documents"], 0)
        self.assertGreater(payload["metrics"]["documents_complete"], 0)
        self.assertEqual(
            payload["metrics"]["documents_complete"] + payload["metrics"]["missing_documents"],
            payload["metrics"]["pending"],
        )
        self.assertEqual(len(payload["attention"]), 7)
        self.assertEqual(sum(item["value"] for item in payload["sla_distribution"]), payload["metrics"]["pending"])


if __name__ == "__main__":
    unittest.main()
