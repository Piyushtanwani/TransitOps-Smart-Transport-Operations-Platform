# 07 — Testing Strategy

Philosophy for 8 hours: **test the rules, not the framework.** Highest-value tests first; everything runnable with `make test` (pytest, quiet, < 60 s).

## 1. Harness (`backend/app/tests/conftest.py`)

- Test database: `transitops_test` on the same Postgres container (`DATABASE_URL_TEST`); session-scoped fixture runs `alembic upgrade head` once; function-scoped fixture wraps each test in a transaction rolled back after (fast, isolated).
- `client` fixture: FastAPI `TestClient` with dependency-overridden `get_db`.
- `factories.py`: `make_user(role=…)`, `make_vehicle(**kw)`, `make_driver(**kw)`, `make_trip(**kw)` with sane defaults; `auth_headers(role)` helper that creates+logs in a user of that role.

## 2. Suite A — `test_business_rules.py` (the centerpiece; one test per BR, names cite IDs)

| Test | Asserts |
|---|---|
| `test_br1_duplicate_registration_rejected` | 2nd vehicle with same reg → 409 `DUPLICATE_REGISTRATION`; message contains the reg no |
| `test_br2_in_shop_and_retired_hidden_from_dispatchable` | `?dispatchable=true` excludes both; creating a trip with an in_shop vehicle → 409 `VEHICLE_NOT_AVAILABLE` |
| `test_br3_expired_license_blocked` | driver with `license_expiry=yesterday` → trip create 409 `DRIVER_LICENSE_EXPIRED` |
| `test_br3_suspended_driver_blocked` | 409 `DRIVER_SUSPENDED` |
| `test_br4_double_dispatch_vehicle_blocked` | dispatch trip A; trip B (same vehicle) dispatch → 409; **plus DB-level check:** raw insert of second `dispatched` row raises `IntegrityError` (partial index) |
| `test_br4_double_dispatch_driver_blocked` | same for driver |
| `test_br5_cargo_exceeds_capacity` | 620 kg on 500 kg van → 409 `CARGO_EXCEEDS_CAPACITY`; boundary: exactly 500 kg → 201 |
| `test_br6_dispatch_sets_on_trip` | after dispatch: trip=dispatched, vehicle=on_trip, driver=on_trip, `start_odometer==vehicle.odometer` |
| `test_br7_complete_restores_and_rolls_odometer` | statuses → available; `vehicles.odometer_km == end_odometer`; optional fuel fields create a linked fuel_log |
| `test_br8_cancel_dispatched_restores` | vehicle+driver available; cancelling a draft leaves others untouched |
| `test_br9_open_maintenance_sets_in_shop` | vehicle → in_shop and disappears from `dispatchable` list |
| `test_br10_close_maintenance_restores_unless_retired` | available again; retired vehicle stays retired |
| `test_invalid_transitions_rejected` | complete a draft / dispatch a completed / re-cancel → 409 `INVALID_STATUS_TRANSITION` |
| `test_end_odometer_lt_start_rejected` | 409 `END_ODOMETER_LT_START` |
| `test_open_maintenance_on_on_trip_vehicle_blocked` | 409; message contains active trip code |

## 3. Suite B — `test_auth_rbac.py`

Login ok / wrong password 401 (identical message for unknown email) / inactive user 401 · `GET /auth/me` roundtrip · refresh returns new pair; reused refresh rejected · expired access → 401 `TOKEN_EXPIRED` (freeze time or short TTL override) · **RBAC sweep:** parametrized table walking docs/03 §3 — each (role, method, path) → expected 200/403; e.g. FA `POST /trips` → 403, D `GET /reports/vehicles` → 403, SO `POST /drivers` → 201.

## 4. Suite C — `test_e2e_workflow.py` (replays brief §5 — also the live demo script)

Register Van-05 (500 kg) → register Alex (valid license) → create trip 450 kg (passes 450 ≤ 500) → dispatch (both on_trip) → complete with end odometer + fuel (both available, odometer rolled, fuel log linked) → open "Oil Change" maintenance (in_shop, hidden from dispatchable) → `GET /reports/vehicles` reflects fuel cost, distance, efficiency → close maintenance (available). Single test function with staged asserts + printed narration; run it in front of judges with `pytest -q -k e2e -s`.

## 5. Suite D — `test_schema_constraints.py` (Afif)

Raw-SQL/ORM negative tests: negative capacity CHECK, bad email CHECK, duplicate open maintenance per vehicle, `ck_trips_completed_fields`, FK RESTRICT on vehicle delete.

## 6. Suite E — `test_reports_and_ai.py`

- Report math golden test: seed 1 vehicle, 2 completed trips (distances 100+150), fuel 20 L ₹2 000, maintenance ₹1 000, revenue ₹10 000, acquisition ₹100 000 → efficiency 12.5 km/L, op-cost 3 000, ROI 0.07. CSV endpoint: 200, `text/csv`, header row, same row count.
- KPI endpoint math on seeded fixtures (utilization rounding, zero-division guard).
- AI: `AI_DISABLED` path (no key) → 503 envelope; tool permission check unit test (`driver` requesting `get_vehicle_costs` → `AI_TOOL_FORBIDDEN`); chat persistence (messages rows written). OpenRouter itself is **mocked** (`httpx` transport stub) — never call the network in tests.

## 7. Frontend testing (right-sized)

- zod schemas unit-tested with vitest where math/refinements exist (cargo ≤ capacity message, fuel both-or-neither, registration regex) — `frontend/src/lib/__tests__/schemas.test.ts`.
- Everything else via the **manual QA checklist** (15 min, Hour 6, all three members on different roles):
  1. Login wrong password → friendly error; four roles see correct nav.
  2. Create vehicle with duplicate reg → error on the field.
  3. Trip form: overweight cargo blocked client-side with the exact message; in_shop vehicle absent from select.
  4. Dispatch → dashboard KPIs change without reload.
  5. Complete → vehicle odometer visibly updated; fuel log appears.
  6. Maintenance open/close cycle reflected in Vehicles table badges.
  7. Reports CSV downloads and opens in Excel.
  8. Chatbot: role-scoped question + a forbidden question (driver asks ROI → polite refusal).
  9. 375 px viewport walkthrough; theme toggle persists.
  10. Hard refresh anywhere → state intact (all data server-side).

## 8. Gates

- Hour-3 checkpoint: Suites A+D green.
- Hour-6 checkpoint: all suites green + manual checklist done. `make test` in the demo is a scripted moment (judges: "properly tested").
