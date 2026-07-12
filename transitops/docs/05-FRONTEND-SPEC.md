# 05 — Frontend Specification — Owner: Piyush

Stack: React 18 + TypeScript (strict) + Vite + Tailwind + TanStack Query + react-hook-form + zod + Recharts + react-router v6. Mobile-responsive down to 375 px.

## 0. Mockup fidelity (mandatory step)

The official wireframe is at **https://link.excalidraw.com/l/65VNwvy7c4X/1FHGDNgD2td** (also linked in the brief). It cannot be parsed by tooling — a human must open it. Piyush: open the mockup, and for each screen compare against §3 below; where the mockup differs (element order, column choice, placement of primary buttons), **the mockup wins** — update this doc's screen section in the same commit. The layout skeleton in §2 matches the standard structure of these hackathon mockups (left sidebar navigation, topbar, KPI card row, table-centric pages, modal forms); expect adjustments to be minor. Record confirmation in task FE-02.

## 1. Design language — "Control Room"

The subject is a transport operations desk: highway signage, instrument clusters, telltale lights. The design borrows exactly that vocabulary and nothing decorative.

**Palette (dark-first; light theme derives by inversion of surface ramp):**

| Token | Hex (dark) | Use |
|---|---|---|
| `surface-0` | `#0E1116` | app background |
| `surface-1` | `#161B22` | cards, sidebar, table rows |
| `surface-2` | `#1F2630` | hover, inputs, modals |
| `line` | `#2A323D` | 1px borders, dividers |
| `ink` | `#E8EDF2` | primary text |
| `ink-mute` | `#94A1B2` | secondary text, labels |
| `signal` | `#F5A524` | **primary accent — "signal amber"** (highway-sign amber): primary buttons, active nav, focus rings, chart emphasis |
| `ok` | `#3FB68B` | available / completed / go |
| `info` | `#4C8DFF` | on-trip / dispatched |
| `warn` | `#E8833A` | in-shop / caution / expiring |
| `danger` | `#E5484D` | suspended / cancelled / block / destructive |
| `neutral` | `#6B7684` | retired / off-duty / draft |

Light theme: `surface-0 #F6F7F9`, `surface-1 #FFFFFF`, `line #E3E7EC`, `ink #16202B`; status hues unchanged. Toggle persists to `localStorage('theme')` only (the sole permitted localStorage use besides tokens).

**Type:** Display/headings **Barlow Semi Condensed** (600/700) — a face literally derived from highway signage; body/UI **Inter** (400/500); data (registration numbers, trip codes, odometers, money) **IBM Plex Mono** 500 with `tabular-nums`. Scale: 28/22/17/14/12.5 px; labels 11 px uppercase tracking-wide `ink-mute`.

**Signature element — telltale status system:** every status everywhere renders as a `<StatusBadge>`: a small filled dot + uppercase 11px label in the status hue on a 12%-alpha pill of the same hue (e.g. ● ON TRIP in `info`). KPI cards carry a 3px left rule in their semantic hue, like gauge tick marks. This one motif carries the identity; everything else stays quiet: 8px radius, 1px `line` borders, no shadows in dark theme, 4px spacing grid, generous 24px card padding.

**States:** every async view implements loading (skeleton rows, never spinners inside tables), error (inline retry card), and empty ("No vehicles in the workshop. Vehicles appear here when maintenance is opened." + primary action). Focus-visible ring in `signal`. `prefers-reduced-motion` respected; transitions ≤ 150 ms opacity/transform only.

## 2. App shell

```
┌───────────┬────────────────────────────────────────────────┐
│  ◤ Transit│  {Page title}                    [🔎 global]   │  Topbar 56px: page title,
│    Ops    │────────────────────────────────────────────────│  search (vehicles/drivers/trips),
│           │                                                │  theme toggle, user chip
│ OPERATIONS│   KPI ROW (dashboard) / PageHeader + actions   │  (name + RoleBadge) ▾ logout
│ • Dashboard                                                │
│ • Trips   │   Content: cards / DataTable / forms           │  Sidebar 232px, collapsible
│ • Vehicles│                                                │  to icons at <1024px;
│ • Drivers │                                                │  bottom sheet nav at <768px
│ FINANCE   │                                                │
│ • Fuel &  │                                                │
│   Expenses│                                       [💬]     │  Floating chat launcher
│ • Reports │                                                │  bottom-right (docs/06)
│ ADMIN     │                                                │
│ • Users   │                                                │
│ • AI Settings                                              │
└───────────┴────────────────────────────────────────────────┘
```

