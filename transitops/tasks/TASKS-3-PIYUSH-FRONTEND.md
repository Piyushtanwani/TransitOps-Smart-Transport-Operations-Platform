# SECTION 3 — FRONTEND · Owner: **Piyush**

Read first: `CLAUDE.md`, `docs/05-FRONTEND-SPEC.md` (your spec — tokens, screens, components), `docs/03-API-SPEC.md` (contract + error envelope), `docs/06 §5–7` (AI UI).
Protocol: top-to-bottom · run **Verify** · tick `[x]` · flip `TASKS-OVERVIEW.md` · commit with the exact message.
Contract-first rule: if a backend endpoint is not live yet, build against the exact shapes in `docs/03` (temporary typed mock module `src/api/__mocks__/` allowed, deleted at integration) — never invent shapes.

---

## [x] FE-01 — Vite scaffold + Tailwind tokens + fonts + theme toggle
**Depends on:** —
**Deliverables**
- `npm create vite@latest frontend -- --template react-ts`; deps per `docs/08 §3`; TS `strict: true`; eslint+prettier configured; your git identity set in this clone.
- Tailwind configured with the **full token table** of `docs/05 §1` as CSS variables on `:root`/`.light` + `tailwind.config.js` color mapping (`surface-0…2, line, ink, ink-mute, signal, ok, info, warn, danger, neutral`); radius 8px; spacing 4px grid.
- Fonts via Fontsource or Google Fonts link: Barlow Semi Condensed (600/700), Inter (400/500), IBM Plex Mono (500); base styles in `index.css` (body = Inter on `surface-0`, headings Barlow SC, `.font-data` = Plex Mono `tabular-nums`).
- `ThemeToggle` (dark default; `.light` class on `<html>`; persists to `localStorage('theme')` — the only permitted localStorage besides tokens).
**Definition of Done:** blank app renders themed background + sample heading in all three faces; toggle persists across reload.
**Verify**
```bash
cd frontend && npm run build && npm run lint
```
**Commit:** `chore(fe): vite+ts scaffold with control-room design tokens and theming [FE-01]`

---

## [ ] FE-02 — Mockup fidelity review + ui/ component kit
**Depends on:** FE-01
**Deliverables**
- **Open the official mockup** https://link.excalidraw.com/l/65VNwvy7c4X/1FHGDNgD2td and reconcile against `docs/05 §2–3`: note any differing element order/placement per screen in a checklist at the bottom of `docs/05` (`## 6. Mockup reconciliation — <date>`); **the mockup wins** — adjust the doc in the same commit. Capture screenshots into `docs/mockup/` for teammates.
- Build the component kit per `docs/05 §5`: `Button, Input, Select, Textarea, DateInput, Modal, ConfirmDialog, DataTable (sortable headers, pagination footer, loading skeleton rows, empty-state slot), StatusBadge (+ single STATUS_META map in src/lib/status.ts), ScoreBar, Card, KpiCard, PageHeader, Tabs, Toast (context+hook), EmptyState, Skeleton, RoleBadge` — each ≤150 lines, focus-visible ring in `signal`, reduced-motion respected.
- Kitchen-sink route `/dev/kit` (dev-only) rendering every component for eyeball QA.
**Definition of Done:** kit renders in both themes; DataTable handles sort+paginate on stub data; reconciliation section committed.
**Verify**
```bash
cd frontend && npm run build && npm run lint
```
**Commit:** `feat(fe): ui component kit + mockup reconciliation notes [FE-02]`

---

