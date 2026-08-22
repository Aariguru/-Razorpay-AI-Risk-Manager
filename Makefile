.PHONY: api-install api-test api-lint web-install web-test web-lint web-build up down

api-install:
	cd apps/api && python -m pip install -e ".[dev]"

api-test:
	cd apps/api && pytest

api-lint:
	cd apps/api && ruff check . && mypy app

web-install:
	cd apps/web && npm install

web-test:
	cd apps/web && npm run test

web-lint:
	cd apps/web && npm run lint

web-build:
	cd apps/web && npm run build

up:
	docker compose -f infra/compose.yaml up --build

down:
	docker compose -f infra/compose.yaml down
