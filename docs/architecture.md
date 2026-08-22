# Architecture

## Phase 1 boundary

The current codebase is a modular monolith: a React client calls a FastAPI service. The service currently exposes platform metadata and health endpoints only. This intentional thin slice provides stable contracts before risk logic is added.

## Target architecture

```text
React analyst dashboard
          |
          v
FastAPI application
  |-- transaction and review APIs
  |-- hybrid risk-scoring service
  |     |-- ML probability
  |     |-- deterministic rules
  |     `-- anomaly signals
  |-- explainability service
  `-- bounded AI investigation agent
          |
          v
PostgreSQL + model artifacts + background workers
```

## Design principles

- Synthetic or public-compatible data only; no private Razorpay data or APIs.
- No raw cardholder data: identifiers are tokenized in the proposed data model.
- Deterministic, stored scoring components and model versions for auditability.
- The agent has restricted read/investigate tools and returns structured advice; it does not execute payment actions.
- Human analyst decisions and overrides are first-class audit events.

## Service boundaries planned for later phases

| Module | Responsibility |
| --- | --- |
| `services` | Transactions, assessments, reviews, and dashboard aggregates |
| `ml` | Feature engineering, model inference, calibration, evaluation |
| `rules` | Transparent policy and behavioral rules |
| `agents` | Tool-bounded investigation and structured recommendations |
| `db` | Persistence, migrations, repository layer, audit records |

## API contract conventions

All future endpoints will be versioned beneath `/api/v1`, validated with Pydantic schemas, and documented automatically through OpenAPI. Error responses will include a stable machine-readable code and correlation-ready request identifier.
