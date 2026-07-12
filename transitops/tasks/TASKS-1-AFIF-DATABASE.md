# SECTION 1 — DATABASE · Owner: **Afif**

Read first: `CLAUDE.md`, `docs/02-DATABASE.md` (your spec — the DDL there is law), `docs/04-BUSINESS-RULES.md §1`, `docs/08-DEVOPS-GIT.md`.
Protocol: execute top-to-bottom · run **Verify** · tick `[x]` here · flip the row in `TASKS-OVERVIEW.md` · commit with the exact message.
You own the judges' **top criterion**. Your demo moment is scripted in `docs/09 §Minute 3–4.5`.

---

## [ ] DB-01 — Postgres up, test DB, git identity
**Depends on:** —
**Deliverables**
- `docker-compose.yml` and `.gitignore` **ship in this pack at repo root** — verify them against `docs/08 §1–2`; do not rewrite.
- Copy `.env.example` → `.env` (never committed).
- `git config user.name "Afif <surname>"` + `user.email` set to YOUR identity in this clone.
**Definition of Done:** `docker compose up -d db` healthy; database `transitops` reachable; test database `transitops_test` created.
**Verify**
```bash
docker compose up -d db && sleep 6
docker exec transitops-db pg_isready -U transitops
docker exec transitops-db psql -U transitops -c "CREATE DATABASE transitops_test;" || true
git config user.name && git config user.email
```
**Commit:** `chore(db): postgres 16 compose with persistent volume + test db [DB-01]`

---

## [x] DB-02 — DB wiring: config, session, declarative base, enums
**Depends on:** DB-01, BE-01 (backend skeleton exists; if BE-01 not landed, create the minimal `backend/app/` package yourself per CLAUDE.md §4 — coordinate at CP1)
**Deliverables**
- `backend/app/db/session.py`: `engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)`, `SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)`.
- `backend/app/db/base.py`: `class Base(DeclarativeBase)` + imports of **every** model module (Alembic autogenerate depends on this file).
- `backend/app/models/enums.py`: Python `str, Enum` classes mirroring `docs/02 §2` exactly — `UserRole`, `VehicleType`, `VehicleStatus`, `DriverStatus`, `TripStatus`, `MaintenanceStatus`, `ExpenseType`, `ChatRole`. SQLAlchemy columns will use `SAEnum(PyEnum, name="<pg_type_name>", values_callable=lambda e: [m.value for m in e])` so PostgreSQL ENUM **values are the lowercase strings**, not member names.
**Definition of Done:** `python -c "from app.db.base import Base"` imports clean (models added incrementally in DB-03..05).
**Verify**
```bash
cd backend && . .venv/bin/activate && python -c "from app.db.session import engine; from app.db.base import Base; print('wiring ok')"
```
**Commit:** `feat(db): sqlalchemy engine, session, base, domain enums [DB-02]`

---

## [x] DB-03 — Models: users, vehicles, drivers
**Depends on:** DB-02
**Deliverables**
- `models/user.py`, `models/vehicle.py`, `models/driver.py` — columns, types, defaults, UNIQUEs, CHECK constraints and indexes **exactly** as `docs/02 §3` (use `CheckConstraint("...", name="ck_users_email")` etc. so names match the DDL; `server_default=func.now()` + `onupdate=func.now()` for timestamps; UUID PKs via `server_default=text("gen_random_uuid()")`).
- Relationships: none needed yet beyond backrefs added later by trips.
**Definition of Done:** models import; constraint names match spec (Alembic will emit them verbatim in DB-06).
**Verify**
```bash
cd backend && . .venv/bin/activate && python -c "from app.models.user import User; from app.models.vehicle import Vehicle; from app.models.driver import Driver; print([c.name for c in Vehicle.__table__.columns])"
```
**Commit:** `feat(db): users, vehicles, drivers models with checks and uniques [DB-03]`

---

