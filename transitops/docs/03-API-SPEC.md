# 03 — API Specification — Owner: Ismail

Base URL `/api/v1`. All endpoints require `Authorization: Bearer <access_token>` except `POST /auth/login` and `POST /auth/refresh`. Content type JSON. FastAPI auto-docs must render at `/docs` (show judges).

## 1. Conventions

- IDs are UUID strings. Timestamps ISO-8601 UTC. Money `NUMERIC` serialized as string-safe numbers.
- Every list endpoint supports `?page=1&page_size=20` (max 100), returns `{"items": [...], "total": n, "page": 1, "page_size": 20}` and supports `?sort=field&order=asc|desc` plus resource-specific filters listed below.
- Mutations return the full updated resource. Deletes return `204`.

## 2. Error envelope (single global shape — frontend depends on it)

```json
{ "error": { "code": "CARGO_EXCEEDS_CAPACITY",
             "message": "Cargo weight 620 kg exceeds Van-05 capacity of 500 kg.",
             "field": "cargo_weight_kg" } }
```
- `422` validation (Pydantic errors mapped: first error → `field`, readable `message`).
- `409` business-rule conflict (`DomainError` codes below). `401` bad/expired token → `TOKEN_EXPIRED`/`INVALID_CREDENTIALS`. `403` `FORBIDDEN_ROLE`. `404` `NOT_FOUND`.
- Domain codes (exhaustive): `DUPLICATE_REGISTRATION`, `DUPLICATE_LICENSE`, `VEHICLE_NOT_AVAILABLE`, `DRIVER_NOT_AVAILABLE`, `DRIVER_LICENSE_EXPIRED`, `DRIVER_SUSPENDED`, `CARGO_EXCEEDS_CAPACITY`, `INVALID_STATUS_TRANSITION`, `VEHICLE_HAS_OPEN_MAINTENANCE`, `END_ODOMETER_LT_START`, `AI_DISABLED`, `AI_TOOL_FORBIDDEN`.

## 3. RBAC matrix (enforced via `require_roles`; FM = fleet_manager, D = driver/dispatcher, SO = safety_officer, FA = financial_analyst)

| Capability | FM | D | SO | FA |
|---|---|---|---|---|
| Users CRUD, AI settings | ✅ | — | — | — |
| Vehicles create/update/retire | ✅ | — | — | — |
| Vehicles read | ✅ | ✅ | ✅ | ✅ |
| Drivers create/update/suspend | ✅ | — | ✅ | — |
| Drivers read | ✅ | ✅ | ✅ | ✅ |
| Trips create/dispatch/complete/cancel | ✅ | ✅ | — | — |
| Trips read | ✅ | ✅ | ✅ | ✅ |
| Maintenance create/close | ✅ | — | — | — |
| Maintenance read | ✅ | ✅ | ✅ | ✅ |
| Fuel logs create | ✅ | ✅ | — | ✅ |
| Expenses create | ✅ | — | — | ✅ |
| Fuel/expenses read, Reports, CSV export | ✅ | — | — | ✅ |
| Dashboard KPIs | ✅ | ✅ | ✅ | ✅ |
| Chatbot | per `ai_settings.role_tool_permissions` (docs/06) |

Frontend hides forbidden actions; backend returns 403 regardless (state this in demo: defense in depth).

## 4. Endpoints

### Auth
| Method + path | Body → Response |
|---|---|
| `POST /auth/login` | `{email, password}` → `200 {access_token, refresh_token, token_type:"bearer", user:{id,email,full_name,role}}`; `401 INVALID_CREDENTIALS` (same message for unknown email vs bad password — no user enumeration). |
| `POST /auth/refresh` | `{refresh_token}` → new pair (rotation: old refresh rejected after use). |
| `GET /auth/me` | → current user. |

### Users (FM only)
`GET /users` (filters: `role`, `q` name/email) · `POST /users` `{email, full_name, role, password}` (password min 8, 1 digit) · `PATCH /users/{id}` `{full_name?, role?, is_active?, password?}` · `DELETE /users/{id}` → deactivate (`is_active=false`), never hard-delete (audit integrity).

### Vehicles
- `GET /vehicles` filters: `status`, `type`, `region`, `q` (reg no/name). Extra flag `?dispatchable=true` → only `status='available'` (BR-2; used by trip form).
- `POST /vehicles` `{registration_number, name, type, max_load_capacity_kg, odometer_km?, acquisition_cost, region}` → 201; duplicate reg → `409 DUPLICATE_REGISTRATION`.
- `GET /vehicles/{id}` includes rollups `{open_maintenance: bool, active_trip_code?: str}`.
- `PATCH /vehicles/{id}` editable: name, type, capacity, acquisition_cost, region, odometer_km (manual correction FM-only). **Status is never set directly here** except `POST /vehicles/{id}/retire` (allowed only from `available`/`in_shop`; `409 INVALID_STATUS_TRANSITION` otherwise) and `POST /vehicles/{id}/unretire` (FM, → available).
- `DELETE /vehicles/{id}` → `409` if any trips/logs exist (RESTRICT); UI offers Retire instead.

