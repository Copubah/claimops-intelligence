# DynamoDB data model

## Table design

The planned on-demand table uses generic keys `PK` and `SK`, plus five sparse global secondary indexes. Every item includes `entity_type`, `created_at`, `updated_at`, and `schema_version`. Sensitive personal data is deliberately excluded. Five indexes avoid table scans for core claim access patterns; because DynamoDB is on-demand, the tradeoff is modest additional write/storage usage rather than idle capacity cost.

| Entity | PK | SK | Purpose |
|---|---|---|---|
| Claim | `CLAIM#<id>` | `META` | Current claim snapshot, version, SLA, assignment |
| Claim event/audit | `CLAIM#<id>` | `EVENT#<timestamp>#<event_id>` | Immutable state/action history |
| Missing document | `CLAIM#<id>` | `DOC#<doc_type>` | Request/reminder/follow-up state |
| Risk assessment | `CLAIM#<id>` | `RISK#<assessment_id>` | Score, rule signals, explanation, review state |
| QA review | `CLAIM#<id>` | `QA#<review_id>` | Sample result, categories, coaching notes |
| Action item | `ACTION#<action_id>` | `META` | Prioritized actionable queue item |
| Agent | `AGENT#<agent_id>` | `PROFILE` | Fictional operational identity and capacity |
| Partner | `PARTNER#<partner_id>` | `PROFILE` | Fictional partner metadata and targets |
| Report definition | `REPORTDEF#<id>` | `META` | Metrics, dimensions, filters, schedule, delivery |
| Report run | `REPORTDEF#<id>` | `RUN#<timestamp>#<run_id>` | Status, period, S3 key, checksum, failure summary |
| Subscription | `REPORTDEF#<id>` | `SUB#<subscription_id>` | Delivery channel and verified fictional recipient |
| Idempotency | `IDEMPOTENCY#<scope>` | `KEY#<key>` | Retry result with TTL |
| Alert transition | `CLAIM#<id>` | `ALERT#<alert_type>#<state>` | Deduplicates state-transition notifications |
| Daily aggregate | `METRIC#<date>` | `<dimension>#<value>` | Precomputed historical KPI slices |

## Access patterns and indexes

| Access pattern | Key/index strategy |
|---|---|
| Claim detail with history | Base table `PK = CLAIM#id` |
| All claims, newest first | GSI1 `CLAIMS` / `created_at#id` |
| Claims by SLA state/deadline | GSI2 `SLA#<state>` / `sla_deadline#id` |
| Claims by owner | GSI3 `AGENT#<id>` / `status#updated_at#id` |
| Partner backlog | GSI4 `PARTNER#<id>` / `status#created_at#id` |
| Claims by stage/status | GSI5 `STAGE#<stage>#<status>` / `updated_at#id` |

Other entities overload these index attributes only when their access patterns require them. For example, action items can use GSI1 `ACTION#OPEN`, reports can use GSI2 `REPORT#<type>`, and scheduled definitions can use GSI1 `REPORT_SCHEDULE#ENABLED`. Sparse keys mean unrelated entities do not consume entries in every index.

Claim items denormalize partner, owner, stage, and SLA attributes into sparse index keys. Index keys are updated transactionally with state. Large report files and verbose exports never go into DynamoDB.

## Executable Phase 6 mapping

`backend/claimops/repositories/dynamodb.py` is the canonical claim mapper and read adapter. It uses the low-level DynamoDB wire format so Lambda clients can be injected and tested without AWS access. Decimal conversion prevents unsupported floating-point writes. Unassigned claims omit GSI3 keys, making the agent index sparse.

Generate table-independent seed requests without contacting AWS:

```bash
PYTHONPATH=backend:. python3 scripts/build_dynamodb_seed.py
```

The ignored output contains one DynamoDB `PutRequest` per claim. A later deployment/seeding phase will batch these into groups of 25 and apply retry/backoff for unprocessed items.

## Integrity, retention, and concurrency

- Claim updates require `version = expected_version`, then increment the version.
- A transaction writes the new snapshot and its audit event atomically.
- Audit events and completed report metadata are immutable.
- Idempotency records and short-lived job locks use DynamoDB TTL; claims and audit history do not.
- SLA alert markers are keyed by claim, alert type, and entered state/version so repeated EventBridge invocations do not resend.
- Money is stored as integer minor units plus ISO currency; timestamps use UTC.
