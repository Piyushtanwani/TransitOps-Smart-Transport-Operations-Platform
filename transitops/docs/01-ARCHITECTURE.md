# 01 — Architecture

## 1. System overview

```
┌──────────────────────────┐        HTTPS/JSON         ┌───────────────────────────────┐
│  React 18 + TS (Vite)    │  ───────────────────────▶ │  FastAPI  /api/v1             │
│  Tailwind · TanStack Q   │ ◀───────────────────────  │  ┌ routers (thin)             │
│  RHF + zod · Recharts    │      access JWT (Bearer)  │  ├ services (business rules)  │
│  Chat widget             │                           │  ├ schemas (pydantic v2)      │
└──────────────────────────┘                           │  └ models (SQLAlchemy 2.0)    │
                                                       └──────────┬───────────┬────────┘
                                                                  │           │ tool calls
                                                        SQL (txn, │           ▼
                                                        row locks)│   ┌───────────────────┐
                                                                  ▼   │ OpenRouter API    │
                                                       ┌──────────────┤ (chat completions │
                                                       │ PostgreSQL 16│  + function/tool  │
                                                       │ (Docker)     │  calling)         │
                                                       └──────────────┴───────────────────┘
```

Single deployable backend; the AI layer is a service module inside it (`app/services/ai/`), not a separate process. All state — domain data, chat history, AI configuration, audit trail — lives in PostgreSQL.

## 2. Tech stack + one-line rationale (judges ask "why")

| Layer | Choice | Why (say this in Q&A) |
|---|---|---|
| DB | **PostgreSQL 16** (Docker) | Local relational DB per judging brief; ENUMs, CHECKs, **partial unique indexes** let us enforce business invariants in the schema itself. |
| Migrations | **Alembic** | Versioned schema = reviewable database design; `alembic upgrade head` reproduces the DB anywhere. |
| ORM | **SQLAlchemy 2.0, sync + psycopg2** | Parameterized, typed, mature. Sync chosen deliberately over async: zero event-loop pitfalls under an 8-hour clock; FastAPI runs sync endpoints in a threadpool, ample for demo load. Documented tradeoff. |
| API | **FastAPI + Pydantic v2** | Auto OpenAPI docs (live at `/docs` — show judges), first-class validation, dependency injection for auth/RBAC. |
| Auth | **JWT access (30 min) + refresh (7 d), bcrypt via passlib** | Stateless, standard; refresh rotation endpoint; role claim embedded, re-verified against DB each request. |
| Frontend | **React 18 + TypeScript + Vite** | Fast HMR for hackathon speed; strict TS = fewer runtime bugs. |
| Server state | **TanStack Query** | Cache + `invalidateQueries` after mutations ⇒ dashboard/tables always reflect DB (the "real-time dynamic data" criterion) without websockets. |
| Forms | **react-hook-form + zod** | Client validation mirrors Pydantic; instant, human-readable field errors. |
| Styling | **Tailwind CSS + hand-rolled ui/ kit** | Consistent token system, no heavyweight component lib to fight; dark-first per mockup. |
| Charts | **Recharts** | Declarative, fast to compose the 3 analytics charts. |
| AI | **OpenRouter** (OpenAI-compatible `/chat/completions`) | One key, many models; admin can swap model at runtime from the DB-backed settings page. |
| Tests | **pytest + FastAPI TestClient + SQLite-free (Postgres test schema)** | Business rules proven executable; `test_e2e_workflow.py` replays the brief's 9-step example. |

## 3. Request lifecycle (canonical write path)

`POST /api/v1/trips/{id}/dispatch` →
1. Router: parse path/body → `Depends(require_roles("fleet_manager","driver"))` resolves current user (JWT decode → DB user fetch → active check).
2. Service `trip_service.dispatch(db, trip_id, actor)` opens one transaction:
   - `SELECT trip FOR UPDATE`, `SELECT vehicle FOR UPDATE`, `SELECT driver FOR UPDATE` (lock ordering: trip → vehicle → driver, always, to avoid deadlocks).
   - Re-validate every business rule (BR-2…BR-6) against locked rows.
   - Mutate statuses (trip→dispatched, vehicle→on_trip, driver→on_trip), stamp `dispatched_at`, `start_odometer`.
   - Write `audit_logs` row.
3. Commit. Any rule failure → raise `DomainError(code, message, field?)` → global handler maps to HTTP 409/422 with the standard envelope.
4. Frontend mutation `onSuccess` → `invalidateQueries(['trips','vehicles','drivers','kpis'])` → UI updates everywhere.

## 4. Module responsibilities

- `app/core/config.py` — pydantic-settings `Settings` (env-driven, cached).
- `app/core/security.py` — `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`.
- `app/core/deps.py` — `get_db` (session per request), `get_current_user`, `require_roles(*roles)` factory.
- `app/core/errors.py` — `DomainError`, `NotFoundError`, exception handlers producing the §2 envelope of the API spec.
- `app/services/*` — the only home of business logic; every function docstring cites the BR-ids it enforces.
- `app/services/ai/context.py` — assembles chatbot system prompt (project summary + live KPIs + role permissions).
- `app/services/ai/tools.py` — tool registry (name, JSON schema, allowed_roles, executor fn).
- `app/services/ai/chat.py` — OpenRouter loop: send → if tool_calls, execute permitted tools → send results → final answer; persists messages.
- `frontend/src/api/client.ts` — axios instance; request interceptor injects access token; response interceptor: on 401 once, call `/auth/refresh`, retry; on failure, hard logout.
- `frontend/src/auth/AuthContext.tsx` — user + tokens in memory; refresh token in `localStorage` (documented tradeoff; httpOnly cookies noted as the production hardening step).

## 5. Key definitions (single source of truth)

- **Active Vehicles** = status ≠ `retired`.
- **Fleet Utilization %** = vehicles `on_trip` ÷ Active Vehicles × 100 (0 if none active).
- **Drivers On Duty** = status ∈ {`available`, `on_trip`}.
- **Pending Trips** = status `draft`; **Active Trips** = status `dispatched`.
- **Actual distance** = `end_odometer − start_odometer` (on completion). **Fuel efficiency (vehicle)** = Σ actual distance of completed trips ÷ Σ liters (all fuel logs). Show `—` when liters = 0.
- **Operational cost (vehicle)** = Σ fuel_logs.cost + Σ maintenance.cost (+ expenses of type shown separately in reports; brief defines op-cost as Fuel + Maintenance — follow the brief, list "Other expenses" as its own column).
- **ROI (vehicle)** = (Σ trips.revenue − operational cost) ÷ acquisition_cost. Guard: acquisition_cost > 0 enforced by schema.

## 6. Scalability & security story (for Q&A, not to build)

Stateless API ⇒ horizontal scale behind a load balancer; Postgres read replicas for reports; pagination + indexes already in place; JWT means no session store. Next hardening steps we would take: httpOnly refresh cookies + CSRF token, rate limiting (slowapi), async SQLAlchemy for high concurrency, S3-backed document storage, background worker (RQ) for email reminders. Being able to *name* these precisely scores "scalability" without burning hackathon hours.
