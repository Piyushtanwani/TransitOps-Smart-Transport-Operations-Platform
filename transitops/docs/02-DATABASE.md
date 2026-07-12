# 02 — Database Design (PostgreSQL 16) — Owner: Afif

This is the **exact** schema. Implement it as SQLAlchemy models + one Alembic migration whose generated SQL matches this DDL. The DDL below is also kept at `backend/app/db/schema.sql` for judges to read.

## 1. ERD

```
users 1───∞ trips(created_by)                    ┌──────────────┐
users 1───∞ audit_logs                           │  ai_settings │ (singleton row id=1)
users 1───∞ chat_sessions 1───∞ chat_messages    └──────────────┘

vehicles 1───∞ trips ∞───1 drivers
vehicles 1───∞ maintenance_logs
vehicles 1───∞ fuel_logs ∞───0..1 trips
vehicles 1───∞ expenses  ∞───0..1 trips
vehicles 1───∞ vehicle_documents            (T2 stretch)
```

## 2. Enumerated types

```sql
CREATE TYPE user_role          AS ENUM ('fleet_manager','driver','safety_officer','financial_analyst');
CREATE TYPE vehicle_type       AS ENUM ('truck','van','mini_truck','trailer');
CREATE TYPE vehicle_status     AS ENUM ('available','on_trip','in_shop','retired');
CREATE TYPE driver_status      AS ENUM ('available','on_trip','off_duty','suspended');
CREATE TYPE trip_status        AS ENUM ('draft','dispatched','completed','cancelled');
CREATE TYPE maintenance_status AS ENUM ('open','closed');
CREATE TYPE expense_type       AS ENUM ('toll','parking','fine','loading','other');
CREATE TYPE chat_role          AS ENUM ('user','assistant','tool');
```

Rationale: ENUMs make invalid states unrepresentable at the storage layer and self-document the domain — cite this to judges.

## 3. Tables (full DDL)

