# 09 — Demo & Presentation Script (7 minutes + Q&A)

Judges stated: *everyone presents; shared ownership.* Each member demos what they built. Rehearse once at Hour 7.5. Screen order below; keep the app seeded (`make seed` restores a clean demo state).

## Minute 0–1 — Piyush: Problem & product tour
"Logistics ops on spreadsheets → conflicts, expired licenses, invisible costs. TransitOps is the operations desk." Login screen (mention validation + demo accounts), sign in as **Fleet Manager**, sweep the Dashboard: 7 live KPIs, filters, license-expiry alert, charts. One line on design system: "Control-room language — telltale status badges, highway-sign type, dark-first with a light toggle."

## Minute 1–3 — Ismail: The business rules, live (the core demo)
As **Dispatcher (driver role)**, run the brief's own workflow:
1. New Trip: pick **Van-05 (500 kg)** + **Alex** → enter **620 kg** → instant client error *"620 kg exceeds Van-05 capacity of 500 kg"*; change to **450 kg** → create.
2. Dispatch → show trip, vehicle, driver all flip to **On Trip** and Dashboard KPIs move **without reload**.
3. Try assigning the same vehicle to another trip → 409 conflict toast. One sentence: "That's also enforced by a partial unique index in Postgres — even a race can't double-book."
4. Complete with end odometer + fuel → statuses restore, vehicle odometer rolls forward, fuel log appears.
5. Open **Oil Change** maintenance → vehicle goes **In Shop** and vanishes from the dispatch select. Close → back to Available.
6. Flash the terminal: `pytest -q` → green; "every rule you just saw is a named test, BR-1 through BR-10."

## Minute 3–4.5 — Afif: Database design (judges' top criterion)
Split screen: ERD from `docs/02` + `psql \d+ trips`. Talk track: normalized entities, ENUM types making illegal statuses unrepresentable, CHECK constraints, FK RESTRICT preserving history (retire, don't delete), and the **signature**: `uq_trips_active_vehicle` partial unique index — run the failing raw INSERT live. Show Alembic migration + idempotent seed ("reproducible database in two commands"). One KPI SQL on screen: "aggregates in the database, no N+1."

## Minute 4.5–6 — Ismail: AI that earns its place
1. Chatbot as **Financial Analyst**: "Which vehicle has the worst ROI and why?" → watch tool chips (`get_vehicle_costs`) → grounded answer with real numbers.
2. Switch to **Driver** role, ask the same → polite refusal naming who *can* see it. "Same tool registry, role-filtered server-side; the admin configures it here" → flash **AI Settings** (model picker, permission grid).
3. **Trip Advisor**: propose a risky trip (low-safety-score driver, 95% capacity) → *Caution* verdict with reasons. "Deterministic checks decide; the model only explains — and the whole app runs fine with AI switched off."

## Minute 6–7 — Piyush: Reports + wrap
As **Financial Analyst**: Reports table (efficiency, op-cost, ROI columns), export CSV, open it. Close: "PostgreSQL-only persistence, layered FastAPI, typed React, tested rules, three sections built in parallel from a shared spec — repo history shows all three of us committing throughout." Show `git shortlog -sn` for two seconds.

## Q&A cheat sheet (owner in brackets)
- *Why sync SQLAlchemy?* [Ismail] Deliberate: threadpool handles demo load; zero async pitfalls under time pressure; upgrade path is mechanical.
- *How do you prevent double dispatch under concurrency?* [Afif] Row locks in the service **and** the partial unique index — belt and suspenders; show the test.
- *Scaling?* [Ismail] Stateless JWT API → horizontal; read replicas for reports; pagination + indexes already in.
- *Security?* [Ismail] bcrypt, short-lived access + refresh rotation, server-side RBAC, ORM-parameterized SQL, CORS allowlist, secrets in env. Next: httpOnly cookies + rate limiting.
- *Why not Firebase/Supabase?* [Afif] Brief asked for local relational DB; and our invariants live in constraints Firebase can't express.
- *What does AI add beyond a gimmick?* [Piyush] Ops questions answered from live data in one sentence instead of four screens; dispatch risk surfaced before mistakes; access mirrors RBAC.
- *Driver persona creating trips?* [Anyone] Brief defines Driver as the trip-creating role — implemented as specified, noted the dispatcher reading in docs.
- *What would you build next?* [Piyush] License-expiry emails (worker), vehicle documents, MCP endpoint so any AI client can query the fleet, PDF reports.
