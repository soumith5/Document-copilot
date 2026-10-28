# Document Copilot — implementation checklist

Work top to bottom. Check items off as you go (`[x]`). Each phase has a **gate** — don't skip ahead until the gate passes.

---

## Backend or frontend first?

**Start with foundation + backend, then bring the frontend online once auth and a stub API exist.**


| Order                                       | Why                                                                                                         |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1. Supabase + env                           | Both services depend on the same project URL, keys, and Postgres schema.                                    |
| 2. Backend scaffold + schema                | The product lives in retrieval, grounding, and persistence. You can test ingestion and search without a UI. |
| 3. Auth (backend verify + frontend sign-in) | Every chat request needs a verified Supabase JWT before retrieval or LLM work.                              |
| 4. Chat API stub + frontend shell           | Wire the streaming contract early so UI and backend evolve against the same interface.                      |
| 5. Ingestion → retrieval → agent            | Fill in the real intelligence layer on the backend.                                                         |
| 6. Chat UI polish                           | Citations, source passages, and error states once grounded answers work.                                    |


The frontend stays **thin** (session, chat UI, streaming client). The backend stays **authoritative** (retrieval, LLM, citations, DB writes). Building backend-first avoids a pretty UI with nothing to talk to.

Reference: [architecture.md](architecture.md) § Implementation Sequence · [client-brief.md](client-brief.md) · setup guides in [guides/](guides/).

---



## Phase 0 — Prerequisites

**Gate:** tools installed, corpus downloaded, external accounts ready.

- [x] Install Python 3.12+, uv, Node 20+, pnpm (see [README.md](../README.md))
- [x] Create Supabase project; save URL, anon key, service_role key, direct DB URL ([supabase-setup.md](guides/supabase-setup.md))
- [x] Create OpenAI API key (needed from Phase 5 onward)
- [x] Configure `USER_AGENT` in `data/download.py` and run `uv run data/download.py` from repo root
- [x] Confirm `data/downloads/manifest.json` lists AAPL, MSFT, NVDA, AMZN, GOOGL 10-Ks (2021–2025)

---



## Phase 1 — Backend scaffold & database

**Gate:** `uv run uvicorn app.main:app --reload` starts; `uv run alembic upgrade head` applies schema to Supabase.

- [x] Init backend deps per [backend-setup.md](guides/backend-setup.md) (`uv sync`, add FastAPI, SQLAlchemy, Alembic, etc.)
- [x] Create `backend/app/main.py` — FastAPI app, CORS, health route
- [x] Create `backend/app/config.py` — pydantic-settings for all env vars (fail fast if missing)
- [x] Copy `backend/.env.example` → `backend/.env` and fill Supabase + OpenAI + `DATABASE_URL` (direct connection)
- [x] Init Alembic; wire `alembic/env.py` to import SQLAlchemy metadata from `app/database/models.py`
- [x] Define SQLAlchemy models: `profiles`, `chat_threads`, `chat_messages`, `message_citations`, `source_documents`, `document_chunks`
- [x] First migration — explicitly add in review:
  - [x] `create extension if not exists vector`
  - [x] `vector(1536)` embedding column on chunks
  - [x] generated `tsvector` column for full-text search
  - [x] HNSW index (vectors) and GIN index (tsvector / metadata)
  - [x] RLS policies scoped to authenticated user
- [x] Run `uv run alembic upgrade head` against Supabase
- [x] Add `structlog` logging and basic request logging middleware

---



## Phase 2 — Frontend scaffold

**Gate:** `pnpm dev` serves the app; env validation fails loudly if vars are missing.