Sidebar sections/items filter by role (RBAC matrix docs/03 §3): e.g. `driver` sees Operations + Dashboard only + Fuel logging; `financial_analyst` sees Finance; Admin group FM-only. Active item: `signal` text + 2px left `signal` bar.

## 3. Screens (routes → content). All tables = shared `<DataTable>`: sortable headers, column filters, debounced search, pagination footer "1–20 of 143", row actions kebab.

### `/login`
Split screen: left panel `surface-1` with wordmark "TransitOps" (Barlow SC 700) + tagline "Smart Transport Operations Platform" + a list "One login, four roles: Fleet Manager, Dispatcher, Safety Officer, Financial Analyst". Right: card with "Sign in to your account", "Enter your credentials to continue", Email + Password (zod: valid email, min 8), a "Role (Quick)" select for demo accounts (replaces popover), "Remember me" checkbox, "Forgot password?" link, submit "Sign In", inline field errors, top-level error banner for 401 ("Invalid credentials."). Below the form, text explaining access scoped by role. On success → role landing: FM/D → `/dashboard`, SO → `/drivers`, FA → `/reports`.

### `/dashboard`
1. Filter bar: Type, Status, Region selects (server-side via `/dashboard/kpis` params) + Reset.
2. KPI row (7 cards, wrap 4+3): Active Vehicles, Available, In Maintenance, Active Trips, Pending Trips, Drivers On Duty, Fleet Utilization % (this card shows a slim progress bar in `signal`). Values Plex Mono 28px; label uppercase.
3. Alert banner (if `expiring_licenses > 0`, SO/FM): warn-hued strip "3 driver licenses expire within 30 days → Review" linking `/drivers?license_valid=false`.
4. Charts grid (2×): Line "Trips — last 14 days" (completed vs dispatched); Stacked bars "Cost by vehicle — fuel vs maintenance" (top 8); Donut "Fleet status distribution" using status hues.
5. "Ask TransitOps" inline hint card → opens chat widget.

### `/vehicles`
PageHeader: title, count, `+ Add vehicle` (FM). Columns: Reg No (mono), Name, Type, Capacity kg, Odometer km, Region, Status (`StatusBadge`), Actions (Edit / Open maintenance (FM) / Retire (FM, ConfirmDialog: "Retired vehicles leave the dispatch pool permanently — continue?")). Filters: status, type, region. Row click → `/vehicles/:id` detail: spec card, rollup chips (open maintenance?, active trip), tabs Trips / Maintenance / Fuel / Expenses (filtered tables). **VehicleFormModal** fields+zod: registration (regex `^[A-Z]{2}-\d{2}-[A-Z]{1,2}-\d{4}$` with hint "e.g. GJ-01-AB-1234"), name (2–80), type select, capacity (>0), odometer (≥0), acquisition cost (>0), region select. Server 409 `DUPLICATE_REGISTRATION` maps onto the registration field.

### `/drivers`
Columns: Name, License No (mono), Category, **Expiry** (date + inline warn badge "expires in 12 d" when <30 d; danger "expired"), Contact, Safety Score (`<ScoreBar>` 0–100 colored ok/warn/danger at ≥80/50/<50), Status, Actions (Edit · Suspend/Reinstate · Set Off-duty — SO/FM). Filters: status, license validity. Suspend uses ConfirmDialog; 409 while on-trip surfaces the API message verbatim.

