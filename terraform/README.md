# Terraform layout

`environments/dev` will compose reusable modules. A production environment can later use the same modules with separate state and variables.

| Module | Ownership |
|---|---|
| `api_gateway` | HTTP API routes, stages, access logs, throttling |
| `lambda` | Functions, layers/packages, permissions, async failure destinations |
| `dynamodb` | On-demand table, indexes, encryption, PITR settings |
| `s3` | Frontend and private report buckets, encryption, lifecycle, access blocks |
| `cloudfront` | SPA distribution, origin access control, security headers |
| `eventbridge` | Timezone-aware schedules and Lambda targets |
| `sns` | Operational alert topic and subscriptions |
| `ses` | Delivery configuration and event destinations |
| `iam` | Least-privilege execution and GitHub OIDC roles |
| `monitoring` | Log groups, metrics, dashboards, alarms, notifications |

Module outputs expose identifiers, not whole resources. Cross-module wiring occurs in the environment root. Provider configuration and remote state belong only in environment roots. Terraform resources begin in Phase 34.

