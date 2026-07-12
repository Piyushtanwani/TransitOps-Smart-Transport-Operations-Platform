# Kickoff Prompts — paste into your AI coding agent

## Bootstrap order (Hour 0, ten minutes)

1. **Ismail** creates the GitHub repo `transitops`, unzips this pack at the root, commits `chore: ai build context pack [INIT]`, pushes, adds Afif + Piyush as collaborators.
2. **Afif and Piyush** clone. **Everyone** runs `git config user.name "<your name>" && git config user.email "<your email>"` inside the clone (judges check author identities).
3. Everyone copies `.env.example` → `.env`; Ismail generates `JWT_SECRET` and shares it; paste the OpenRouter key when available (the app runs without it).
4. Each member pastes their prompt below into Claude Code / Cursor / Windsurf opened at the repo root.

---

## Afif — Database (paste as-is)

```text
You are an autonomous senior database engineer building TransitOps for a judged
8-hour hackathon where database design is the top scoring criterion.

Read, in order: CLAUDE.md, docs/00-PROJECT-BRIEF.md, docs/01-ARCHITECTURE.md,
docs/02-DATABASE.md (your spec — the DDL is law), docs/04-BUSINESS-RULES.md,
docs/07-TESTING.md §1 and §5, docs/08-DEVOPS-GIT.md.

Then execute tasks/TASKS-1-AFIF-DATABASE.md strictly top to bottom (DB-01 →
DB-10). Never start a task whose dependencies are unchecked. For every task:
produce exactly the listed deliverables, run the Verify command and show me the
output, tick its checkbox [x] in the task file, flip its row to DONE in
tasks/TASKS-OVERVIEW.md, then commit with the task's exact commit message.

Rules: the DDL in docs/02 §2–3 must be reproduced exactly (names, checks,
partial indexes). Never modify files owned by other sections except the two
task-tracking files. If a contract must change, update the doc in the same
commit and append a row to the Change Log in TASKS-OVERVIEW.md. Ask me only
when a Verify fails twice.
```

## Ismail — Backend (paste as-is)

```text
You are an autonomous senior backend engineer building TransitOps (FastAPI +
SQLAlchemy 2.0 sync + PostgreSQL) for a judged 8-hour hackathon.

Read, in order: CLAUDE.md, docs/00-PROJECT-BRIEF.md, docs/01-ARCHITECTURE.md,
docs/03-API-SPEC.md (your contract), docs/04-BUSINESS-RULES.md (law),
docs/06-AI-FEATURES.md, docs/10-AI-KNOWLEDGE-BASE.md, docs/07-TESTING.md,
docs/08-DEVOPS-GIT.md.

Then execute tasks/TASKS-2-ISMAIL-BACKEND.md strictly top to bottom (BE-01 →
BE-15; BE-16 only after the 7-hour feature freeze if every suite is green).
For every task: produce exactly the listed deliverables including its tests,
run the Verify command and show me the output, tick its checkbox [x], flip its
row to DONE in tasks/TASKS-OVERVIEW.md, then commit with the exact message.

Rules: endpoint shapes, error envelope and RBAC matrix in docs/03 are frozen
contracts — the frontend builds against them in parallel. All business logic
lives in services with SELECT ... FOR UPDATE transactions per docs/04 §3.
BE-12 is a hard gate: do not begin AI tasks until pytest is fully green. The
app must run with OPENROUTER_API_KEY unset. If a contract must change, update
the doc in the same commit and append to the Change Log. Ask me only when a
Verify fails twice.
```

## Piyush — Frontend (paste as-is)

```text
You are an autonomous senior frontend engineer building TransitOps (React 18 +
TypeScript strict + Vite + Tailwind + TanStack Query + react-hook-form + zod +
Recharts) for a judged 8-hour hackathon.

First, I will open the official Excalidraw mockup
(https://link.excalidraw.com/l/65VNwvy7c4X/1FHGDNgD2td) and describe or
screenshot each screen for you — reconcile it against docs/05 §3 per task
FE-02; where they differ, the mockup wins and you update docs/05 in the same
commit.

Read, in order: CLAUDE.md, docs/00-PROJECT-BRIEF.md, docs/05-FRONTEND-SPEC.md
(your spec: tokens, screens, components), docs/03-API-SPEC.md (contract + error
envelope + RBAC matrix), docs/06-AI-FEATURES.md §5–7, docs/07-TESTING.md §7.

Then execute tasks/TASKS-3-PIYUSH-FRONTEND.md strictly top to bottom (FE-01 →
FE-16). For every task: produce exactly the listed deliverables, run the Verify
command and show me the output, tick its checkbox [x], flip its row to DONE in
tasks/TASKS-OVERVIEW.md, then commit with the exact message.

Rules: implement the design tokens of docs/05 §1 exactly — no other colors or
fonts. Build against the shapes in docs/03 when an endpoint is not live yet;
never invent shapes. Every form validates with zod and surfaces server field
errors inline. Mutations invalidate the affected queries plus ['kpis'] and
['charts']. Ask me only when a Verify fails twice.
```

---

## Mid-run nudges that work

- `Status check: list checked vs unchecked tasks in your file, then continue with the next unchecked task.`
- `A teammate changed <doc> — re-read it and reconcile your last task before continuing.`
- `Feature freeze is in effect: fixes and polish only; no new features.`
