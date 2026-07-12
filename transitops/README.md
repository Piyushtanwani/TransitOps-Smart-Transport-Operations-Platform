# TransitOps — Smart Transport Operations Platform

A full-stack fleet management system for logistics companies: vehicles, drivers, trip
dispatching, maintenance, fuel & expenses, analytics, and an AI copilot — everything
persisted in PostgreSQL, every business rule enforced server-side.

**Stack:** FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Alembic · React 18 + TypeScript ·
Vite · Tailwind CSS · TanStack Query · Recharts · OpenRouter (AI)

---

## Quickstart

Prerequisites: Docker, Python 3.11+, Node 18+.

```bash
# 1. Start PostgreSQL + install dependencies
make up
make install

# 2. Create schema and load the demo fleet
make db-migrate
make seed

# 3. Run (two shells)
make api     # FastAPI on http://localhost:8000  (Swagger at /docs)
make web     # React on   http://localhost:5173
```

Copy `.env.example` → `.env` first and set a real `JWT_SECRET`.
One-shot setup: `make demo` (starts DB, migrates, seeds).

### Demo logins (password for all: `Transit@123`)

| Email | Role | Can do |
|---|---|---|
| manager@transitops.in | Fleet Manager | Everything — fleet, users, AI settings |
| dispatch@transitops.in | Driver / Dispatcher | Create, dispatch, complete & cancel trips, log fuel |
| safety@transitops.in | Safety Officer | Driver compliance, licences, suspensions |
| finance@transitops.in | Financial Analyst | Expenses, reports, ROI, CSV export |

---

## What it does

- **Vehicle registry** — unique registrations, capacity, odometer, regions, retire/unretire
  lifecycle. Deleting a vehicle with history is blocked; retiring is the paved path.
- **Driver management** — licence categories and expiry tracking, safety scores,
  suspension workflow. Expired or suspended drivers can never be assigned to a trip.
- **Trip dispatching** — draft → dispatched → completed/cancelled state machine with row
  locks and partial unique indexes, so double-dispatching a vehicle or driver is
  impossible even under concurrent requests. Odometer rolls forward on completion, with
  an optional linked fuel log.
- **Maintenance** — opening a job pulls the vehicle out of the dispatch pool
  automatically; closing it returns the vehicle to service.
- **Fuel & expenses** — per-vehicle logs with validation and role-gated access.
- **Dashboard & reports** — live KPIs (utilization, active trips, drivers on duty),
  14-day trip chart, cost breakdown, per-vehicle fuel efficiency / operational cost /
  ROI, one-click CSV export.

### The 10 business rules

Registration/licence uniqueness · no retired or in-shop vehicles in dispatch ·
no expired/suspended drivers · no double-dispatch (DB-enforced) · cargo ≤ capacity ·
dispatch flips vehicle+driver to on-trip · completion restores them and rolls the
odometer · cancelling a dispatched trip restores both · opening maintenance sets
in-shop · closing restores availability unless retired.

All ten are enforced in service-layer transactions with `SELECT … FOR UPDATE`, and the
critical ones again by the database itself (partial unique indexes, CHECK constraints).

---

## AI features (OpenRouter)

Configure entirely from the UI: **Settings → AI** lets a Fleet Manager toggle the
assistant, pick a model, tune temperature/tokens, edit the system prompt, manage the
per-role tool permission grid, and **paste an OpenRouter API key** — stored in the
database (never echoed back). Without a key, every AI surface degrades gracefully
instead of breaking.

- **Fleet chatbot** — role-aware assistant with 9 read-only tools against live data
  (KPIs, vehicles, drivers, trips, maintenance, costs, fuel efficiency…). A driver
  asking for ROI gets a polite refusal; tool calls are shown as chips for transparency;
  every conversation is persisted.
- **Trip Advisor** — deterministic risk checks (capacity, licence, availability,
  utilization %, safety score, service overdue) with a go/caution/block verdict and an
  LLM-written recommendation when configured. Advisory only; responds in milliseconds.
- **Daily Ops Briefing** — one-screen morning summary: fleet status, expiring licences,
  open workshop jobs, worst-ROI vehicles, live trips.
- **Maintenance Risk Ranking** — explainable per-vehicle service-risk scores.
- **Expense Anomaly Detection** — flags fuel-price outliers (median-band), duplicate
  same-day expenses, and unusually large spends.
- **MCP server** — `backend/mcp_server.py` exposes the same tool registry over the
  Model Context Protocol, so Claude Desktop (or any MCP client) can query the fleet.

---

## Testing

```bash
make test    # 133 tests: business rules, RBAC sweep, schema constraints, e2e, AI
make lint    # ruff + eslint
```

The e2e suite replays the full lifecycle — register vehicle → register driver → create
trip → dispatch → complete with fuel → open/close maintenance → verify the report math —
and prints its narration (`pytest -q -k e2e -s`).

---

## Security & production posture

- JWT auth (30-min access + 7-day refresh with rotation), bcrypt cost 12
- Server-side RBAC on every endpoint — the UI hides what the API already forbids
- Friendly, field-targeted errors in one consistent envelope; unhandled errors return a
  clean 500 without leaking internals
- Login brute-force lockout (429 after repeated failures), security headers, gzip,
  CORS allowlist, parameterized queries only, paginated lists capped at 100
- Secrets only via environment / DB — never in git

## Project structure

```
backend/
  app/
    api/v1/      # thin routers (auth, vehicles, drivers, trips, maintenance, …)
    core/        # config, security (JWT/bcrypt), deps (RBAC), error envelope
    db/          # engine, queries, seed, canonical schema.sql
    models/      # SQLAlchemy models mirroring the DDL
    schemas/     # Pydantic request/response models
    services/    # ALL business logic, incl. services/ai/ (chat, advisor, insights)
    tests/       # pytest suites A–E
  alembic/       # migrations
  mcp_server.py  # optional MCP exposure of the AI tool registry
frontend/
  src/
    api/ auth/ components/ features/ hooks/ lib/ types/
docs/            # architecture, API spec, business rules, DB design, testing
```
