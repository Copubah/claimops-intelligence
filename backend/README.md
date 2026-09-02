# Backend

The Python backend will keep business rules independent from AWS integrations:

- `claimops/domain` — entities, value objects, policies, domain errors
- `claimops/services` — use cases and ports
- `claimops/repositories` — persistence interfaces and adapters
- `claimops/api` — transport schemas, routing, and authorization boundary

Lambda handlers in `/lambdas` remain thin composition roots. Phase 5 introduces the read-only Claims API with an in-memory repository adapter; DynamoDB arrives in Phase 6.

Phase 6 adds the executable DynamoDB claim mapper and read adapter. Local API composition still defaults to the in-memory adapter until AWS runtime configuration is introduced; no AWS call is made on import.

Set `CLAIMOPS_REPOSITORY=dynamodb`, `CLAIMOPS_TABLE_NAME`, and `CLAIMOPS_AWS_REGION` to select the DynamoDB adapter. The default remains `memory`; AWS credentials are never stored in application configuration.

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
- `GET /api/v1/actions`
- `POST /api/v1/claims/{claim_id}/actions`

List filters include partner, product, claim type, status, stage, agent, SLA status, risk level/minimum score, documentation status, missing-document type, and created-at range. Claim responses explicitly separate required, submitted, and missing documents. Results use opaque cursor pagination with a maximum page size of 100.

Action commands require `X-Actor-Email` and `Idempotency-Key` headers plus the claim's expected version. Local actions update the in-memory claim state; DynamoDB actions use a transactional claim-and-audit write. Recommendations never mutate claims automatically.

## Test

```bash
PYTHONPATH=backend:. pytest tests/api tests/unit -q
```
