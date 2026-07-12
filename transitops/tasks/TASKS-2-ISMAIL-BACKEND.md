# SECTION 2 — BACKEND · Owner: **Ismail**

Read first: `CLAUDE.md`, `docs/03-API-SPEC.md` (your contract), `docs/04-BUSINESS-RULES.md` (law), `docs/06-AI-FEATURES.md`, `docs/07-TESTING.md`.
Protocol: top-to-bottom · run **Verify** · tick `[x]` · flip `TASKS-OVERVIEW.md` · commit with the exact message. Write tests **inside** each task (its DoD says which); BE-12 is the gate where all suites must be green together.

---

## [x] BE-01 — Backend scaffold: pyproject, app skeleton, health, Makefile
**Depends on:** DB-01
**Deliverables**
- `backend/pyproject.toml` with deps exactly per `docs/08 §3` (`[project.optional-dependencies].dev = pytest, ruff, freezegun`), `[tool.ruff]` line-length 100.
- Package tree per `CLAUDE.md §4` with empty `__init__.py` files; `app/main.py`: app factory, CORS from `settings.CORS_ORIGINS`, router mounting stub, `GET /api/v1/health` → `{"status":"ok","db":"up|down"}` (runs `SELECT 1`).
- `app/core/config.py`: pydantic-settings `Settings` reading every var in `.env.example`; cached `get_settings()`.
- Root `Makefile` **ships in this pack** — verify targets against `docs/08 §3`; adjust only if a path differs on your machine.
- Your git identity configured in this clone.
**Definition of Done:** venv installs clean; server boots; health returns db up.
**Verify**
```bash
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" -q
uvicorn app.main:app --port 8000 & sleep 2 && curl -s localhost:8000/api/v1/health && kill %1
```
**Commit:** `chore(api): fastapi scaffold, settings, health endpoint, makefile [BE-01]`

---

## [x] BE-02 — Core: security (JWT/bcrypt), deps, error framework
**Depends on:** BE-01, DB-02
**Deliverables**
- `core/security.py`: `hash_password`, `verify_password` (passlib bcrypt, rounds 12), `create_access_token(user)` (claims `sub`, `role`, `exp` = now+`JWT_ACCESS_TTL_MIN`), `create_refresh_token(user)` (`jti` uuid, exp days), `decode_token(token) -> dict` raising on invalid/expired.
- `core/errors.py`: `DomainError(code, message, field=None)` (maps → 409), `NotFoundError(resource)` (404), FastAPI exception handlers producing the exact envelope of `docs/03 §2`; RequestValidationError handler mapping Pydantic errors → 422 envelope (first error → `field`, human message).
- `core/deps.py`: `get_db` (yield SessionLocal), `get_current_user` (Bearer parse → decode → DB fetch → 401 `TOKEN_EXPIRED`/`INVALID_CREDENTIALS`/inactive), `require_roles(*roles)` factory → 403 `FORBIDDEN_ROLE`.
- Unit tests: `tests/test_security.py` (hash roundtrip, expired token via freezegun, envelope shape for a sample DomainError through a dummy route).
**Definition of Done:** tests green; any raised `DomainError` anywhere returns the standard envelope.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q app/tests/test_security.py
```
**Commit:** `feat(api): jwt+bcrypt security, rbac dependency, standard error envelope [BE-02]`

---

## [x] BE-03 — Auth endpoints: login / refresh / me (+tests)
**Depends on:** BE-02, DB-03
**Deliverables**
- `schemas/auth.py`, `api/v1/auth.py`: `POST /auth/login`, `POST /auth/refresh` (rotation: respond with a fresh pair; reject non-refresh tokens), `GET /auth/me` — shapes exactly per `docs/03 §4 Auth`, identical 401 message for unknown email vs wrong password.
- `tests/conftest.py` + `tests/factories.py` per `docs/07 §1` (test DB, transaction-rollback fixture, `client`, `make_user`, `auth_headers(role)`).
- `tests/test_auth_rbac.py` (auth half of Suite B): login ok / bad password / inactive user / me roundtrip / refresh returns new pair / access token expired → 401 `TOKEN_EXPIRED`.
**Definition of Done:** suite green; manual login works against seeded users once DB-07 lands.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q app/tests/test_auth_rbac.py
```
**Commit:** `feat(api): auth login/refresh/me with rotation and tests [BE-03]`