```sql
-- ============ users ============
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(120) NOT NULL,
    role            user_role NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_users_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- ============ vehicles ============
CREATE TABLE vehicles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_number VARCHAR(20) NOT NULL UNIQUE,            -- BR-1
    name                VARCHAR(80) NOT NULL,                    -- model/name e.g. "Tata Ace Van-05"
    type                vehicle_type NOT NULL,
    max_load_capacity_kg NUMERIC(10,2) NOT NULL CHECK (max_load_capacity_kg > 0),
    odometer_km         NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (odometer_km >= 0),
    acquisition_cost    NUMERIC(14,2) NOT NULL CHECK (acquisition_cost > 0),  -- ROI divisor
    region              VARCHAR(40) NOT NULL,                    -- dashboard filter: North/South/East/West
    status              vehicle_status NOT NULL DEFAULT 'available',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_vehicles_status ON vehicles(status);
CREATE INDEX ix_vehicles_type_region ON vehicles(type, region);

-- ============ drivers ============
CREATE TABLE drivers (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name        VARCHAR(120) NOT NULL,
    license_number   VARCHAR(30) NOT NULL UNIQUE,
    license_category VARCHAR(10) NOT NULL,                       -- LMV / HMV / MCWG …
    license_expiry   DATE NOT NULL,
    contact_number   VARCHAR(15) NOT NULL CHECK (contact_number ~ '^[0-9+][0-9 -]{7,14}$'),
    safety_score     NUMERIC(5,2) NOT NULL DEFAULT 100 CHECK (safety_score BETWEEN 0 AND 100),
    status           driver_status NOT NULL DEFAULT 'available',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_drivers_status ON drivers(status);
CREATE INDEX ix_drivers_license_expiry ON drivers(license_expiry);

-- ============ trips ============
CREATE TABLE trips (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_code        VARCHAR(12) NOT NULL UNIQUE,                -- 'TRP-0001', app-generated from sequence
    source           VARCHAR(120) NOT NULL,
    destination      VARCHAR(120) NOT NULL,
    vehicle_id       UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    driver_id        UUID NOT NULL REFERENCES drivers(id)  ON DELETE RESTRICT,
    cargo_weight_kg  NUMERIC(10,2) NOT NULL CHECK (cargo_weight_kg > 0),
    planned_distance_km NUMERIC(10,2) NOT NULL CHECK (planned_distance_km > 0),
    revenue          NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (revenue >= 0),   -- needed for ROI
    status           trip_status NOT NULL DEFAULT 'draft',
    start_odometer   NUMERIC(12,2),
    end_odometer     NUMERIC(12,2),
    notes            TEXT,
    created_by       UUID NOT NULL REFERENCES users(id),
    dispatched_at    TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ,
    cancelled_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_trips_odometer CHECK (end_odometer IS NULL OR start_odometer IS NULL OR end_odometer >= start_odometer),
    CONSTRAINT ck_trips_completed_fields CHECK (status <> 'completed' OR (start_odometer IS NOT NULL AND end_odometer IS NOT NULL))
);
CREATE SEQUENCE trip_code_seq START 1;
CREATE INDEX ix_trips_status ON trips(status);
CREATE INDEX ix_trips_vehicle ON trips(vehicle_id);
CREATE INDEX ix_trips_driver ON trips(driver_id);

-- ★ Signature constraints: the DATABASE ITSELF forbids double-dispatch (BR-4) — demo these to judges.
CREATE UNIQUE INDEX uq_trips_active_vehicle ON trips(vehicle_id) WHERE status = 'dispatched';
CREATE UNIQUE INDEX uq_trips_active_driver  ON trips(driver_id)  WHERE status = 'dispatched';

-- ============ maintenance_logs ============
CREATE TABLE maintenance_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id  UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    title       VARCHAR(120) NOT NULL,                           -- "Oil Change"
    description TEXT,
    cost        NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (cost >= 0),
    status      maintenance_status NOT NULL DEFAULT 'open',
    opened_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at   TIMESTAMPTZ,
    created_by  UUID NOT NULL REFERENCES users(id),
    CONSTRAINT ck_maint_closed CHECK (status <> 'closed' OR closed_at IS NOT NULL)
);
CREATE UNIQUE INDEX uq_maint_open_per_vehicle ON maintenance_logs(vehicle_id) WHERE status = 'open';  -- one open job per vehicle
CREATE INDEX ix_maint_vehicle ON maintenance_logs(vehicle_id);

-- ============ fuel_logs ============
CREATE TABLE fuel_logs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id       UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    trip_id          UUID REFERENCES trips(id) ON DELETE SET NULL,   -- optional link when logged at trip completion
    liters           NUMERIC(8,2) NOT NULL CHECK (liters > 0),
    cost             NUMERIC(12,2) NOT NULL CHECK (cost >= 0),
    odometer_at_fill NUMERIC(12,2) CHECK (odometer_at_fill IS NULL OR odometer_at_fill >= 0),
    filled_at        DATE NOT NULL DEFAULT CURRENT_DATE,
    created_by       UUID NOT NULL REFERENCES users(id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_fuel_vehicle_date ON fuel_logs(vehicle_id, filled_at);

-- ============ expenses ============
CREATE TABLE expenses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id  UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    trip_id     UUID REFERENCES trips(id) ON DELETE SET NULL,
    type        expense_type NOT NULL,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    description VARCHAR(255),
    incurred_at DATE NOT NULL DEFAULT CURRENT_DATE,
    created_by  UUID NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_expenses_vehicle_date ON expenses(vehicle_id, incurred_at);

-- ============ AI: settings (singleton), chat persistence ============
CREATE TABLE ai_settings (
    id            SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    chatbot_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    model         VARCHAR(80) NOT NULL DEFAULT 'anthropic/claude-3.5-haiku',
    temperature   NUMERIC(3,2) NOT NULL DEFAULT 0.30 CHECK (temperature BETWEEN 0 AND 2),
    max_tokens    INTEGER NOT NULL DEFAULT 1024 CHECK (max_tokens BETWEEN 128 AND 8192),
    system_prompt TEXT NOT NULL,
    role_tool_permissions JSONB NOT NULL,     -- {"driver": ["get_vehicles", ...], ...} see docs/06 §4
    updated_by    UUID REFERENCES users(id),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat_sessions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      VARCHAR(120) NOT NULL DEFAULT 'New chat',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE chat_messages (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role       chat_role NOT NULL,
    content    TEXT NOT NULL,
    tool_calls JSONB,                          -- persisted tool invocations for transparency
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_chat_messages_session ON chat_messages(session_id, created_at);

-- ============ audit_logs (T1) ============
CREATE TABLE audit_logs (
    id         BIGSERIAL PRIMARY KEY,
    user_id    UUID REFERENCES users(id),
    action     VARCHAR(60) NOT NULL,           -- 'trip.dispatch', 'vehicle.create', …
    entity     VARCHAR(30) NOT NULL,
    entity_id  UUID,
    payload    JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ vehicle_documents (T2 stretch — migration only if time) ============
CREATE TABLE vehicle_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id  UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    doc_type    VARCHAR(40) NOT NULL,           -- RC / Insurance / PUC / Permit
    file_path   VARCHAR(255) NOT NULL,
    expiry_date DATE,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`updated_at` maintenance: SQLAlchemy `onupdate=func.now()` on every mutable table (simpler than triggers; state the tradeoff if asked).

## 4. Constraint → business-rule map (rehearse this table for judging)

| DB mechanism | Enforces |
|---|---|
| `vehicles.registration_number UNIQUE`, `drivers.license_number UNIQUE` | BR-1 uniqueness |
| Partial unique indexes `uq_trips_active_*` | BR-4: one dispatched trip per vehicle/driver — **race-proof at DB level** |
| `uq_maint_open_per_vehicle` | one open maintenance job per vehicle |
| `CHECK cargo_weight_kg > 0`, capacity/odometer/cost checks | data sanity for BR-5 math |
| `ck_trips_odometer`, `ck_trips_completed_fields` | completion integrity (brief Step 6) |
| ENUM types | illegal statuses impossible |
| `ON DELETE RESTRICT` on operational FKs | no orphaned history; retire vehicles instead of deleting |
| Cross-table rules (capacity vs cargo, license expiry, status gates) | **service layer** inside transactions with `FOR UPDATE` — DB constraints cover what SQL can express declaratively; services cover the rest. Say exactly this sentence to judges. |

## 5. KPI / report queries (implement verbatim in `report_service.py`)

```sql
-- Dashboard KPIs (one round trip)
SELECT
  COUNT(*) FILTER (WHERE status <> 'retired')                       AS active_vehicles,
  COUNT(*) FILTER (WHERE status = 'available')                      AS available_vehicles,
  COUNT(*) FILTER (WHERE status = 'in_shop')                        AS in_maintenance,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'on_trip')
        / NULLIF(COUNT(*) FILTER (WHERE status <> 'retired'),0), 1) AS fleet_utilization_pct