### `/trips` + `/trips/new`
List columns: Code (mono), Route (source → destination with arrow glyph), Vehicle, Driver, Cargo kg, Status, Dispatched/Completed date, Actions **by status**: draft → Dispatch / Edit / Cancel; dispatched → Complete / Cancel; terminal → View. **New Trip form (full page, 2-col)**: source, destination (2–120 chars), Vehicle select fed by `/vehicles?dispatchable=true` (option row shows reg + capacity; empty state: "No available vehicles — check Maintenance."), Driver select from `/drivers?assignable=true` (shows expiry + score), cargo (>0; live client check against selected vehicle capacity with the exact message style "620 kg exceeds Van-05 capacity of 500 kg"), planned distance (>0), revenue (≥0, optional), notes. **CompleteTripModal**: end odometer (≥ start, shown as helper "Start: 45,210 km"), revenue?, fuel liters + fuel cost (paired: both or neither, zod refine). **Dispatch** = ConfirmDialog summarizing checks ("Van-05 available · Alex license valid till 2027-03-01 · 450/500 kg") + optional **AI Trip Advisor panel** (docs/06 §6) with verdict chip go/caution/block.

### `/maintenance`
Columns: Vehicle, Title, Cost, Opened, Status (open/closed), Actions: Close (FM → modal asking final cost). `+ Open maintenance` (FM): vehicle select limited to `status=available` with helper text explaining BR-9; creating shows toast "GJ-01-AB-1234 moved to In Shop".

### `/fuel-expenses` (tabs: Fuel | Expenses)
Fuel columns: Vehicle, Liters, Cost, ₹/L (derived), Odometer, Date, Trip. Expense columns: Vehicle, Type badge, Amount, Description, Date. Add-modals per docs/03. Role gating per matrix.

### `/reports` (FA/FM)
Header: `Export CSV` button hitting `/reports/vehicles.csv` (blob download). Summary strip: totals (fleet op-cost, revenue, avg fuel efficiency). Main **Report table**: Reg, Name, Distance km, Liters, Fuel ₹, Maintenance ₹, Other ₹, Op-cost ₹, Revenue ₹, Efficiency km/L, **ROI** (percent, ok/danger sign coloring, `—` guards). Chart: horizontal bar ROI by vehicle.

### `/admin/users` (FM) — table + create/edit modal (email zod + server duplicate mapping, role select, active toggle, reset password field).
### `/admin/ai-settings` (FM) — see docs/06 §5 for exact controls.
### Chat widget — global launcher; panel spec in docs/06 §7.
### `*` → NotFound card; `/forbidden` → shown on 403 route guards.

## 4. Frontend engineering rules

- `api/client.ts`: axios; 401→refresh-once→retry; every error normalized to `{code,message,field}` from the envelope; `useApiError(form)` helper maps `field` errors into RHF `setError`, others → `<Toast variant="danger">`.
- Query keys: `['vehicles',filters]`, `['kpis',filters]`, etc. Mutations invalidate the touched entity **plus** `['kpis']` and `['charts']` — the "everything updates live" demo moment.
- Types in `src/types/api.ts` mirror docs/03 exactly; statuses as string-literal unions; single `STATUS_META` map → hue + label used by `StatusBadge` (one source of truth).
- Route guards: `<ProtectedRoute>` (auth) wrapping `<RequireRole roles={[…]}>` per matrix; unauthorized → `/forbidden`.
- No `any`; eslint+prettier clean; components ≤ ~150 lines, extract when larger.

## 5. Component inventory (build once in `components/ui`, use everywhere)

`Button` (primary=signal / secondary / ghost / danger; loading state) · `Input` `Select` `Textarea` `DateInput` (label, hint, error slot) · `Modal` (focus-trapped, ESC) · `ConfirmDialog` · `DataTable` · `StatusBadge` · `ScoreBar` · `Card` · `KpiCard` · `PageHeader` · `Tabs` · `Toast` (context) · `EmptyState` · `Skeleton` · `RoleBadge`.

## 6. Mockup reconciliation — 2026-07-12
- **Login screen:** Tagline is "Smart Transport Operations Platform". Left panel includes a list of the 4 roles. Right panel uses a "Role (Quick)" dropdown instead of a demo accounts popover. Right panel includes "Remember me" checkbox, "Forgot password?" link, and explanatory text about role scopes below the form. Error message for 401 is "Invalid credentials."
- **Dashboard screen:** Topbar contains a search input on the left. Topbar right contains user name, role badge, and avatar. Sidebar active state has a signal-colored border. KPI cards have a colored left-border accent (blue, green, orange). Vehicle Status is a horizontal bar chart with Available (green), On Trip (blue), In Shop (orange), Retired (red).
