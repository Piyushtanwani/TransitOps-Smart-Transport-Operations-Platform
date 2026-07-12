# TASKS — Overview & Live Progress Board

**Protocol (from CLAUDE.md §3):** work strictly in order within your file · respect `Depends on` · run the task's Verify · mark `[x]` in your file **and** flip Status here to `DONE` · commit with the task's exact message. If a contract must change, update the doc in the same commit and add a row to the Change Log.

## 1. Sections & ownership

| Section | Owner | File | Scope |
|---|---|---|---|
| 1 — Database | **Afif** | `TASKS-1-AFIF-DATABASE.md` | PostgreSQL, models, constraints, migrations, seed, schema tests, KPI/report SQL |
| 2 — Backend | **Ismail** | `TASKS-2-ISMAIL-BACKEND.md` | FastAPI, auth+RBAC, services (business rules), endpoints, AI layer, test suites |
| 3 — Frontend | **Piyush** | `TASKS-3-PIYUSH-FRONTEND.md` | Design system, shell, all screens, forms+validation, charts, chat UI, polish |

## 2. Progress board (single source of truth — keep current!)

| ID | Task | Owner | Status |
|---|---|---|---|
| DB-01 | Postgres via compose + test DB + git identity | Afif | DONE |
| DB-02 | DB wiring: config, session, base, enums | Afif | DONE |
| DB-03 | Models: users, vehicles, drivers | Afif | DONE |
| DB-04 | Models: trips, maintenance, fuel, expenses (+partial indexes) | Afif | DONE |
| DB-05 | Models: ai_settings, chat, audit | Afif | DONE |
| DB-06 | Alembic init + `0001_initial_schema` + schema.sql | Afif | DONE |
| DB-07 | Idempotent seed with demo dataset | Afif | TODO |
| DB-08 | Suite D: schema-constraint tests | Afif | TODO |
| DB-09 | `db/queries.py`: KPI + report SQL functions | Afif | TODO |
| DB-10 | DB ops: reset target, index review, EXPLAIN notes | Afif | TODO |
| BE-01 | Backend scaffold: pyproject, app skeleton, health, Makefile | Ismail | DONE |
| BE-02 | Core: settings, security (JWT/bcrypt), deps, error framework | Ismail | TODO |
| BE-03 | Auth endpoints: login / refresh / me (+tests) | Ismail | TODO |
| BE-04 | Users CRUD (FM) + `require_roles` | Ismail | TODO |
| BE-05 | Vehicles CRUD + retire/unretire + `dispatchable` | Ismail | TODO |
| BE-06 | Drivers CRUD + status + expiring + `assignable` | Ismail | TODO |
| BE-07 | Trip service + lifecycle endpoints (BR-2…BR-8) | Ismail | TODO |
| BE-08 | Maintenance service + endpoints (BR-9, BR-10) | Ismail | TODO |
| BE-09 | Fuel logs + expenses endpoints | Ismail | TODO |
| BE-10 | Dashboard KPIs + charts endpoints | Ismail | TODO |
| BE-11 | Reports endpoint + CSV export | Ismail | TODO |
| BE-12 | GATE: Suites A/B/C green | Ismail | TODO |
| BE-13 | AI: client, knowledge/context, settings API | Ismail | TODO |
| BE-14 | AI: tool registry + chat loop + sessions | Ismail | TODO |
| BE-15 | AI: Trip Advisor endpoint | Ismail | TODO |
| BE-16 | (T2) MCP server over tool registry | Ismail | TODO |
| FE-01 | Vite scaffold + Tailwind tokens + fonts + theme toggle | Piyush | TODO |
| FE-02 | Mockup fidelity review + ui/ component kit | Piyush | TODO |
| FE-03 | API client + AuthContext + router guards + Login | Piyush | TODO |
| FE-04 | App shell: sidebar (role-filtered) + topbar | Piyush | TODO |
| FE-05 | Dashboard: KPIs, filters, alert banner, charts | Piyush | TODO |
| FE-06 | Vehicles: table, form modal, detail, retire | Piyush | TODO |
| FE-07 | Drivers: table, form, status actions, expiry badges | Piyush | TODO |
| FE-08 | Trips: list + New Trip form (live capacity check) | Piyush | TODO |
| FE-09 | Trip lifecycle UI: dispatch/complete/cancel | Piyush | TODO |
| FE-10 | Maintenance page | Piyush | TODO |
| FE-11 | Fuel & Expenses page | Piyush | TODO |
| FE-12 | Reports page + CSV download | Piyush | TODO |
| FE-13 | Admin: Users page | Piyush | TODO |
| FE-14 | Chat widget | Piyush | TODO |
| FE-15 | Admin: AI Settings + Trip Advisor panel | Piyush | TODO |
| FE-16 | Polish gate: states audit, responsive, QA checklist, README | Piyush | TODO |

## 3. Cross-section dependency graph (contract-first: build against docs/03 shapes when a dependency lags; integrate at checkpoints)

```
DB-01 → BE-01 → BE-02 → BE-03 ─┬→ BE-04 … BE-11 → BE-12 → BE-13 → BE-14 → BE-15 → (BE-16)
DB-02..06 ─────────────────────┤        ▲                     ▲
DB-07 (seed) → manual login ───┘   DB-09 (queries) ──────► BE-10/11
FE-01 → FE-02 → FE-03 ──(needs BE-03 live or spec-stub)──► FE-04 → FE-05..13 (pair with BE-05..11)
FE-14/15 need BE-13..15 · FE-16 last
```

## 4. 8-hour timeline & sync checkpoints (all three sync 5 min at each ✓)

| Clock | Afif | Ismail | Piyush |
|---|---|---|---|
| 0:00–0:30 | DB-01 | BE-01 | FE-01 |
| 0:30–2:00 | DB-02→04 | BE-02→03 | FE-02→03 |
| **✓ CP1 @ 2:00** | *Migration applied (DB-06 started), login E2E with a seeded user (mini-seed ok), shell renders* |||
| 2:00–4:00 | DB-05→07 | BE-04→07 | FE-04→06 |
| **✓ CP2 @ 4:00** | *Full seed in; vehicles+drivers E2E; trip lifecycle passing Suite A locally* |||
| 4:00–5:30 | DB-08→09 | BE-08→11 | FE-07→09 |
| **✓ CP3 @ 5:30** | *T0 complete end-to-end; BE-12 gate green; DB-10* |||
| 5:30–7:00 | DB-10 + assist QA | BE-13→15 | FE-10→15 |
| **✓ CP4 @ 7:00 — FEATURE FREEZE** | *AI demo works; only FE-16/fixes/(BE-16 if all green) beyond this line* |||
| 7:00–8:00 | Demo-reset script check | `make test` final, README run section | FE-16, QA checklist, rehearse (docs/09) |

## 5. Change log (append-only)

| When | Who | What changed | Docs updated |
|---|---|---|---|
| BE-01 | Ismail | Makefile `install` target uses `python3.12` (host `python` is 3.9; project needs 3.11+). No contract change. | – |
| BE-01 | Ismail | DB section (DB-02..DB-09) was unstarted; per CLAUDE.md §3.4 the backend owner implements it against `docs/02` (frozen DDL) to unblock BE tasks. Committed under the DB task messages, DB rows flipped as delivered. | – |
