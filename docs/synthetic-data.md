# Synthetic claims dataset

The Phase 2 generator creates deterministic fictional operational data. It contains no customer names, contact details, policy numbers, addresses, government identifiers, or source data from an insurer. Partner, agent, facility, product, and claim identifiers are invented.

## Generate the baseline dataset

```bash
python3 scripts/generate_claims.py
```

This writes 2,000 JSON records to `data/generated/claims.json`. Generated output is intentionally ignored by Git because it is reproducible. Use a fixed seed and reference timestamp to reproduce a run:

```bash
python3 scripts/generate_claims.py \
  --count 2000 \
  --seed 20260831 \
  --as-of 2026-08-31T12:00:00+00:00 \
  --format json \
  --output data/generated/claims.json
```

CSV is also supported with `--format csv --output data/generated/claims.csv`. Nested document and risk explanations are JSON-encoded inside CSV cells.

## Designed variation

The generator deliberately creates all SLA bands, missing-document follow-ups, explainable high-risk review cases, rejections, unassigned open claims, uneven agent workloads, partner-specific patterns, and excess Document Review volume. These patterns exist to make future operational views meaningful; they are not real business rules or fraud determinations.

Every record contains `data_classification: SYNTHETIC`. Amounts use KES and are fictional. Generation is deterministic for the same count, seed, and reference timestamp.

