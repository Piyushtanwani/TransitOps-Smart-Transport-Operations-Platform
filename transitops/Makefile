.PHONY: up install db-migrate db-test-create db-reset seed api web test lint demo

up:            ## start postgres (persistent named volume)
	docker compose up -d db

install:       ## install backend + frontend dependencies
	cd backend && python3.12 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm install

db-migrate:    ## apply all alembic migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

db-test-create: ## create the test database (idempotent)
	docker exec transitops-db psql -U transitops -c "CREATE DATABASE transitops_test;" || true

db-reset:      ## drop + migrate + seed (demo restore) [DB-10]
	cd backend && . .venv/bin/activate && alembic downgrade base && alembic upgrade head && python -m app.db.seed --force

seed:          ## load the demo dataset
	cd backend && . .venv/bin/activate && python -m app.db.seed

api:           ## run fastapi with reload on :8000
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

web:           ## run vite dev server on :5173
	cd frontend && npm run dev

test:          ## backend test suites (A-E)
	cd backend && . .venv/bin/activate && pytest -q

lint:          ## ruff + eslint
	cd backend && . .venv/bin/activate && ruff check app
	cd frontend && npm run lint

demo: up db-migrate seed  ## one-command judge setup (then: make api / make web in two shells)
