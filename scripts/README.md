# Scripts

`generate_claims.py` creates the deterministic fictional dataset introduced in Phase 2. It uses only the Python standard library and never reads credentials or external customer data.

```bash
python3 scripts/generate_claims.py
python3 scripts/generate_claims.py --help
```

See [`docs/synthetic-data.md`](../docs/synthetic-data.md) for the schema intent and reproducibility options.

`build_dynamodb_seed.py` transforms the same claims into low-level DynamoDB `PutRequest` objects without contacting AWS:

```bash
PYTHONPATH=backend:. python3 scripts/build_dynamodb_seed.py
```
