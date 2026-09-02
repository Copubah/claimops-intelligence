# SLA calculation engine

Phase 9 introduces a pure, timezone-aware domain engine in `backend/claimops/domain/sla.py`. It has no AWS, HTTP, or persistence dependency, so scheduled monitoring and the API can use the same tested rules.

## Default thresholds

| Remaining time | Status |
|---|---|
| More than 60 minutes | `HEALTHY` |
| 30 through 60 minutes, inclusive | `WATCH` |
| Zero through less than 30 minutes | `AT_RISK` |
| Deadline has passed | `BREACHED` |
| Deadline is missing | `UNKNOWN` |

Exactly at the deadline is `AT_RISK`; the claim becomes `BREACHED` immediately after it. Results separately expose non-negative `remaining_seconds` and `breached_by_seconds` to prevent ambiguous UI calculations.

Thresholds can be configured with `CLAIMOPS_SLA_AT_RISK_MINUTES` and `CLAIMOPS_SLA_WATCH_MINUTES`. The watch threshold must be greater than the at-risk threshold. All input datetimes must include a timezone and are normalized to UTC.

## Claim evaluation and transitions

Open claims are evaluated at the supplied observation time. Finalized claims use `updated_at` as their completion time, preventing a completed claim from appearing to accrue new breach time. Batch evaluation excludes finalized claims unless explicitly requested.

Each claim evaluation compares the calculated state with the stored `sla_status`. The transition result identifies whether the state changed and whether an alert is required. Only a new transition into `AT_RISK` or `BREACHED` requests an alert; repeated evaluation in the same state does not. Persistence and scheduled execution are reserved for Phase 11, and alert delivery for Phase 12.