## [ ] FE-03 — API client + AuthContext + router guards + Login
**Depends on:** FE-02 (integrates live once BE-03 is up)
**Deliverables**
- `src/api/client.ts`: axios instance on `VITE_API_BASE_URL`; request interceptor injects access token; response interceptor: single-flight 401 → `POST /auth/refresh` → retry once → else hard logout; every error normalized to `{code,message,field}` from the envelope (`docs/03 §2`).
- `src/types/api.ts`: string-literal unions + interfaces mirroring `docs/03` (User, Vehicle, Driver, Trip, Maintenance, FuelLog, Expense, Kpis, ReportRow, AiSettings, ChatMessage…).
- `src/auth/AuthContext.tsx` (user + access token in memory, refresh token in localStorage — documented tradeoff), `useAuth()`, `<ProtectedRoute>`, `<RequireRole roles>`; `src/hooks/useApiError.ts` mapping `field` → RHF `setError`, otherwise danger Toast.
- `router.tsx` with all routes of `docs/05 §3` (feature pages as placeholders), `/forbidden`, `*` NotFound.
- **Login page** exactly per spec: split layout, zod (email, min-8 password), demo-accounts popover, 401 banner, role-based landing redirect.
**Definition of Done:** login against seeded `manager@transitops.in` works E2E; expired-token path returns to login gracefully.
**Verify**
```bash
cd frontend && npm run build && npm run lint   # + manual: login all 4 roles
```
**Commit:** `feat(fe): auth flow, api client with refresh retry, guarded router, login [FE-03]`

---

## [ ] FE-04 — App shell: role-filtered sidebar + topbar
**Depends on:** FE-03
**Deliverables**
- `components/layout/AppShell.tsx` per `docs/05 §2`: 232px sidebar (sections OPERATIONS/FINANCE/ADMIN filtered by role matrix `docs/03 §3`; active = signal text + 2px left bar), 56px topbar (page title, global search stub, ThemeToggle, user chip with RoleBadge + logout menu), floating chat launcher slot (wired in FE-14), responsive: icon rail <1024px, bottom-sheet nav <768px.
**Definition of Done:** each role sees exactly its nav items; layout holds at 375px.
**Verify**
```bash
cd frontend && npm run build   # + manual role-nav walkthrough
```
**Commit:** `feat(fe): app shell with role-aware navigation [FE-04]`

---

## [ ] FE-05 — Dashboard
**Depends on:** FE-04 (live data needs BE-10)
**Deliverables**
- `features/dashboard/DashboardPage.tsx` per spec: filter bar (type/status/region → query params of `['kpis',filters]`), 7 `KpiCard`s (utilization card gets slim signal progress bar), license-expiry alert banner (SO/FM, links to `/drivers?license_valid=false`), 3 Recharts (line trips-14d, stacked bars cost-by-vehicle top 8, donut status distribution using STATUS_META hues), "Ask TransitOps" hint card.
- Loading = skeleton cards; error = inline retry card.
**Definition of Done:** filters refetch; numbers match a psql spot-check; charts render seeded shapes.
**Verify**
```bash
cd frontend && npm run build   # + manual against seeded API
```
**Commit:** `feat(fe): live kpi dashboard with filters, alert, charts [FE-05]`

---

## [ ] FE-06 — Vehicles
**Depends on:** FE-04 (live: BE-05)
**Deliverables**
- List page per spec (columns, filters, kebab actions gated FM), `VehicleFormModal` (zod incl. registration regex `^[A-Z]{2}-\d{2}-[A-Z]{1,2}-\d{4}$` with hint, capacity>0, cost>0), server `DUPLICATE_REGISTRATION` mapped onto the field via `useApiError`, Retire `ConfirmDialog` with the spec's warning copy, detail route `/vehicles/:id` (spec card, rollup chips, tabs Trips/Maintenance/Fuel/Expenses reusing DataTable with `vehicle_id` filter).
- Mutations invalidate `['vehicles']` + `['kpis']` + `['charts']`.
**Definition of Done:** create → appears without reload; duplicate reg shows inline field error; retire flips badge to neutral RETIRED.
**Verify**
```bash
cd frontend && npm run build && npm run lint
```
**Commit:** `feat(fe): vehicle registry with validated form and detail view [FE-06]`

---