## [x] DB-04 — Models: trips, maintenance, fuel, expenses (+ signature partial indexes)
**Depends on:** DB-03
**Deliverables**
- `models/trip.py`: all columns incl. `trip_code` (UNIQUE), `revenue`, odometers, lifecycle timestamps, `ck_trips_odometer`, `ck_trips_completed_fields`; FKs `ON DELETE RESTRICT`; relationships `vehicle`, `driver`, `creator`.
- **Signature constraints:** `Index("uq_trips_active_vehicle", "vehicle_id", unique=True, postgresql_where=text("status = 'dispatched'"))` and the driver twin — plus `Sequence("trip_code_seq")` (used by BE-07 to render `TRP-0001`).
- `models/maintenance.py` with `uq_maint_open_per_vehicle` partial unique index + `ck_maint_closed`.
- `models/fuel_log.py`, `models/expense.py` per DDL (trip FK `ON DELETE SET NULL`).
- Register all in `db/base.py`.
**Definition of Done:** table objects expose the partial indexes (visible in `Trip.__table__.indexes`).
**Verify**
```bash
cd backend && . .venv/bin/activate && python -c "from app.models.trip import Trip; print([i.name for i in Trip.__table__.indexes])" | grep uq_trips_active_vehicle
```
**Commit:** `feat(db): trips, maintenance, fuel, expenses with partial unique indexes enforcing BR-4 [DB-04]`

---

## [x] DB-05 — Models: ai_settings, chat, audit
**Depends on:** DB-04
**Deliverables**
- `models/ai_settings.py`: singleton (`id SMALLINT PK DEFAULT 1` + `CheckConstraint("id = 1")`), `role_tool_permissions JSONB NOT NULL`, defaults per DDL.
- `models/chat.py`: `ChatSession`, `ChatMessage` (`tool_calls JSONB`), cascade deletes per DDL.
- `models/audit.py`: `AuditLog` (BIGSERIAL PK, JSONB payload).
- Register in `db/base.py`.
**Definition of Done:** imports clean; JSONB columns use `sqlalchemy.dialects.postgresql.JSONB`.
**Verify**
```bash
cd backend && . .venv/bin/activate && python -c "from app.db.base import Base; print(sorted(Base.metadata.tables.keys()))"
# expect: ai_settings, audit_logs, chat_messages, chat_sessions, drivers, expenses, fuel_logs, maintenance_logs, trips, users, vehicles
```
**Commit:** `feat(db): ai settings singleton, chat persistence, audit log models [DB-05]`

---

## [ ] DB-06 — Alembic init + `0001_initial_schema` + schema.sql export
**Depends on:** DB-05
**Deliverables**
- `alembic init alembic` under `backend/`; `alembic/env.py` imports `app.db.base` and sets `target_metadata = Base.metadata`; reads `DATABASE_URL` from settings/env.
- Revision `0001_initial_schema` via autogenerate, then **hand-audit** against `docs/02 §2–3`: ENUM types created (autogenerate misses `CREATE TYPE` sometimes — add explicit `sa.Enum(..., name=...).create(op.get_bind(), checkfirst=True)` in `upgrade()` if needed), partial indexes present with `postgresql_where`, sequence `trip_code_seq` created, all CHECK constraint names match. Write a full `downgrade()`.
- Export canonical DDL: `backend/app/db/schema.sql` (`docker exec transitops-db pg_dump -U transitops --schema-only transitops > backend/app/db/schema.sql`) — the artifact judges read.
**Definition of Done:** `alembic upgrade head` on a **fresh** DB succeeds; `downgrade base` drops everything; re-upgrade succeeds (round-trip proof).
**Verify**
```bash
cd backend && . .venv/bin/activate
alembic upgrade head && alembic downgrade base && alembic upgrade head
docker exec transitops-db psql -U transitops -d transitops -c "\d+ trips" | grep -E "uq_trips_active_(vehicle|driver)"
```
**Commit:** `feat(db): initial alembic migration for full schema + canonical schema.sql [DB-06]`

---

