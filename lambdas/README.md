# Lambda entry points

Planned independently deployable entry points:

- `api` — versioned synchronous HTTP API
- `sla_monitor` — periodic SLA evaluation and transition alerts
- `report_generator` — manual and scheduled report generation
- `report_delivery` — archived report email delivery

Handlers will call shared backend services; domain rules must not live in handlers.