FROM vehicles;

SELECT COUNT(*) FILTER (WHERE status='dispatched') AS active_trips,
       COUNT(*) FILTER (WHERE status='draft')      AS pending_trips FROM trips;

SELECT COUNT(*) FILTER (WHERE status IN ('available','on_trip')) AS drivers_on_duty FROM drivers;

-- Per-vehicle report row (fuel eff, op cost, ROI)
SELECT v.id, v.registration_number, v.name, v.type, v.region, v.acquisition_cost,
       COALESCE(t.total_distance,0) AS total_distance_km,
       COALESCE(f.total_liters,0)   AS total_liters,
       COALESCE(f.total_fuel_cost,0) AS fuel_cost,
       COALESCE(m.total_maint_cost,0) AS maintenance_cost,
       COALESCE(e.total_other,0)    AS other_expenses,
       COALESCE(f.total_fuel_cost,0)+COALESCE(m.total_maint_cost,0) AS operational_cost,
       COALESCE(t.total_revenue,0)  AS revenue,
       CASE WHEN COALESCE(f.total_liters,0) > 0
            THEN ROUND(COALESCE(t.total_distance,0)/f.total_liters, 2) END AS fuel_efficiency_km_l,
       ROUND((COALESCE(t.total_revenue,0)
             - (COALESCE(f.total_fuel_cost,0)+COALESCE(m.total_maint_cost,0)))
             / v.acquisition_cost, 4) AS roi