---

## [x] BE-04 — Users CRUD (FM) + RBAC sweep scaffolding
**Depends on:** BE-03
**Deliverables**
- `schemas/user.py`, `api/v1/users.py` per spec: list (filters `role`, `q`), create (password policy: min 8, ≥1 digit — Pydantic validator with readable message), patch, delete = deactivate. All behind `require_roles("fleet_manager")`.
- Extend `tests/test_auth_rbac.py` with the **parametrized RBAC sweep table** from `docs/07 §3` — add rows as later endpoints land (each subsequent BE task appends its rows).
**Definition of Done:** FM can manage users; other roles get 403; duplicate email → 409 envelope on field `email`.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q app/tests/test_auth_rbac.py -k users
```
**Commit:** `feat(api): user management for fleet manager with rbac sweep [BE-04]`

---

## [x] BE-05 — Vehicles CRUD + retire/unretire + `dispatchable`
**Depends on:** BE-04, DB-04
**Deliverables**
- `schemas/vehicle.py` (create/update/read; read includes rollups `open_maintenance`, `active_trip_code` via two cheap subqueries on detail only), `api/v1/vehicles.py` + `services/vehicle_service.py`:
  - List with pagination/sort + filters `status,type,region,q` + `?dispatchable=true` → `status='available'` (BR-2).
  - Create → 409 `DUPLICATE_REGISTRATION` (catch IntegrityError, friendly message with the reg no).
  - Patch (no direct status), `POST /{id}/retire` (only from available/in_shop; open maintenance blocks per `docs/04 §4.8`), `POST /{id}/unretire`.
  - Delete → 409 when history exists (FK RESTRICT) with "Retire instead" message.
- Tests: BR-1 duplicate, dispatchable filter excludes in_shop/retired (feeds Suite A `test_br1`, `test_br2`).
**Definition of Done:** all vehicle endpoints match spec; tests green.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k "vehicle or br1 or br2"
```
**Commit:** `feat(api): vehicle registry with retire flow and dispatchable pool [BE-05]`

---

## [x] BE-06 — Drivers CRUD + status + expiring + `assignable`
**Depends on:** BE-05
**Deliverables**
- `schemas/driver.py`, `api/v1/drivers.py`, `services/driver_service.py`:
  - List + filters `status`, `license_valid`, `q`; `?assignable=true` → `status='available' AND license_expiry >= today` (BR-3).
  - Create/patch (SO+FM per matrix), `POST /{id}/status` (off_duty/available/suspended; never on_trip manually; 409 with active trip code if on_trip — lock the row), `GET /drivers/expiring?days=30`.
- Tests: assignable filter (expired + suspended excluded), suspend-while-on-trip 409 (fixture creates a dispatched trip), duplicate license 409.
**Definition of Done:** endpoints per spec; tests green.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k "driver or br3"
```
**Commit:** `feat(api): driver management with license validity and status guard [BE-06]`

---

## [x] BE-07 — Trip service + lifecycle endpoints (THE core task)
**Depends on:** BE-06
**Deliverables**
- `services/trip_service.py` implementing `create`, `dispatch`, `complete`, `cancel` **exactly** per the transaction recipe in `docs/04 §3` — fixed lock order trip→vehicle→driver, every BR re-checked under locks, `IntegrityError` from partial indexes caught → 409 `VEHICLE_NOT_AVAILABLE`/`DRIVER_NOT_AVAILABLE`. `trip_code` from `trip_code_seq` rendered `TRP-{n:04d}`. `complete` writes odometer forward + optional linked fuel log (both-or-neither validated in schema). Audit rows on every transition (`services/audit.py` helper: `audit(db, actor, action, entity)`).
- `schemas/trip.py` (create; complete body `{end_odometer, revenue?, fuel_liters?, fuel_cost?}` with paired-fields validator), `api/v1/trips.py` (list w/ filters per spec + the four lifecycle routes, FM+D only for mutations).
- **Suite A**: `tests/test_business_rules.py` — all 15 tests named in `docs/07 §2`, including the two-session concurrency/IntegrityError test for BR-4.
**Definition of Done:** Suite A green. This is CP2's exit criterion.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q app/tests/test_business_rules.py
```
**Commit:** `feat(api): trip lifecycle with locked transactional transitions BR-2..BR-8 [BE-07]`