- [x] Init frontend per [frontend-setup.md](guides/frontend-setup.md) (Vite React TS, Tailwind, shadcn, React Router)
- [x] Create `src/lib/env.ts` — validate `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- [x] Copy `frontend/.env.example` → `frontend/.env`
- [x] Add base layout, routing shell (`/login`, `/chat`, `/chat/:threadId`)
- [x] `pnpm tsc --noEmit` and lint pass

---



## Phase 3 — Auth end-to-end

**Gate:** analyst can sign up / sign in in the browser; backend rejects requests without a valid token.

- [x] Supabase dashboard: email provider on; disable email confirm for local dev if needed
- [x] `src/lib/supabase.ts` — browser Supabase client
- [x] Login / sign-up page (Driftwood email only — no SSO)
- [x] Protected routes — redirect unauthenticated users to `/login`
- [x] `backend/app/auth/dependencies.py` — verify `Authorization: Bearer <token>` via Supabase Auth; expose `get_current_user`
- [x] `backend/app/database/supabase.py` — user-scoped and service-role clients
- [x] Smoke test: authenticated `GET /health` or `/me` returns user; missing token → 401

---



## Phase 4 — Chat plumbing (stub first)

**Gate:** user can open a thread, send a message, and see a streamed stub reply in the UI.

- [x] `src/lib/http.ts` — fetch wrapper with bearer token injection and typed errors
- [x] `src/lib/api.ts` — list/create threads, load message history (FastAPI, not direct Supabase writes)
- [x] Backend routes: create thread, list threads, get thread messages (user-scoped)
- [x] `POST /chat/stream` — AI SDK-compatible streaming with a **stubbed** assistant response (no LLM yet)
- [x] `backend/app/chat/streaming.py` + `messages.py` — wire format conversion
- [x] Frontend: Vercel AI SDK `useChat` + `DefaultChatTransport` pointed at FastAPI `/chat/stream`
- [x] Persist user + assistant messages to Supabase after stream completes
- [x] CORS configured (`ALLOWED_ORIGINS`) so browser can reach local backend

---



## Phase 5 — Ingestion pipeline

**Gate:** all 25 sample 10-Ks are in `source_documents` + `document_chunks` with embeddings; you can query chunks by document ID in SQL.

- [x] HTML → normalized Markdown parser for SEC filings (preserve section structure, page hints where possible)
- [x] Chunking strategy — sized for retrieval (section-aware splits, metadata: ticker, company, filing type, year, accession, page/section)
- [x] Ingestion CLI or admin endpoint: read `data/downloads/manifest.json`, process each filing once (idempotent)
- [x] OpenAI embeddings batch write to `document_chunks.embedding`
- [x] Populate `search_vector` (generated tsvector) on insert/migration
- [x] Store full filing metadata in `source_documents` (source URL, filing date, company, etc.)
- [x] Verify: re-running ingestion does not duplicate documents

---



## Phase 6 — Retrieval

**Gate:** given a test query (e.g. "Apple Services revenue mix"), hybrid search returns relevant chunks with metadata.

- [x] `retrieval/queries.py` — pgvector semantic search over `document_chunks`
- [x] `retrieval/queries.py` — Postgres full-text search over `search_vector`
- [x] `retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [x] `retrieval/retriever.py` — fetch top chunks + neighboring context for grounding
- [x] Backend unit tests for retrieval ranking on known corpus snippets
- [x] Optional: bounded agent tools `search_filings`, `read_chunk`, `read_surrounding_chunks`

---



## Phase 7 — LLM agent & grounding (trust contract)

**Gate:** real answers cite only retrieved passages; insufficient evidence → explicit refusal; citation validation tests pass.

This phase satisfies the client brief's **trust** requirements: never invent facts, always cite, show underlying passage.

- [x] `assistant/agent.py` — PydanticAI agent with typed deps and `GroundedAnswer` output
- [x] `assistant/instructions.md` — system prompt: corpus-only answers, cite every claim, no stock picks, refuse when evidence is weak
- [x] `chat/orchestrator.py` — one turn: retrieve → agent → validate → stream → persist
- [x] Replace stub stream with real PydanticAI streaming through `/chat/stream`
- [x] `grounding/validator.py` — every citation maps to a retrieved chunk; fail closed on validation errors
- [x] `message_citations` persistence linked to assistant messages
- [x] Backend tests: citation extraction, grounding enforcement, "not in corpus" path
- [x] Manual spot-check against [client-brief example questions](client-brief.md#example-analyst-questions) (at least 3–5)

---



## Phase 8 — Frontend chat experience

**Gate:** analyst workflow from the brief works in the browser — ask, stream, verify citations, revisit history.

- [x] Message list with streaming indicator and error states
- [x] Citation chips on assistant messages (filing, company, date, page/section)
- [x] Source passage panel — one-click to view excerpt + link to filing metadata
- [x] Thread sidebar — list past conversations; create new thread
- [x] Empty states and loading skeletons
- [x] Friendly errors for 401 / 403 / 404 / network / CORS (distinct copy per class)
- [x] Responsive layout suitable for desktop analysts (mobile out of scope)

---



## Phase 9 — Deploy & pilot readiness

**Gate:** deployed stack usable by a 5-analyst pilot for one week; example questions return cited, verifiable answers.

- [x] Railway: backend service (Uvicorn) + frontend service (Vite static build)
- [x] Production env vars on Railway; `service_role` key backend-only
- [x] Supabase: re-enable email confirmation (or approved dev bypass policy)
- [x] Run ingestion against production Supabase once
- [x] End-to-end smoke test on deployed URLs (sign in → chat → citation → history)
- [ ] Run through all 10 [example analyst questions](client-brief.md#example-analyst-questions); document any gaps
- [ ] Confirm out-of-scope guardrails: no trading advice, no external data, refuses over-inference (e.g. Q10 on generative AI margins)

---



## Definition of done (client brief)

The pilot succeeds when **5 senior analysts** use it for a week and report **≥ 3 hours saved per analyst per week**.

Before inviting the pilot:

- [ ] Answers are grounded in the corpus only — hallucinations treated as P0 bugs
- [ ] Every factual claim has a citation to filing + page/section
- [ ] Analysts can verify any claim via shown passage in one click
- [ ] Each analyst sees only their own conversation history
- [ ] Corpus covers sample 10-Ks (AAPL, AMZN, GOOGL, MSFT, NVDA, 2021–2025) — expand later per brief (10-Qs, broader S&P 500) if time allows

---



## Suggested weekly focus (optional)


| Week | Focus                                                       |
| ---- | ----------------------------------------------------------- |
| 1    | Phases 0–3 — Supabase, backend scaffold, schema, auth       |
| 2    | Phases 4–5 — chat stub + full ingestion of sample corpus    |
| 3    | Phases 6–7 — hybrid retrieval, PydanticAI agent, grounding  |
| 4    | Phases 8–9 — citation UI, deploy, pilot question validation |


Adjust pace as needed; the phase gates matter more than the calendar.