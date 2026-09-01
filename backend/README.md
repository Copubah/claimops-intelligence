# Backend

The Python backend will keep business rules independent from AWS integrations:

- `claimops/domain` — entities, value objects, policies, domain errors
- `claimops/services` — use cases and ports
- `claimops/repositories` — persistence interfaces and adapters
- `claimops/api` — transport schemas, routing, and authorization boundary

Lambda handlers in `/lambdas` remain thin composition roots. Phase 5 introduces the read-only Claims API with an in-memory repository adapter; DynamoDB arrives in Phase 6.

## Run locally

From the repository root:

```bash
python3 scripts/generate_claims.py
PYTHONPATH=backend uvicorn claimops.api.app:app --reload --port 8000
```

Open `http://localhost:8000/docs`. The API loads `data/generated/claims.json` when present and otherwise generates the same deterministic fictional portfolio in memory.

## Endpoints

- `GET /health`
- `GET /api/v1/claims`
- `GET /api/v1/claims/{claim_id}`

List filters include partner, product, claim type, status, stage, agent, SLA status, risk level/minimum score, documentation status, missing-document type, and created-at range. Claim responses explicitly separate required, submitted, and missing documents. Results use opaque cursor pagination with a maximum page size of 100.

## Test

```bash
PYTHONPATH=backend:. pytest tests/api tests/unit -q
```