## [ ] DB-07 — Idempotent seed with demo dataset
**Depends on:** DB-06
**Deliverables**
- `backend/app/db/seed.py`, runnable as `python -m app.db.seed`, exactly per `docs/02 §7`:
  - Wipe-and-reload inside one transaction **only when** DB is empty or `--force` passed (`TRUNCATE ... RESTART IDENTITY CASCADE` on domain tables; never touch alembic_version).
  - 4 users (roles per spec, password `Transit@123` bcrypt-hashed via `app.core.security.hash_password` — if BE-02 not landed yet, inline `passlib` CryptContext and swap later), 10 vehicles (incl. `GJ-01-AB-1234` "Tata Ace Van-05" 500 kg), 8 drivers (incl. Alex D'Souza valid, one expired license, one suspended, one off_duty, two on_trip), 14 trips (8 completed w/ odometers+revenue, 2 dispatched consistent with on_trip pairs, 3 draft, 1 cancelled), 5 maintenance (1 open on the in_shop vehicle), ~20 fuel logs, ~15 expenses over last 60 days, `ai_settings` singleton with `role_tool_permissions` copied from `docs/06 §4` defaults.
  - **Consistency invariants the script must assert before commit:** every `dispatched` trip pairs with vehicle+driver in `on_trip`; the open-maintenance vehicle is `in_shop`; completed trips have `end >= start` odometer; trip_codes sequential.
  - Prints a summary table + the four demo logins.
**Definition of Done:** run twice — second run without `--force` is a no-op with a friendly message; with `--force` re-seeds cleanly.
**Verify**
```bash
cd backend && . .venv/bin/activate && python -m app.db.seed --force && python -m app.db.seed
docker exec transitops-db psql -U transitops -d transitops -c "SELECT status, COUNT(*) FROM vehicles GROUP BY status ORDER BY 1;"
```
**Commit:** `feat(db): idempotent seed with consistent demo fleet dataset [DB-07]`

---

## [ ] DB-08 — Suite D: schema-constraint tests
**Depends on:** DB-07 (and BE-01 test scaffolding; if `conftest.py` absent, create the minimal engine/session fixtures yourself against `transitops_test` per `docs/07 §1`)
**Deliverables**
- `backend/app/tests/test_schema_constraints.py` per `docs/07 §5`: negative capacity CHECK → `IntegrityError`; invalid email CHECK; duplicate registration UNIQUE; **second `dispatched` trip for same vehicle via raw ORM insert → `IntegrityError` from `uq_trips_active_vehicle`**; duplicate open maintenance per vehicle; `ck_trips_completed_fields`; vehicle delete with trips → FK RESTRICT error.
**Definition of Done:** suite green against `transitops_test`.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q app/tests/test_schema_constraints.py
```
**Commit:** `test(db): schema constraint suite proving DB-level rule enforcement [DB-08]`

---

## [ ] DB-09 — `db/queries.py`: KPI + report SQL functions
**Depends on:** DB-06
**Deliverables**
- `backend/app/db/queries.py` with typed functions wrapping the **verbatim SQL** from `docs/02 §5` via `sqlalchemy.text()` with bound params:
  - `get_vehicle_kpis(db, type_=None, region=None, status=None) -> dict` (filters applied as optional WHERE clauses),
  - `get_trip_kpis(db) -> dict`, `get_driver_kpis(db) -> dict`,
  - `get_vehicle_report_rows(db) -> list[dict]` (the big LEFT-JOIN query),
  - `get_trips_last_14_days(db)`, `get_cost_breakdown_top8(db)`, `get_status_distribution(db)` for `/dashboard/charts`.
- Docstring on each citing `docs/01 §5` definitions. These are consumed by BE-10/BE-11 — do not rename without a Change Log entry.
**Definition of Done:** functions return correct shapes against seeded data (spot-check utilization % and one report row by hand).
**Verify**
```bash
cd backend && . .venv/bin/activate && python - <<'EOF'
from app.db.session import SessionLocal
from app.db import queries
db = SessionLocal()
print(queries.get_vehicle_kpis(db)); print(queries.get_vehicle_report_rows(db)[0])
EOF
```
**Commit:** `feat(db): aggregate KPI and vehicle-report query functions [DB-09]`

---

## [ ] DB-10 — DB ops: demo reset, index review, EXPLAIN notes
**Depends on:** DB-07, DB-09
**Deliverables**
- The `db-reset` target **ships in the root Makefile** — verify it end-to-end (downgrade base → upgrade head → seed `--force`).
- Run `EXPLAIN ANALYZE` on the report query and one filtered list query; paste plans + one-line commentary into `docs/02` under a new `## 9. Query plans` section (judges: performance awareness).
- Confirm every FK has a covering index (docs/02 already specifies them — verify with `\di`).
**Definition of Done:** `make db-reset` restores a clean demo in <30 s; docs updated.
**Verify**
```bash
make db-reset && docker exec transitops-db psql -U transitops -d transitops -c "SELECT COUNT(*) FROM trips;"
```
**Commit:** `chore(db): demo reset target + query plan notes [DB-10]`

---

### After DB-10
Support Ismail on any failing Suite A concurrency test, pair with Piyush on QA checklist item 10 (persistence proof: hard refresh + `docker compose restart db`), and rehearse your `docs/09` segment — the live failing INSERT against the partial index is your money shot.
