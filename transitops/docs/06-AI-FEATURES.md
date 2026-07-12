# 06 — AI Features (OpenRouter) — Owner: Ismail

Two features, both must **degrade gracefully** when `OPENROUTER_API_KEY` is unset (endpoints return 503 `AI_DISABLED`; UI shows a quiet "AI assistant is not configured" card — the core app never depends on AI).

## 1. OpenRouter client (`app/services/ai/client.py`)

OpenAI-compatible. Use `httpx` directly (no SDK dependency):

```python
resp = httpx.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
             "HTTP-Referer": "http://localhost:5173", "X-Title": "TransitOps"},
    json={"model": cfg.model, "temperature": float(cfg.temperature),
          "max_tokens": cfg.max_tokens, "messages": messages,
          "tools": tool_schemas or None}, timeout=45)
```

Model comes from `ai_settings` (DB), never hardcoded — admin can switch models live. Handle 429/5xx with one retry then a friendly failure message persisted as the assistant turn.

## 2. Chatbot = full project context + live data + role awareness

System prompt assembled per request by `ai/context.py`:

1. **Static context** (`app/services/ai/knowledge.py`, a constant string ~520 words): what TransitOps is, the entities, the 10 business rules, KPI definitions, the role matrix — i.e., "full context of the whole project". **Ready to paste from `docs/10-AI-KNOWLEDGE-BASE.md`** — use it verbatim.
2. **Live snapshot:** current KPI numbers (one cheap query) + today's date.
3. **Requester identity:** name, role, and an explicit permission statement: *"The user is a driver/dispatcher. You may only call the tools listed. If asked about financial data (costs, ROI, revenue, expenses), refuse politely and say which role can access it."*
4. **Admin override:** `ai_settings.system_prompt` appended last (admin-configurable behavior/tone/extra instructions).

Answering style instruction: concise, cite concrete numbers from tool results, never invent data — if a tool returns empty, say so.

## 3. Tool calling loop (`ai/chat.py`)

1. Load session (create if none, title = first 40 chars of first message); load last 20 messages for history; persist the incoming user message.
2. Build messages: [system] + history + user. Attach JSON tool schemas **filtered to the requester's role** (§4).
3. Call OpenRouter. While the response contains `tool_calls` (max 4 iterations): for each call → verify tool ∈ role's allowlist (else return tool error `AI_TOOL_FORBIDDEN` into the loop — the model then apologizes), execute against the DB with the same SQLAlchemy session, append `{"role":"tool", ...}` results, call again.
4. Persist assistant message with `tool_calls` JSON (transparency: UI shows "🔧 checked vehicles (status=available)" chips). Return `{session_id, reply, tool_calls}`.

## 4. Tool registry (`ai/tools.py`) — name, args, returns, default role access

| Tool | Args | Returns | FM | D | SO | FA |
|---|---|---|---|---|---|---|
| `get_kpis` | – | dashboard KPI object | ✅ | ✅ | ✅ | ✅ |
| `get_vehicles` | `status?, type?, region?, q?, limit=20` | id, reg, name, type, capacity, odometer, region, status | ✅ | ✅ | ✅ | ✅ |
| `get_drivers` | `status?, license_valid?, q?, limit=20` | profile + expiry + score + status | ✅ | ✅ | ✅ | ✅ |
| `get_trips` | `status?, vehicle_reg?, driver_name?, date_from?, date_to?, limit=20` | code, route, vehicle, driver, cargo, status, dates | ✅ | ✅ | ✅ | ✅ |
| `get_maintenance` | `status?, vehicle_reg?` | jobs + costs | ✅ | ✅ | ✅ | ✅ |
| `get_expiring_licenses` | `days=30` | drivers with expiry ≤ N days | ✅ | ❌ | ✅ | ❌ |
| `get_vehicle_costs` | `vehicle_reg?` | report rows: fuel/maint/op-cost/revenue/ROI | ✅ | ❌ | ❌ | ✅ |
| `get_fuel_efficiency` | `vehicle_reg?` | km/L per vehicle | ✅ | ✅ | ❌ | ✅ |
| `explain_business_rule` | `topic` | matching BR text from knowledge | ✅ | ✅ | ✅ | ✅ |