## [ ] FE-07 — Drivers
**Depends on:** FE-06 (live: BE-06)
**Deliverables**
- List per spec: expiry column with warn/danger inline badges (<30 d / expired), `ScoreBar`, status actions (Suspend/Reinstate/Off-duty, SO+FM, ConfirmDialog; 409 message from API shown verbatim in Toast), driver form modal (license number, category select LMV/HMV/MCWG/Other, expiry DateInput, contact zod regex per DDL, safety score 0–100).
- Filter `license_valid=false` view reachable from dashboard alert.
**Definition of Done:** expired-license seed driver shows danger badge; suspend-while-on-trip surfaces the trip-code error.
**Verify**
```bash
cd frontend && npm run build && npm run lint
```
**Commit:** `feat(fe): driver management with license and safety indicators [FE-07]`

---

## [ ] FE-08 — Trips list + New Trip form
**Depends on:** FE-07 (live: BE-07)
**Deliverables**
- `/trips` list per spec: status-dependent action sets, filters, mono trip codes, route arrow rendering.
- `/trips/new` full-page 2-col form: Vehicle select fed by `?dispatchable=true` (option shows reg + capacity; EmptyState copy per spec), Driver select from `?assignable=true` (shows expiry + score), cargo with **live client check** against selected vehicle capacity producing exactly "«x» kg exceeds «name» capacity of «cap» kg", planned distance>0, revenue≥0 optional, notes; zod schema in `src/lib/schemas/trip.ts` (unit-testable), server 409s mapped to fields.
**Definition of Done:** overweight blocked client-side; boundary (cargo == capacity) allowed; created trip lands in list as DRAFT.
**Verify**
```bash
cd frontend && npm run test -- schemas && npm run build
```
**Commit:** `feat(fe): trip creation with live capacity validation [FE-08]`

---

## [ ] FE-09 — Trip lifecycle UI
**Depends on:** FE-08
**Deliverables**
- **Dispatch** ConfirmDialog summarizing checks per spec copy ("Van-05 available · Alex license valid till … · 450/500 kg") with Advisor slot (wired FE-15); **CompleteTripModal** (end odometer ≥ start with helper "Start: 45,210 km", revenue?, fuel liters+cost zod-paired both-or-neither); **Cancel** ConfirmDialog with reason field.
- All three mutations invalidate `['trips','vehicles','drivers','kpis','charts']` — the "everything updates live" demo moment.
- 409 envelope codes rendered as danger Toasts with the API message verbatim.
**Definition of Done:** full brief workflow (create→dispatch→complete→statuses restore, odometer rolls) clickable end-to-end; invalid transitions show friendly conflict toasts.
**Verify**
```bash
cd frontend && npm run build   # + manual lifecycle run per docs/07 §7 items 4–5
```
**Commit:** `feat(fe): dispatch, complete, cancel flows with live status propagation [FE-09]`

---

## [ ] FE-10 — Maintenance page
**Depends on:** FE-09 (live: BE-08)
**Deliverables**
- List per spec; `+ Open maintenance` modal (vehicle select limited `status=available` + helper text explaining BR-9), Close modal asking final cost; toasts "«reg» moved to In Shop" / "restored to Available"; invalidations incl. `['vehicles']`, `['kpis']`.
**Definition of Done:** open→vehicle vanishes from trip form's dispatchable select; close→returns.
**Verify**
```bash
cd frontend && npm run build
```
**Commit:** `feat(fe): maintenance workflow ui [FE-10]`

---

## [ ] FE-11 — Fuel & Expenses page
**Depends on:** FE-10 (live: BE-09)
**Deliverables**
- `/fuel-expenses` Tabs per spec: Fuel table (derived ₹/L column) + add modal; Expenses table (type badges) + add modal; date-range + vehicle filters; role-gated create buttons per matrix.
**Definition of Done:** fuel log added at trip completion (FE-09) appears here linked to its trip.
**Verify**
```bash
cd frontend && npm run build
```
**Commit:** `feat(fe): fuel and expense tracking ui [FE-11]`

---

