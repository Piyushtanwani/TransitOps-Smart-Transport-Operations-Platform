# CLAUDE.md — TransitOps Master Build Instructions

You are building **TransitOps**, a transport operations platform, for an 8-hour hiring hackathon judged on database design, code quality, modularity, validation, UI, and security. Read this file completely before writing any code.

## 1. What you are building

A monorepo web application:

- **Backend:** FastAPI (Python 3.11+) + SQLAlchemy 2.0 + Alembic + PostgreSQL 16. JWT auth with RBAC (4 roles). REST API under `/api/v1`.
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query + react-hook-form + zod + Recharts. Dark-first UI matching `docs/05-FRONTEND-SPEC.md`.
- **AI layer:** OpenRouter (OpenAI-compatible API) powering (a) an RBAC-aware, admin-configurable fleet chatbot with tool calling against live PostgreSQL data, and (b) an AI Trip Advisor for dispatch risk. Spec: `docs/06-AI-FEATURES.md`.
- **Everything persists in PostgreSQL** — entities, chat sessions/messages, AI settings, audit logs. Never localStorage for data (theme preference only).

## 2. Document map — read before the relevant work

| Before working on… | Read |
|---|---|
| Anything | `docs/00-PROJECT-BRIEF.md`, `docs/01-ARCHITECTURE.md` |
| Models, migrations, seed | `docs/02-DATABASE.md` (contains the exact DDL — do not deviate) |
| Endpoints, services, auth | `docs/03-API-SPEC.md`, `docs/04-BUSINESS-RULES.md` |
| UI screens, components | `docs/05-FRONTEND-SPEC.md` |
| Chatbot, Trip Advisor | `docs/06-AI-FEATURES.md` |
| Tests | `docs/07-TESTING.md` |
| Chatbot static context | `docs/10-AI-KNOWLEDGE-BASE.md` (paste verbatim in BE-13) |
| Docker, env, git | `docs/08-DEVOPS-GIT.md` |

## 3. Task protocol (mandatory)

1. Your tasks live in `tasks/TASKS-<N>-<NAME>-<AREA>.md`. Execute **top to bottom**; never start a task whose `Depends on` items are unchecked.
2. Each task lists **Deliverables**, **Definition of Done**, and a **Verify** command. Run Verify; only then mark `[ ]` → `[x]` in the task file **and** flip the row in `tasks/TASKS-OVERVIEW.md` to `DONE`.
3. Commit after every task using the exact commit message given in the task (Conventional Commits, e.g. `feat(db): vehicles + drivers tables with constraints [DB-03]`).
4. If blocked by a teammate's unfinished dependency, implement against the documented contract (DDL / OpenAPI shapes in docs) using the shared spec — the docs are the source of truth, not the other person's code.
5. Never silently change a contract (schema, endpoint shape, route path). If a change is unavoidable, update the relevant doc in the same commit and note it in `tasks/TASKS-OVERVIEW.md → Change Log`.

## 4. Repository layout (create exactly this)

```
transitops/
├── CLAUDE.md  README.md  .env.example  .gitignore
├── docker-compose.yml  Makefile
├── docs/  tasks/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py                # FastAPI app factory, CORS, routers, error handlers
│       ├── core/                  # config.py (pydantic-settings), security.py (JWT, bcrypt), deps.py (get_db, get_current_user, require_roles)
│       ├── db/                    # base.py, session.py, seed.py
│       ├── models/                # one file per entity (user.py, vehicle.py, driver.py, trip.py, maintenance.py, fuel_log.py, expense.py, chat.py, ai_settings.py, audit.py)
│       ├── schemas/               # pydantic v2 request/response schemas mirroring models
│       ├── services/              # business logic ONLY here (trip_service.py, maintenance_service.py, report_service.py, ai/…)
│       ├── api/v1/                # thin routers: auth.py, users.py, vehicles.py, drivers.py, trips.py, maintenance.py, fuel_logs.py, expenses.py, dashboard.py, reports.py, ai.py
│       └── tests/                 # conftest.py, factories.py, test_business_rules.py, test_auth_rbac.py, test_e2e_workflow.py, …
└── frontend/
    ├── package.json  vite.config.ts  tailwind.config.js  tsconfig.json
    └── src/
        ├── main.tsx  App.tsx  index.css
        ├── api/                   # client.ts (axios + interceptors), one module per resource
        ├── auth/                  # AuthContext.tsx, ProtectedRoute.tsx, RequireRole.tsx
        ├── components/ui/         # Button, Input, Select, Modal, Table, Badge, Card, Toast, EmptyState, Spinner, ConfirmDialog
        ├── components/layout/     # AppShell (Sidebar + Topbar), PageHeader
        ├── features/              # dashboard/ vehicles/ drivers/ trips/ maintenance/ expenses/ reports/ chat/ admin/
        ├── hooks/  lib/  types/
        └── router.tsx
```

