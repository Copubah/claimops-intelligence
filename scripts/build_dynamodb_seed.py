#!/usr/bin/env python3
"""Create deterministic DynamoDB PutRequest fixtures without calling AWS."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from claimops.repositories.dynamodb import claim_to_item, serialize_item  # noqa: E402
from generate_claims import generate_claims  # noqa: E402


def build_requests(count: int, seed: int) -> list[dict[str, object]]:
    claims = generate_claims(count=count, seed=seed, as_of=datetime(2026, 8, 31, 12, tzinfo=UTC))
    return [{"PutRequest": {"Item": serialize_item(claim_to_item(claim))}} for claim in claims]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--output", type=Path, default=Path("data/generated/dynamodb-claims.json"))
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be at least 1")
    requests = build_requests(args.count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(requests, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(requests)} table-independent DynamoDB PutRequest objects to {args.output}")


if __name__ == "__main__":
    main()

