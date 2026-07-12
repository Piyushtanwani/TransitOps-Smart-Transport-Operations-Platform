# TransitOps — AI Build Context Pack

**Event:** Odoo Hackathon (8 hours) · **Team:** Piyush (Frontend) · Ismail (Backend) · Afif (Database)

This repository-ready pack contains **everything an AI coding agent (Claude Code, Cursor, Windsurf, Copilot Workspace) needs to build TransitOps end-to-end with zero additional human context.** Drop these files into the root of an empty git repository and instruct the agent: *"Read CLAUDE.md, then execute your assigned task file."*

## How to use (per team member)

1. `git clone` the shared repo containing this pack.
2. Open your AI coding tool in the repo root.
3. Prompt: `Read CLAUDE.md and docs/. You are executing tasks/TASKS-<N>-<YOURNAME>-<AREA>.md. Complete tasks strictly in order, respecting the Depends-on column. After each task: run its verification command, mark the checkbox [x], update tasks/TASKS-OVERVIEW.md, and commit with the given message.`
4. Sync with teammates at the checkpoints defined in `tasks/TASKS-OVERVIEW.md` (end of Hour 1, 3, 5, 7).

## File map

| File | Purpose | Primary owner |
|---|---|---|
| `CLAUDE.md` | Master instructions, conventions, guardrails, commands | All |
| `docs/00-PROJECT-BRIEF.md` | Problem statement, users, judging criteria, scope tiers | All |
| `docs/01-ARCHITECTURE.md` | System design, tech stack + rationale, repo layout | All |
| `docs/02-DATABASE.md` | Complete PostgreSQL DDL, ERD, constraints, seed data | Afif |
| `docs/03-API-SPEC.md` | Every endpoint: schemas, status codes, RBAC matrix | Ismail |
| `docs/04-BUSINESS-RULES.md` | All 10 mandatory rules, state machines, enforcement map | Ismail + Afif |
| `docs/05-FRONTEND-SPEC.md` | Design system, every screen/component, mockup fidelity | Piyush |
| `docs/06-AI-FEATURES.md` | OpenRouter chatbot (RBAC-aware, admin-configurable), Trip Advisor, MCP stretch | Ismail |
| `docs/07-TESTING.md` | Test strategy, the 10 business-rule tests, E2E demo script | All |
| `docs/10-AI-KNOWLEDGE-BASE.md` | Ready-made chatbot static context (paste in BE-13) | Ismail |
| `KICKOFF-PROMPTS.md` | Copy-paste AI-agent prompts per member + bootstrap order | All |
| `docker-compose.yml`, `Makefile`, `.gitignore` | Ready-made infrastructure files (verify, do not rewrite) | All |
| `docs/08-DEVOPS-GIT.md` | Docker Compose, env vars, Makefile, git workflow | All |
| `docs/09-DEMO-SCRIPT.md` | 3-person presentation plan mapped to judging criteria | All |
| `tasks/TASKS-OVERVIEW.md` | Live progress board, dependency graph, hour timeline | All |
| `tasks/TASKS-1-AFIF-DATABASE.md` | Section 1 — Database (DB-01…DB-10) | Afif |
| `tasks/TASKS-2-ISMAIL-BACKEND.md` | Section 2 — Backend (BE-01…BE-16) | Ismail |
| `tasks/TASKS-3-PIYUSH-FRONTEND.md` | Section 3 — Frontend (FE-01…FE-16) | Piyush |
| `.env.example` | All environment variables | All |

## MCP server (T2 stretch, BE-16)

`backend/mcp_server.py` exposes the same read-only AI tool registry
(`app/services/ai/tools.py`) over the MCP stdio transport, so any MCP client —
including **Claude Desktop** — can query the fleet directly.

- Install the extra: `pip install -e ".[mcp]"` (adds `fastmcp`).
- Run: `python mcp_server.py` (from `backend/`).
- Auth: runs with a fixed service role equivalent to `financial_analyst` (the
  broadest read scope). Per-user MCP auth is the production hardening step.
- Connect from Claude Desktop: add to its MCP config —
  ```json
  { "mcpServers": { "transitops": {
      "command": "python",
      "args": ["/absolute/path/to/backend/mcp_server.py"]
  } } }
  ```

## Non-negotiables (from the judges)

- PostgreSQL running locally/Docker. **No Firebase, Supabase, or MongoDB Atlas.**
- All data persistent in PostgreSQL — including chat history and AI settings. **No static JSON as the final data source.**
- Robust input validation with human-readable feedback on every form and endpoint.
- All three members commit regularly under their own git identity.
- AI features must add real value: RBAC-aware fleet chatbot + AI Trip Advisor (dispatch risk analysis).
