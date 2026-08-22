# AI Risk Manager

An agentic payment-risk intelligence demo for the Razorpay AI Builder challenge. It uses **synthetic and public-compatible data only** and does not connect to, represent, or claim access to Razorpay private systems, APIs, or internal data.

## What this project will demonstrate

- Explainable, hybrid ML and rules-based payment risk scoring
- Suspicious-pattern detection and structured AI investigations
- An analyst-oriented operations dashboard
- A documented FastAPI backend and React dashboard
- Reproducible tests, containers, and CI checks

## Current status

Phase 6 is complete: the responsive analyst dashboard presents live risk KPIs, distribution, a case queue, explainable score details, bounded agent investigations, and the human review workflow.

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (optional, for the full local stack)

### Run locally

```bash
# API
cd apps/api
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Web app (in another terminal)
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`. API health and OpenAPI documentation are at `http://localhost:8000/health` and `http://localhost:8000/docs`.

### Environment and CORS

Copy the root `.env.example` and adjust the local values as needed. The API reads `DATABASE_URL`, `APP_ENV`, `AGENT_PROVIDER`, and `OPENAI_API_KEY` via the configuration layer. The frontend continues to use `VITE_API_BASE_URL` / `VITE_API_URL`.

The backend CORS policy is intentionally limited to localhost and IPv4/IPv6 loopback origins, so Vite can move between ports like `5173`, `5174`, etc., without accepting arbitrary external origins.

### Generate safe demo data

```bash
cd apps/api
python scripts/generate_synthetic_data.py --count 250
```

The command writes reproducible JSONL records to `data/synthetic/transactions.jsonl`. These records contain tokenized, fictional values only.

### Database migration

```bash
cd apps/api
alembic upgrade head
```

### Run with Docker

```bash
docker compose -f infra/compose.yaml up --build
```

## Repository layout

```text
apps/api       FastAPI backend
apps/web       React + TypeScript dashboard
docs           Architecture, model, and demo documentation
infra          Docker Compose and deployment foundations
.github        CI workflow
```

## Development commands

```bash
# Backend (from apps/api)
ruff check .
mypy app
pytest

# Frontend (from apps/web)
npm run lint
npm run test
npm run build
```

## Safety and data boundary

The product must never ingest or persist raw card numbers, CVVs, or credentials. Its demo data will be synthetic and use tokenized identifiers. Agent recommendations are decision support: human review and policy controls remain part of the intended workflow.

## Roadmap

1. Foundation — completed
2. Synthetic data, schema, migrations, and ingestion — completed
3. Explainable hybrid risk engine — completed
4. Analyst APIs, review workflow, and feedback capture — completed
5. AI investigation agent with bounded tools — completed
6. Professional analyst dashboard — completed
4. Analyst APIs and review workflow
5. AI investigation agent with bounded tools
6. Dashboard and visual analytics
7. E2E testing, deployment, and five-minute demo polish

See [docs/architecture.md](docs/architecture.md) and [docs/demo-script.md](docs/demo-script.md) for the intended end state.