FROM vehicles v
LEFT JOIN (SELECT vehicle_id, SUM(end_odometer-start_odometer) AS total_distance,
                  SUM(revenue) AS total_revenue
           FROM trips WHERE status='completed' GROUP BY vehicle_id) t ON t.vehicle_id=v.id
LEFT JOIN (SELECT vehicle_id, SUM(liters) total_liters, SUM(cost) total_fuel_cost
           FROM fuel_logs GROUP BY vehicle_id) f ON f.vehicle_id=v.id
LEFT JOIN (SELECT vehicle_id, SUM(cost) total_maint_cost
           FROM maintenance_logs GROUP BY vehicle_id) m ON m.vehicle_id=v.id
LEFT JOIN (SELECT vehicle_id, SUM(amount) total_other
           FROM expenses GROUP BY vehicle_id) e ON e.vehicle_id=v.id
ORDER BY v.registration_number;
```

## 6. Migration plan

One initial Alembic revision `0001_initial_schema` creating everything in §2–§3 (T0/T1 tables; `vehicle_documents` in a later `0002` only if T2 attempted). `alembic downgrade base` must fully drop (write the downgrade).

## 7. Seed data (`app/db/seed.py`, idempotent — delete-then-insert inside a transaction, guarded by `--force` flag or empty-DB check)

- **Users (password for all: `Transit@123`, bcrypt-hashed at seed time):**
  `manager@transitops.in` (fleet_manager, "Meera Nair") · `dispatch@transitops.in` (driver, "Piyush Rathod") · `safety@transitops.in` (safety_officer, "Afif Khan") · `finance@transitops.in` (financial_analyst, "Ismail Mansuri")
- **Vehicles (10):** mixed types/regions; e.g. `GJ-01-AB-1234` "Tata Ace Van-05" van 500 kg (the brief's example), `GJ-05-CD-2201` "Ashok Leyland Dost" mini_truck 1250 kg, `MH-12-EF-8890` "Eicher Pro 2049" truck 5000 kg, `GJ-01-GH-3345` "Mahindra Blazo 28" truck 18000 kg, trailer 25000 kg, etc. Odometers 8 000–210 000 km; acquisition ₹4.5 L–₹32 L; 6 available, 2 on_trip, 1 in_shop, 1 retired.
- **Drivers (8):** varied safety scores (58–98). Include: "Alex D'Souza" valid LMV license (brief example), one **expired** license (`license_expiry = CURRENT_DATE - 40 days`, status available — proves BR-3 blocks him), one `suspended`, one `off_duty`, two `on_trip` (matching the on_trip vehicles).
- **Trips (14):** 8 completed (with start/end odometer, revenue ₹3 000–₹85 000, linked fuel logs), 2 dispatched (consistent with on_trip vehicle+driver pairs), 3 draft, 1 cancelled. Sources/destinations: Ahmedabad, Surat, Mumbai, Pune, Rajkot, Vadodara, Indore.
- **Maintenance (5):** 1 open ("Gearbox overhaul", on the in_shop vehicle), 4 closed with costs ₹1 200–₹42 000.
- **Fuel logs (~20)** and **expenses (~15, tolls/parking/fines)** spread over the last 60 days so charts have shape.
- **ai_settings:** singleton row with defaults + the role_tool_permissions JSON from `docs/06 §4`.

Seed must print a summary table and the four demo logins when done.

## 8. Verification (Definition of Done for the schema)

```bash
make db-migrate && make seed
psql $DATABASE_URL -c "\d+ trips"                     # shows partial indexes
psql $DATABASE_URL -c "INSERT INTO trips ..."         # duplicate dispatched vehicle → ERROR (demo!)
pytest backend/app/tests/test_schema_constraints.py   # DB-level tests green
```