Defaults live in `ai_settings.role_tool_permissions` JSONB (seeded from this table) — the admin UI edits it, so **access is admin-configurable per role**, exactly as required. Executors reuse existing service/query functions; read-only; every executor caps rows and strips fields the role may not see (e.g. `get_vehicles` omits `acquisition_cost` for D/SO).

## 5. Admin configuration — `/admin/ai-settings` (FM) ⇄ `GET/PUT /ai/settings`

Controls: Chatbot enabled (switch) · Model (text input + datalist of common OpenRouter ids: `anthropic/claude-3.5-haiku`, `openai/gpt-4o-mini`, `google/gemini-flash-1.5`, `meta-llama/llama-3.1-70b-instruct`) · Temperature (slider 0–1, step .05) · Max tokens · System prompt (textarea, 4k max) · **Permissions grid:** roles × tools checkbox matrix bound to `role_tool_permissions` · "Test connection" button → `POST /ai/chat` dry-run ("Reply with OK") showing latency + model. Save = PUT (FM only), audit-logged.

## 6. AI Trip Advisor — `POST /ai/trip-advisor`

Runs at trip creation/dispatch (frontend panel with "Analyze" button; auto-run before Dispatch confirm).

**Step 1 — deterministic (always, no LLM):** evaluate BR-2/3/4/5 for the proposed combo + soft risk factors: capacity utilization % (>90% flag), driver safety score (<60 flag), license expiring <30 d, vehicle overdue for maintenance (odometer since last closed maintenance > 10 000 km), long haul (>500 km) with low score driver.
**Step 2 — LLM summary:** feed structured findings; ask for a 3-sentence dispatch recommendation. If AI disabled → build the summary from templates.
**Response:** `verdict` = `block` (any hard BR failure) | `caution` (≥1 soft flag) | `go`; arrays of findings; summary. UI: verdict chip (danger/warn/ok), findings list, summary italic. **The Dispatch button is never disabled by `caution`** — advisory only; `block` reasons mirror what the server would reject anyway.

## 7. Chat UI (frontend `features/chat/`)

Floating launcher (signal-hued, chat glyph) → 380×560 panel (full-screen sheet on mobile): header "TransitOps Assistant" + model name small + New chat + history dropdown (sessions from API); message list (user right/`signal`-tinted, assistant left/`surface-2`; tool chips under assistant turns); input with Enter-to-send, disabled while streaming request pending ("Thinking…" shimmer). Suggested starter chips by role — D: "Which vehicles can I dispatch right now?" · SO: "Whose license expires this month?" · FA: "Which vehicle has the worst ROI?" · FM: "Fleet status summary". 503 → EmptyState "Assistant is turned off. Fleet Managers can enable it in AI Settings."

## 8. MCP exposure (T2 stretch — only if everything else is green)

The tool registry is deliberately MCP-shaped (name + JSON schema + executor). Stretch task BE-16: wrap it with `fastmcp` as `backend/mcp_server.py` exposing the same read-only tools over stdio, so the fleet can be queried from Claude Desktop/any MCP client — a 30-minute wow-demo. Auth: server runs with a service role = financial_analyst-equivalent read scope; document that per-user MCP auth is the production follow-up. **Do not start this before Hour 7.**

## 9. Guardrails & persistence checklist

- All chat turns + tool call payloads persisted (`chat_sessions`, `chat_messages`) — survives refresh; sessions listed per user only.
- Prompt-injection posture: tools are read-only; the model cannot mutate state; role allowlist enforced in code (not by the prompt); user content never interpolated into SQL (params only).
- Log every AI request (model, latency, token usage if returned) to `audit_logs` action `ai.chat`.
- Costs: default model is a cheap fast one; max_tokens capped; history window 20 messages.
