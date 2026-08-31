# Tests

- `unit` — deterministic domain and KPI/report calculations
- `integration` — repository and AWS-adapter behavior
- `contract` — HTTP request/response and event schemas

Test fixtures are synthetic. Phase 2 introduces standard-library unit tests for generation determinism, required fields, SLA boundary behavior, designed operational variation, and explainable risk-score arithmetic.

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