## 5. Golden rules (violations = failed review)

1. **Layering:** routers stay thin (parse → call service → return schema). All business rules live in `services/`. No SQL in routers; no business logic in models.
2. **Business rules** in `docs/04-BUSINESS-RULES.md` are law. Status transitions happen **only** inside service functions within a single DB transaction, using `SELECT … FOR UPDATE` row locks on the vehicle and driver rows.
3. **Validation everywhere:** Pydantic on every request body (server) AND zod + react-hook-form on every form (client). Field-level errors surface next to inputs; API errors use the standard envelope in `docs/03-API-SPEC.md §2`.
4. **RBAC enforced server-side** via `require_roles(...)` dependencies per the matrix in `docs/03-API-SPEC.md §3`. The frontend hides what the role cannot do, but the API is the enforcement point. Chatbot tools re-check the same matrix.
5. **No banned tech:** Firebase, Supabase, MongoDB, hardcoded static JSON datasets, ORM-less string-formatted SQL. Secrets only via environment variables — never committed.
6. **Determinism before AI:** the Trip Advisor's hard validations are deterministic Python; the LLM only explains/summarizes. The app must fully function with `OPENROUTER_API_KEY` unset (AI features degrade gracefully to a disabled state with a helpful message).
7. **Tests are deliverables:** the 10 business-rule tests in `docs/07-TESTING.md` must pass (`make test`) before the Hour-6 checkpoint.
8. **Migrations only** for schema (Alembic). Seed via `make seed` (idempotent).

## 6. Commands (Makefile ships at repo root)

```
make up          # docker compose up -d (postgres) + install deps
make db-migrate  # alembic upgrade head
make seed        # python -m app.db.seed
make api         # uvicorn app.main:app --reload --port 8000
make web         # cd frontend && npm run dev  (port 5173)
make test        # cd backend && pytest -q
make lint        # ruff check backend && cd frontend && npm run lint
```

## 7. Environment

Copy `.env.example` → `.env`. Key vars: `DATABASE_URL`, `JWT_SECRET`, `JWT_ACCESS_TTL_MIN=30`, `JWT_REFRESH_TTL_DAYS=7`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`, `CORS_ORIGINS=http://localhost:5173`, `VITE_API_BASE_URL=http://localhost:8000/api/v1`.

## 8. Code style

- Python: ruff-clean, type hints everywhere, `snake_case`, docstrings on services explaining which business rule (BR-x) they enforce.
- TypeScript: strict mode, no `any`, `PascalCase` components, feature-folder colocation, shared API types in `src/types/` generated to mirror `docs/03-API-SPEC.md`.
- Seed data must be realistic Indian logistics data (see `docs/02-DATABASE.md §7`) — the demo runs on it.

## 9. Definition of shipped

`docker compose up` + `make db-migrate seed api web` yields: login as any of 4 seeded roles → live dashboard KPIs from PostgreSQL → full CRUD → trip lifecycle with every business rule enforced and human-readable errors → maintenance auto-status flow → fuel/expense logging → reports with charts + CSV export → chatbot answering role-scoped questions from live data → admin AI settings page → `pytest` green.
