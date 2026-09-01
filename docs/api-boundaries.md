# API boundaries

All domain routes are rooted at `/api/v1`. Phase 5 formalizes validated claim schemas, opaque cursor pagination, bounded page sizes, filter composition, request correlation IDs, and structured error envelopes. Authorization is added with the command surface in later phases.

Errors use `{ "error": { "code", "message", "request_id", "details" } }`. Clients may send `X-Request-ID`; otherwise the API creates one and returns it in the response header.

## Read APIs

| Route | Purpose |
|---|---|
| `GET /overview` | Above-the-fold KPIs and action summary |
| `GET /claims` | Filtered claim search |
| `GET /claims/{claim_id}` | Claim, documents, risks, QA, and timeline |
| `GET /actions` | Priority Action Center queue |
| `GET /sla` | SLA status distribution and exposed claims |
| `GET /pipeline` | Stage counts, baselines, bottlenecks |
| `GET /agents` | Workload and performance summaries |
| `GET /partners` | Partner performance summaries |
| `GET /risk-reviews` | Explainable review queue |
| `GET /qa` | QA trends, errors, and coaching opportunities |
| `GET /analytics` | Time-series and aging/rejection analysis |
| `GET /alerts` | Operational alert history |
| `GET /reports` | Searchable report-run archive |
| `GET /reports/{run_id}` | Report metadata and authorized download URL |
| `GET /report-definitions` | Reusable report definitions and schedules |

## Command APIs

| Route | Purpose |
|---|---|
| `POST /claims/{id}/actions` | Assign, reassign, escalate, request documents, follow up, note, resolve, review |
| `POST /risk-reviews/{id}/decision` | Record manual review outcome |
| `POST /reports/generations` | Start an authorized one-time report run |
| `POST /report-definitions` | Create a reusable custom definition |
| `PATCH /report-definitions/{id}` | Update definition, schedule, or delivery |
| `POST /reports/{run_id}/deliveries` | Retry/trigger authorized delivery |

Commands require an `Idempotency-Key`, actor context, expected entity version where relevant, and an action-specific authorization scope. The API returns `409` for stale versions or conflicting transitions and never accepts actor identity from an untrusted request body.

## Internal event contracts

Scheduled payloads contain `event_id`, `job_type`, `scheduled_at`, `timezone`, `definition_id` when applicable, and `schema_version`. Domain events include correlation and causation IDs. Notification providers implement a small adapter contract so SNS can later be joined by Slack or Teams without changing domain services.

## Frontend boundary

The SPA calls only the public API service layer in `frontend/src/services`. Feature components do not import AWS SDKs or persistence details. Server state, authorization failures, loading states, empty states, and stale-write conflicts are handled consistently by shared app infrastructure.
