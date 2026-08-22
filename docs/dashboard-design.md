# Analyst dashboard design

## Purpose

The dashboard turns stored risk assessments into an analyst workflow. It is designed for a five-minute hiring-demo narrative: see risk exposure, open a case, understand its evidence, run the bounded AI investigation, and make the final human decision.

## Screens and API mapping

| Area | User task | API source |
| --- | --- | --- |
| KPI overview | Monitor risk volume and review workload | `GET /dashboard/summary` |
| Risk distribution | Compare low, review, and high-risk exposure | `GET /dashboard/risk-distribution` |
| Priority queue | Select recent assessed cases | `GET /dashboard/recent-assessments` |
| Case explanation | Inspect score components and reasons | `GET /transactions/{id}/assessments/latest` |
| AI investigator | Request and inspect a structured recommendation | `POST /transactions/{id}/investigations` |
| Human control | Record final review and notes | `POST /transactions/{id}/reviews` |

## Interface principles

- Severity colors are reserved for decisions: green allow, amber manual review, red block.
- The score is always accompanied by its ML, rules, and anomaly components.
- AI output includes limitations beside the recommendation.
- The human decision control is visually separate and explicitly states that no action is automatic.
- Empty and disconnected states guide a demo operator to start the API and seed/assess data.

## Running the dashboard

Start the API on port 8000, then run `npm run dev` from `apps/web`. Use `VITE_API_URL` to point the dashboard at another API host if needed.
