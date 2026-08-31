# Backend

The Python backend will keep business rules independent from AWS integrations:

- `claimops/domain` — entities, value objects, policies, domain errors
- `claimops/services` — use cases and ports
- `claimops/repositories` — persistence interfaces and adapters
- `claimops/api` — transport schemas, routing, and authorization boundary

Lambda handlers in `/lambdas` remain thin composition roots. No backend runtime is implemented in Phase 1.

