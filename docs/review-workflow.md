# Analyst review and feedback workflow

## Human-in-the-loop decision flow

```text
Transaction → Risk assessment → Analyst review → Outcome label → Future evaluation/training
```

1. The risk engine stores an assessment with components and explanations.
2. An analyst records `allow`, `manual_review`, or `block` through the review API.
3. Optional feedback labels record the observed outcome: `confirmed_fraud`, `false_positive`, `legitimate`, or `insufficient_evidence`.
4. The review stays associated with the specific assessment model version, making overrides measurable and auditable.

## Dashboard-ready endpoints

- `GET /api/v1/dashboard/summary` — KPI cards and review queue count.
- `GET /api/v1/dashboard/risk-distribution` — low/review/high score buckets.
- `GET /api/v1/dashboard/recent-assessments` — recent transaction cases for a table/queue.

These APIs intentionally return read models rather than frontend-specific database records. The React analyst dashboard in Phase 6 will consume them directly.

## Important boundary

An API review is a simulated analyst workflow, not an instruction to block a real payment. Phase 5’s agent will recommend actions with evidence; Phase 6 will surface the final human control clearly in the interface.