---

## [x] BE-08 — Maintenance service + endpoints (BR-9, BR-10)
**Depends on:** BE-07
**Deliverables**
- `services/maintenance_service.py`: `create` (lock vehicle; must be `available`; on_trip → 409 naming active trip code; retired → 409; second open job blocked by partial index → 409 `VEHICLE_HAS_OPEN_MAINTENANCE`; sets `in_shop`), `close` (`{cost?}`, stamps `closed_at`, vehicle → `available` unless retired).
- `api/v1/maintenance.py` per spec (create/close FM-only; list all roles).
- Tests: `test_br9_*`, `test_br10_*`, `test_open_maintenance_on_on_trip_vehicle_blocked`, duplicate-open 409.
**Definition of Done:** tests green; vehicle disappears from `?dispatchable=true` when a job opens.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k "br9 or br10 or maintenance"
```
**Commit:** `feat(api): maintenance workflow with automatic vehicle status BR-9/BR-10 [BE-08]`

---

## [x] BE-09 — Fuel logs + expenses endpoints
**Depends on:** BE-08
**Deliverables**
- `schemas/fuel.py`, `schemas/expense.py`, `api/v1/fuel_logs.py`, `api/v1/expenses.py`: GET (filters `vehicle_id,date_from,date_to`, pagination) + POST per spec; role gates per matrix (fuel create: FM/D/FA; expense create: FM/FA).
- Tests: creation happy paths, negative liters/amount → 422 envelope with field, role 403 rows appended to the RBAC sweep.
**Definition of Done:** endpoints per spec; sweep updated.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k "fuel or expense"
```
**Commit:** `feat(api): fuel and expense logging with role gates [BE-09]`

---

