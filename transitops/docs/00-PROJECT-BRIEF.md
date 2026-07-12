# 00 — Project Brief

## 1. Problem statement (verbatim intent)

Logistics companies run transport operations on spreadsheets and manual logbooks, causing scheduling conflicts, underutilized vehicles, missed maintenance, expired driver licenses, inaccurate expense tracking, and poor operational visibility. **TransitOps** centralizes the complete lifecycle: vehicle registration, driver management, dispatching, maintenance, fuel/expense logging, and analytics — with hard business rules enforced by the system, not by discipline.

## 2. Target users → application roles

| Persona (brief) | Role key | What they do in the app |
|---|---|---|
| Fleet Manager | `fleet_manager` | Full oversight: fleet assets, maintenance, lifecycle, users, AI settings. **This is the admin role.** |
| Driver (acts as dispatcher per brief) | `driver` | Creates trips, assigns available vehicles + drivers, dispatches, completes/cancels, logs fuel. |
| Safety Officer | `safety_officer` | Manages driver compliance: licenses, expiry tracking, safety scores, suspensions. |
| Financial Analyst | `financial_analyst` | Reviews expenses, fuel consumption, maintenance costs, ROI; exports reports. |

> ⚠️ Note the brief's quirk: the **Driver** persona *"creates trips, assigns vehicles and drivers"* — i.e., it is a dispatcher-style role. Implement exactly as specified; do not invent a separate dispatcher role. Mention this reading in the demo (attention to detail).

## 3. Functional scope (from the brief)

1. **Auth:** email + password login, JWT, RBAC, everything behind auth.
2. **Dashboard:** KPIs — Active Vehicles, Available Vehicles, Vehicles in Maintenance, Active Trips, Pending Trips, Drivers On Duty, Fleet Utilization %. Filters: vehicle type, status, region.
3. **Vehicle Registry:** unique registration number, name/model, type, max load capacity, odometer, acquisition cost, status ∈ {Available, On Trip, In Shop, Retired}.
4. **Driver Management:** name, license number, license category, license expiry, contact, safety score, status ∈ {Available, On Trip, Off Duty, Suspended}.
5. **Trip Management:** source, destination, available vehicle, available driver, cargo weight, planned distance. Lifecycle Draft → Dispatched → Completed / Cancelled.
6. **Maintenance:** records per vehicle; opening one auto-sets vehicle **In Shop** and removes it from dispatch pool; closing restores Available.
7. **Fuel & Expense:** fuel logs (liters, cost, date) and expenses (tolls etc.); auto-compute per-vehicle operational cost (Fuel + Maintenance).
8. **Reports & Analytics:** Fuel Efficiency (distance/liters), Fleet Utilization, Operational Cost, Vehicle ROI = (Revenue − (Maintenance + Fuel)) / Acquisition Cost. CSV export mandatory; PDF optional.

## 4. Scope tiers (build in this order)

- **T0 Mandatory (Hours 0–5):** auth+RBAC, CRUD vehicles/drivers, trip lifecycle with all validations, automatic status transitions, maintenance workflow, fuel & expense tracking, dashboard KPIs, responsive UI, persistent PostgreSQL data, seed data, business-rule tests.
- **T1 Differentiators (Hours 5–7):** charts, CSV export, RBAC-aware AI chatbot with admin config, AI Trip Advisor, search/filter/sort on tables, dark/light toggle, license-expiry alert banner.
- **T2 Stretch (only if green):** PDF export, email reminders for expiring licenses, vehicle document management, audit log viewer, MCP server exposure of chatbot tools.

## 5. What the judges score (map every decision to this)

| Criterion | Where we win it |
|---|---|
| **Database design (top priority)** | `docs/02-DATABASE.md`: normalized schema, ENUM types, CHECK constraints, partial unique indexes preventing double-dispatch at the DB layer, FK strategy, ERD, idempotent seed. Afif presents it. |
| Coding standard / modularity | Layered backend (router→service→model), feature-foldered frontend, typed everywhere, ruff/eslint clean. |
| Logic | State machines + transactional transitions with row locks (`docs/04`). |
| Validation & error handling | zod + Pydantic mirrors; standard error envelope; friendly field errors ("Cargo weight 620 kg exceeds Van-05 capacity of 500 kg"). |
| Front-end design & usability | `docs/05`: consistent token system, intentional typography, empty states, loading skeletons, confirm dialogs. |
| Security | bcrypt, JWT w/ refresh, server-side RBAC, no secrets in git, parameterized ORM queries, CORS allowlist. |
| Performance / scalability | Indexed queries, pagination on every list, aggregate KPI queries (no N+1), React Query caching. |
| Real-time & dynamic data | Everything reads/writes PostgreSQL; dashboard auto-refetches after mutations; no static JSON. |
| Git as a team sport | Each member commits their own section under their identity; Conventional Commits; `docs/08`. |
| AI adds genuine value | Chatbot answers operational questions from live data respecting the asker's role; Trip Advisor flags risky dispatches before they happen. |
| Presentation (everyone speaks) | `docs/09-DEMO-SCRIPT.md` splits the demo 3 ways by ownership. |

## 6. Explicit non-goals (8-hour discipline)

No mobile app, no websockets/live GPS tracking, no multi-tenancy, no i18n, no Kubernetes. Say "designed for, not built" if asked: architecture notes in `docs/01 §6` cover the scaling story.