### Drivers
- `GET /drivers` filters: `status`, `license_valid=true|false`, `q`. Flag `?assignable=true` → `status='available' AND license_expiry >= CURRENT_DATE` (BR-3; trip form source).
- `POST /drivers` `{full_name, license_number, license_category, license_expiry, contact_number, safety_score?}`.
- `PATCH /drivers/{id}` fields above; status changes only via `POST /drivers/{id}/status` `{status: "off_duty"|"available"|"suspended"}` (SO/FM; cannot set `on_trip` manually; cannot change while `on_trip` → 409).
- `GET /drivers/expiring?days=30` → licenses expiring within N days (alert banner + T2 email job).

### Trips
- `GET /trips` filters: `status`, `vehicle_id`, `driver_id`, `date_from`, `date_to`, `q` (code/source/destination).
- `POST /trips` `{source, destination, vehicle_id, driver_id, cargo_weight_kg, planned_distance_km, revenue?, notes?}` → creates `draft`, generates `trip_code`. Validates BR-2/3/4/5 **already at draft time** (clear early feedback) → 409 codes above.
- `POST /trips/{id}/dispatch` (no body) → re-validates everything under row locks, sets trip `dispatched`, vehicle+driver `on_trip`, `start_odometer := vehicle.odometer_km`, `dispatched_at`. Only from `draft`.
- `POST /trips/{id}/complete` `{end_odometer, revenue?, fuel_liters?, fuel_cost?}` → only from `dispatched`; `end_odometer ≥ start_odometer` else `409 END_ODOMETER_LT_START`; sets `completed`, vehicle+driver `available`, `vehicles.odometer_km := end_odometer`; if fuel fields present, creates a linked `fuel_log`.
- `POST /trips/{id}/cancel` `{reason?}` → from `draft` or `dispatched`; if it was `dispatched`, restore vehicle+driver to `available`.
- Any other transition → `409 INVALID_STATUS_TRANSITION` with message naming the attempted edge.

### Maintenance
- `GET /maintenance` filters `status`, `vehicle_id`.
- `POST /maintenance` `{vehicle_id, title, description?, cost?}` → vehicle must be `available` (if `on_trip` → 409 `VEHICLE_NOT_AVAILABLE` "complete or cancel trip TRP-0007 first"; if `retired` → 409). Sets vehicle `in_shop` atomically (BR-9).
- `PATCH /maintenance/{id}` `{title?, description?, cost?}` while open.
- `POST /maintenance/{id}/close` `{cost?}` → sets `closed_at`, vehicle → `available` **unless retired** (BR-10).

### Fuel & Expenses
- `GET|POST /fuel-logs` — POST `{vehicle_id, liters, cost, filled_at?, odometer_at_fill?, trip_id?}`.
- `GET|POST /expenses` — POST `{vehicle_id, type, amount, description?, incurred_at?, trip_id?}`.
- Both lists filter by `vehicle_id`, `date_from`, `date_to`.

### Dashboard & Reports
- `GET /dashboard/kpis?type=&region=&status=` → `{active_vehicles, available_vehicles, in_maintenance, active_trips, pending_trips, drivers_on_duty, fleet_utilization_pct}` (filters apply to vehicle-derived KPIs). Also returns `{alerts: {expiring_licenses: n}}`.
- `GET /dashboard/charts` → `{trips_last_14d: [{date, completed, dispatched}], cost_breakdown: [{vehicle, fuel, maintenance}], status_distribution: [{status, count}]}`.
- `GET /reports/vehicles` → rows exactly matching the SQL in `docs/02 §5` (FA/FM).
- `GET /reports/vehicles.csv` → `text/csv` attachment, same rows, header row, filename `transitops_vehicle_report_<date>.csv`.

### AI (see docs/06 for full behavior)
- `GET /ai/settings` (any role → `{chatbot_enabled, model}` only) / full object + `PUT /ai/settings` (FM only).
- `GET /ai/sessions` · `POST /ai/sessions` · `GET /ai/sessions/{id}/messages`.
- `POST /ai/chat` `{session_id?, message}` → `{session_id, reply, tool_calls:[{tool,args}]}`; `503 AI_DISABLED` when disabled/unconfigured.
- `POST /ai/trip-advisor` `{vehicle_id, driver_id, cargo_weight_kg, planned_distance_km}` → `{verdict:"go"|"caution"|"block", hard_failures:[…], risk_factors:[…], summary}`; deterministic checks always run even if LLM unavailable (summary then rule-generated).

## 5. Auth implementation notes

- Access JWT claims: `sub` (user id), `role`, `exp`; HS256, `JWT_SECRET` ≥ 32 chars. On each request, load user from DB; if missing/`is_active=false` → 401 (revocation without token blacklist).
- Refresh tokens: JWT with `jti`; store current `jti` hash on the user row (`refresh_jti` column? → keep simpler: signature+exp check only, rotation returns new pair and frontend replaces stored token; note the production upgrade path = server-side jti allowlist).
- Login rate limiting: T2 (slowapi) — mention, don't build.
- Passwords: `passlib[bcrypt]`, cost 12.

## 6. OpenAPI hygiene

Tag routers (Auth, Vehicles, …), set `summary` per route, response models on every route, examples on the trip lifecycle endpoints — the `/docs` page is a scored artifact.