## [x] BE-10 — Dashboard KPIs + charts endpoints
**Depends on:** BE-09, DB-09
**Deliverables**
- `api/v1/dashboard.py` + `services/report_service.py` thin wrappers over `app.db.queries`: `GET /dashboard/kpis?type=&region=&status=` (vehicle KPIs filtered; trip/driver KPIs global; plus `alerts.expiring_licenses` count ≤30 d) and `GET /dashboard/charts` returning the three series per spec shapes.
- Tests: KPI math on a controlled fixture (utilization rounding, zero-active guard) per `docs/07 §6`.
**Definition of Done:** shapes match `docs/03` exactly (Piyush's FE-05 depends on them verbatim).
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k kpi && curl -s "localhost:8000/api/v1/dashboard/kpis" -H "Authorization: Bearer $TOKEN" | python -m json.tool
```
**Commit:** `feat(api): dashboard kpis and chart aggregates [BE-10]`

---

## [x] BE-11 — Reports endpoint + CSV export
**Depends on:** BE-10
**Deliverables**
- `GET /reports/vehicles` (FA/FM) returning `db.queries.get_vehicle_report_rows` + a totals object; `GET /reports/vehicles.csv` → `StreamingResponse`, `text/csv`, `Content-Disposition: attachment; filename=transitops_vehicle_report_<YYYY-MM-DD>.csv`, header row matching table columns.
- Tests: golden-math test per `docs/07 §6` (12.5 km/L, op-cost 3 000, ROI 0.07); CSV content-type + row count.
**Definition of Done:** CSV opens in a spreadsheet with correct columns.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k report
```
**Commit:** `feat(api): vehicle analytics report with csv export [BE-11]`

---

## [x] BE-12 — GATE: Suites A/B/C green together
**Depends on:** BE-11 (Suites A+B exist from prior tasks)
**Deliverables**
- `tests/test_e2e_workflow.py` — Suite C: the brief's 9-step Van-05/Alex flow per `docs/07 §4`, with printed narration for the live demo (`pytest -q -k e2e -s`).
- Fix anything the full run surfaces; `ruff check app` clean.
**Definition of Done:** `make test` fully green in <60 s. **CP3 exit criterion — do not start AI tasks before this.**
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q && ruff check app
```
**Commit:** `test(api): e2e workflow replaying the brief scenario; full suite green [BE-12]`

---

## [ ] BE-13 — AI: client, knowledge/context, settings API
**Depends on:** BE-12, DB-05
**Deliverables**
- `services/ai/client.py` (httpx call per `docs/06 §1`, one retry on 429/5xx, 45 s timeout), `services/ai/knowledge.py` (paste the ready-made `PROJECT_KNOWLEDGE` block from `docs/10-AI-KNOWLEDGE-BASE.md` verbatim), `services/ai/context.py` (assemble 4-part system prompt).
- `GET /ai/settings` (redacted for non-FM: `{chatbot_enabled, model}`), `PUT /ai/settings` (FM; validates temperature/max_tokens ranges; audit-logged) with `schemas/ai.py`.
- Graceful degradation: missing `OPENROUTER_API_KEY` or `chatbot_enabled=false` → helper `ensure_ai_enabled()` raising `DomainError("AI_DISABLED", …, http=503)`.
- Tests: settings RBAC, redaction, 503 path.
**Definition of Done:** settings round-trip works; no network calls in tests.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k "ai_settings or ai_disabled"
```
**Commit:** `feat(ai): openrouter client, context assembly, admin settings api [BE-13]`

---

## [ ] BE-14 — AI: tool registry + chat loop + sessions
**Depends on:** BE-13
**Deliverables**
- `services/ai/tools.py`: the 9 tools of `docs/06 §4` — each `{name, description, json_schema, allowed_roles_default, executor(db, user, **args)}`; executors reuse existing services/queries, cap `limit ≤ 50`, strip role-forbidden fields (e.g. `acquisition_cost` for D/SO).
- `services/ai/chat.py`: loop per `docs/06 §3` (max 4 tool iterations, allowlist re-check from `ai_settings.role_tool_permissions`, forbidden → tool-error message `AI_TOOL_FORBIDDEN` fed back to model), persistence of all turns incl. `tool_calls` JSONB, audit `ai.chat`.
- Endpoints: `GET/POST /ai/sessions`, `GET /ai/sessions/{id}/messages` (owner-only), `POST /ai/chat`.
- Tests (OpenRouter **mocked** via httpx transport stub): tool permission unit test (driver→`get_vehicle_costs` blocked), chat persistence rows, a scripted tool-call round-trip.
**Definition of Done:** with a real key in `.env`, a manual curl chat answers a fleet question with tool chips in the response JSON.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k "ai_chat or ai_tools"
```
**Commit:** `feat(ai): rbac-aware tool-calling chatbot with persisted sessions [BE-14]`

---

## [ ] BE-15 — AI: Trip Advisor endpoint
**Depends on:** BE-14
**Deliverables**
- `services/ai/advisor.py` + `POST /ai/trip-advisor` per `docs/06 §6`: deterministic hard checks (reuse trip_service validators, non-mutating) + soft flags (capacity >90 %, safety <60, license <30 d, odometer since last closed maintenance >10 000 km, >500 km with score <70); verdict block/caution/go; LLM 3-sentence summary when enabled, template summary otherwise.
- Tests: verdict matrix (hard fail → block; soft → caution; clean → go) with mocked LLM.
**Definition of Done:** advisor never mutates state; responds <2 s without LLM.
**Verify**
```bash
cd backend && . .venv/bin/activate && pytest -q -k advisor
```
**Commit:** `feat(ai): trip advisor with deterministic risk verdicts [BE-15]`

---

## [ ] BE-16 — (T2, only after CP4 if everything is green) MCP server
**Depends on:** BE-15, all suites green, clock ≥ 7:00
**Deliverables**
- `backend/mcp_server.py` using `fastmcp`: expose the read-only tool registry over stdio with a service-role scope (financial_analyst-equivalent); README note on connecting from Claude Desktop; add `fastmcp` to a `[project.optional-dependencies].mcp` extra so core install stays lean.
**Definition of Done:** `python mcp_server.py` starts; one tool callable from an MCP inspector.
**Verify**
```bash
cd backend && . .venv/bin/activate && pip install -e ".[mcp]" -q && timeout 5 python mcp_server.py || true
```
**Commit:** `feat(ai): optional mcp server exposing fleet tools [BE-16]`

---

### After BE-15/16
Own the final `make test` demo moment, write the README **Run it** section with Piyush (FE-16), and rehearse your two `docs/09` segments (business rules live + AI).
