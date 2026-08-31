# DynamoDB data model

## Table design

The planned on-demand table uses generic keys `PK` and `SK`, plus sparse `GSI1PK/GSI1SK`, `GSI2PK/GSI2SK`, and `GSI3PK/GSI3SK`. Every item includes `entity_type`, `created_at`, `updated_at`, and `schema_version`. Sensitive personal data is deliberately excluded.

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
| Claims by stage/status, newest first | GSI1 `CLAIM_STAGE#<stage>#<status>` / `created_at#id` |
| Claims by SLA state/deadline | GSI2 `SLA#<state>` / `sla_deadline#id` |
| Claims by owner | GSI3 `AGENT#<id>` / `status#updated_at#id` |
| Action queue by priority | GSI1 `ACTION#OPEN` / `<severity>#<due_at>#id` |
| Partner backlog | GSI3 `PARTNER#<id>` / `status#created_at#id` |
| Reports by type and run time | GSI2 `REPORT#<type>` / `created_at#run_id` |
| Scheduled definitions due | GSI1 `REPORT_SCHEDULE#ENABLED` / `next_run_at#id` |

Claim items denormalize partner, owner, stage, and SLA attributes into sparse index keys. Index keys are updated transactionally with state. Large report files and verbose exports never go into DynamoDB.

## Integrity, retention, and concurrency

- Claim updates require `version = expected_version`, then increment the version.
- A transaction writes the new snapshot and its audit event atomically.
- Audit events and completed report metadata are immutable.
- Idempotency records and short-lived job locks use DynamoDB TTL; claims and audit history do not.
- SLA alert markers are keyed by claim, alert type, and entered state/version so repeated EventBridge invocations do not resend.
- Money is stored as integer minor units plus ISO currency; timestamps use UTC.