## [ ] FE-12 — Reports page + CSV download
**Depends on:** FE-11 (live: BE-11)
**Deliverables**
- `/reports` (FA/FM): summary strip totals, full report table per spec columns (mono numerics, ROI % colored ok/danger, `—` guards for null efficiency), horizontal-bar ROI chart, **Export CSV** button → axios blob → programmatic download of `transitops_vehicle_report_<date>.csv`.
**Definition of Done:** CSV opens in a spreadsheet; table matches API rows.
**Verify**
```bash
cd frontend && npm run build
```
**Commit:** `feat(fe): analytics report with csv export [FE-12]`

---

## [ ] FE-13 — Admin: Users page
**Depends on:** FE-12 (live: BE-04)
**Deliverables**
- `/admin/users` (FM): table (name, email, RoleBadge, active), create/edit modal (email zod + server duplicate mapped to field, role select, active toggle, optional reset-password field with policy hint), deactivate ConfirmDialog.
**Definition of Done:** new user can log in; deactivated user gets the 401 path.
**Verify**
```bash
cd frontend && npm run build
```
**Commit:** `feat(fe): user administration [FE-13]`

---

## [ ] FE-14 — Chat widget
**Depends on:** FE-04 (live: BE-14)
**Deliverables**
- `features/chat/` per `docs/06 §7`: floating signal launcher → 380×560 panel (full-screen sheet <768px), header (title, model name from redacted `GET /ai/settings`, New chat, session history dropdown), message list (user right signal-tinted, assistant left surface-2, **tool chips** "🔧 get_vehicles(status=available)" under assistant turns from `tool_calls`), input with Enter-to-send + "Thinking…" shimmer, role-based starter chips per spec, 503 `AI_DISABLED` → EmptyState with the spec copy.
- Sessions + messages via API (persistence proof: reload keeps history).
**Definition of Done:** role-scoped Q&A works with a real key; disabled state renders when admin turns chatbot off.
**Verify**
```bash
cd frontend && npm run build
```
**Commit:** `feat(fe): rbac-aware assistant chat widget with tool transparency [FE-14]`

---

## [ ] FE-15 — Admin AI Settings + Trip Advisor panel
**Depends on:** FE-14 (live: BE-13/15)
**Deliverables**
- `/admin/ai-settings` (FM) per `docs/06 §5`: enabled switch, model input+datalist, temperature slider (0–1, .05), max tokens, system-prompt textarea (4k counter), **roles × tools permission grid** bound to `role_tool_permissions`, "Test connection" button showing latency+model, save → PUT with success toast.
- **Trip Advisor panel** in the Dispatch dialog + `/trips/new` sidebar: "Analyze" → `POST /ai/trip-advisor`, verdict chip (ok/warn/danger per go/caution/block), hard-failure + risk lists, italic summary; **Dispatch never disabled by caution** (advisory copy per spec).
**Definition of Done:** toggling a tool off for `driver` makes the chatbot refuse it live; advisor renders all three verdicts (use seed's risky driver).
**Verify**
```bash
cd frontend && npm run build
```
**Commit:** `feat(fe): ai settings console and trip advisor verdicts [FE-15]`

---

## [ ] FE-16 — Polish gate: states audit, responsive, QA, README
**Depends on:** everything above; clock ≥ 7:00 (feature freeze)
**Deliverables**
- Audit every page: loading skeletons, error retry cards, EmptyStates with action copy, focus rings, 375px layout; remove `/dev/kit` from prod build.
- Run the 10-point manual QA checklist (`docs/07 §7`) with Afif + Ismail on different roles; log findings→fixes as `fix(fe): … [FE-16]` commits.
- Root `README.md` **Run it** section with Ismail: prerequisites, `make demo`, `make api`, `make web`, four demo logins table, 3–4 screenshots.
**Definition of Done:** checklist all green; README lets a stranger run the app in <5 minutes.
**Verify**
```bash
cd frontend && npm run build && npm run lint && npm run test
```
**Commit:** `chore(fe): polish pass, qa checklist green, run-it readme [FE-16]`

---

### After FE-16
Rehearse your two `docs/09` segments (opening tour + reports/wrap) and keep the browser zoom/theme preset for the projector.
