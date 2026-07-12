# 08 — DevOps, Environment & Git

## 1. docker-compose.yml (ships at repo root — authoritative copy; Postgres only, apps run natively for HMR speed)

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: transitops-db
    environment:
      POSTGRES_USER: transitops
      POSTGRES_PASSWORD: transitops
      POSTGRES_DB: transitops
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U transitops"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  pgdata: {}
```

Create the test DB once: `docker exec transitops-db psql -U transitops -c "CREATE DATABASE transitops_test;"` (Makefile target `db-test-create`). Named volume ⇒ **data persists across restarts** — say this when judges ask about persistence.

## 2. `.env.example` (copy to `.env`; backend reads via pydantic-settings, frontend via Vite `VITE_` prefix)

See the file at repo root. Never commit `.env`; `.gitignore` includes `.env`, `__pycache__/`, `.venv/`, `node_modules/`, `dist/`, `.pytest_cache/`.

## 3. Makefile (ships at repo root — authoritative copy, includes `db-reset`)

```makefile
up:            ## start postgres
	docker compose up -d db
install:       ## install backend+frontend deps
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm install
db-migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head
db-test-create:
	docker exec transitops-db psql -U transitops -c "CREATE DATABASE transitops_test;" || true
seed:
	cd backend && . .venv/bin/activate && python -m app.db.seed
api:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000
web:
	cd frontend && npm run dev
test:
	cd backend && . .venv/bin/activate && pytest -q
lint:
	cd backend && . .venv/bin/activate && ruff check app && cd ../frontend && npm run lint
demo: up db-migrate seed        ## one-command judge setup (then: make api / make web in two shells)
```

`backend/pyproject.toml` deps: `fastapi uvicorn[standard] sqlalchemy>=2 psycopg2-binary alembic pydantic>=2 pydantic-settings passlib[bcrypt] python-jose[cryptography] httpx python-multipart` · dev: `pytest ruff freezegun`.
`frontend/package.json` deps: `react react-dom react-router-dom @tanstack/react-query axios react-hook-form zod @hookform/resolvers recharts lucide-react clsx` · dev: `vite typescript tailwindcss postcss autoprefixer eslint prettier vitest`.

## 4. Git workflow (judges explicitly score this — "version control is a team sport")

- **Trunk-based, small commits.** Branch `main` protected by convention; each member works on short-lived branches `feat/db-03-vehicles`, `feat/be-07-trip-lifecycle`, `feat/fe-05-dashboard`, merges via fast PR or `--no-ff` merge after a teammate's 60-second review at sync points.
- **Conventional Commits with task IDs** — every task file specifies its exact commit message, e.g. `feat(api): trip lifecycle endpoints with BR-2..BR-8 [BE-07]`. Fixes: `fix(fe): map 409 CARGO_EXCEEDS_CAPACITY onto cargo field [FE-08]`.
- **Each member commits their own work under their own git identity** (`git config user.name/email` verified in Hour 0 — task *-01). Target: ≥ 8 commits per member spread across the 8 hours; never one bulk commit at the end.
- Commit generated lockfiles; never commit `.env` or `node_modules`.
- `README.md` at repo root gets a **Run it** section (Hour 7): prerequisites, `make demo`, `make api`, `make web`, the four demo logins, screenshot strip.

## 5. Ports & URLs

Postgres `localhost:5432` · API `http://localhost:8000` (`/docs` OpenAPI) · Web `http://localhost:5173`. CORS: exactly `http://localhost:5173`.

## 6. Troubleshooting quick refs

- `psycopg2` build issues → use `psycopg2-binary` (already pinned).
- Alembic can't find models → `alembic/env.py` imports `app.db.base` which imports **all** model modules.
- bcrypt/passlib version warning → pin `bcrypt<4.1` if passlib complains.
- Vite proxy alternative: not used; direct `VITE_API_BASE_URL` + CORS keeps it explicit.
- Windows teammates: run Make targets' underlying commands directly if `make` unavailable (each target is one line — copy/paste).
