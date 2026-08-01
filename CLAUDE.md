# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

SmartHunt is a **single-user** AI-powered job-hunting automation platform — a personal "AI Career
Operating System," not a SaaS product. The backend (`backend/`) is a FastAPI service that discovers
jobs across many external job boards, scores them against the owner's resume via AI, generates a
tailored resume/cover letter per job, and drives a real browser (Playwright) to auto-apply, stopping
only for CAPTCHA/MFA or an unanswerable question. `frontend/` is a Next.js 16 App Router UI being
built incrementally (see "Project status & roadmap" below for what exists so far).

The Python package lives at `backend/src/smarthunt/`. The repo root is a uv workspace whose only
member is `backend/`; `pyproject.toml` at the root and `backend/pyproject.toml` both define pytest
config pointing at `backend/tests`.

### Single-user architecture — a deliberate, permanent constraint

This is a standing architectural decision, not a temporary shortcut: SmartHunt serves **one owner
only**. There is intentionally no multi-tenant design, no organizations/teams, no roles/permissions,
no admin panel, no self-service registration flow, no "forgot password" / email verification. Every
row in every table belongs to the single owner. Do not add multi-user scaffolding (tenant IDs, role
checks, invite flows, etc.) — if multi-user support is ever wanted, the docs treat that as an
entirely separate future phase, not something to hedge for now. Auth only needs: login, logout,
change password.

## Commands

Run all commands from `backend/` unless noted. Dependency management is via `uv`.

```bash
uv sync                                    # install dependencies

uv run ruff check .                        # lint
uv run black --check --target-version py312 .   # format check (use `black .` to fix)
uv run python -m compileall src            # syntax/compile check

uv run pytest --envfile=../.env            # run full test suite (as CI does)
uv run pytest tests/test_jobs.py           # run a single test file
uv run pytest tests/test_jobs.py::test_name -v   # run a single test

uv run alembic upgrade head                # apply DB migrations
uv run alembic revision --autogenerate -m "message"   # new migration

uv run uvicorn smarthunt.main:app --reload --host 0.0.0.0 --port 8000   # run the API locally
```

Local infra (Postgres + Valkey/Redis) is provided by `docker-compose.yml` at the repo root:
`docker compose up -d postgres valkey`.

### Secrets

Non-secret defaults live in the repo-root `.env` (git-ignored, already present locally). Anything
that shouldn't live inside the project directory at all — job-site login credentials for the
Playwright auto-apply flow (LinkedIn/Bayt/GulfTalent/Wuzzuf), AI provider keys, Telegram — lives in
`/home/badr/secrets/secret.env`, outside the repo entirely. `docker-compose.yml`'s `backend` service
loads both via `env_file`. For running the API directly with `uv run uvicorn` (outside Docker), source
both first so `Settings` picks them up from the environment:

```bash
set -a && source /home/badr/secrets/secret.env && source ../.env && set +a
uv run uvicorn smarthunt.main:app --reload --host 0.0.0.0 --port 8000
```

Never print the contents of `/home/badr/secrets/secret.env` (or paste its values anywhere) — treat
it the same as any other credential store.

CI (`.github/workflows/ci.yml`) runs, in order: `ruff check`, `black --check`, `compileall`,
`pytest --envfile=../.env`, then `helm lint ../helm/smarthunt`. Match this before considering work done.

### Tests

- Tests live in `backend/tests/`, mirroring package names (e.g. `test_jobs.py`, `test_scheduler_*.py`).
- `tests/conftest.py` forces `APP_ENV=test` and injects fixed test JWT/secret keys, points at
  `TEST_DATABASE_URL` (defaults to a local `smarthunt_test` Postgres DB), and **runs
  `alembic upgrade head` against that test database automatically** via an autouse session
  fixture — a running, migratable Postgres instance is required to run tests at all (no SQLite/mocked DB).
  `.env.test` in `backend/` is loaded first for any additional overrides.
- Use the `client` fixture (httpx `AsyncClient` over the FastAPI app) and `db_session` fixture for
  endpoint tests; `app.dependency_overrides[get_db]` is wired for you.

## Architecture

### Module layout

The codebase is organized as ~40 vertical feature packages under `smarthunt/` (e.g. `auth/`,
`jobs`-related `career/`, `resume/`, `search/`, `scheduler/`, `providers/`, `notifications/`,
`apply_queue/`, `audit/`, `events/`, `favorites/`, `job_notes/`, `job_tags/`, `saved_searches/`,
`settings/`, `dashboard/`, `activity/`, `recommendation/`, `recruitment/`, `cover_letter/`, `ai/`),
rather than by technical layer. Within each package, the recurring pattern is:

- `router.py` or `api.py` — FastAPI `APIRouter`, thin HTTP layer
- `service.py` — business logic, exposed as a module-level singleton instance (e.g.
  `event_service = EventService()`, `provider_registry = ProviderRegistry()`) that routers import directly
- `schemas.py` — Pydantic request/response models
- `models.py` — SQLAlchemy ORM models (some packages instead define models under
  `smarthunt/database/models/`, e.g. `Job`, `User`, `Resume`, `Application`)
- `repository.py` (where present) — DB query layer between service and models

All routers are wired together in `smarthunt/api/routes/router.py` (`api_router`), which is mounted
in `smarthunt/api/main.py` under `settings.API_V1_STR` (`/api/v1`). When adding a new feature
package with HTTP endpoints, register its router there.

`smarthunt/database/models/__init__.py` re-exports every ORM model across all packages — this is
what Alembic's autogenerate and `Base.metadata` see, so new models must be added there too.

### Providers (job board integrations)

`smarthunt/providers/<site>/provider.py` — one package per external job board (LinkedIn, Indeed,
GulfTalent, Bayt, Wuzzuf, NaukriGulf, MonsterGulf, Wzayef, Tanqeeb, DrJobs, ForasnaGulf). Each
implements `BaseProvider` (`smarthunt/providers/base/provider.py`): an async `search(query,
location, page, limit) -> list[DiscoveredJob]`, plus capability flags (`supports_login`,
`supports_apply`, `supports_resume_upload`, `supports_cover_letter`).

**Only 4 of the 11 providers currently set `supports_login`/`supports_apply` to `True`: LinkedIn,
Bayt, GulfTalent, Wuzzuf.** The other 7 (Indeed, NaukriGulf, MonsterGulf, Wzayef, Tanqeeb, DrJobs,
ForasnaGulf) inherit the `BaseProvider` defaults (all `False`) — they are discovery/search-only
today. Auto-apply (`recruitment/auto_apply_worker.py`, `apply_queue/`) only works where
`supports_apply` is `True` and credentials for that site exist in `Settings` (currently only
`linkedin_email`/`linkedin_password` — Bayt/GulfTalent/Wuzzuf credential fields still need adding).
Even within a supported site, not every posting is auto-appliable: many job boards (LinkedIn
included) mix native "Easy Apply"-style postings with ones that redirect to the employer's own
external ATS (Greenhouse, Workday, etc.), which the current Playwright layer does not handle.

`smarthunt/providers/registry.py` (`provider_registry`) fan-outs `search()` across every provider
concurrently via `asyncio.gather(..., return_exceptions=True)` and normalizes results to
`DiscoveredJob` — a single provider failing/raising does not fail the whole search.
`smarthunt/providers/manager.py` (`provider_manager`) is a separate registration-based lookup used
for provider metadata/statistics endpoints. `smarthunt/providers/circuit_breaker.py` and
`circuit_registry.py` guard against a flaky provider being hammered repeatedly.

### Browser automation / auto-apply

`smarthunt/browser/` wraps Playwright (`playwright/` engine, `session/` for session lifecycle,
`form_detector.py`/`form_filler.py`/`question_answerer.py`/`question_classifier.py` for filling out
application forms, `navigation.py`, `provider_executor.py`). `smarthunt/recruitment/auto_apply_worker.py`
and `smarthunt/apply_queue/` drive the actual apply flow, backed by AI-generated answers to unknown
questions (`browser/unknown_questions.py`) via the `ai/` package.

### Scheduler

`smarthunt/scheduler/scheduler.py` holds a global `AsyncIOScheduler` (APScheduler) instance.
`jobs.py` defines the scheduled discovery/apply jobs; `execution.py`/`execution_service.py` track
run outcomes; `locks/` implements distributed run locking (DB-backed, see `scheduler_locks` table)
so only one instance executes a given job; `failed_job*.py` and `retry_worker.py` handle
failure tracking and retries; `history/` persists execution history for the API.

### AI integration

`smarthunt/ai/` is a provider-agnostic AI client layer (`factory.py` builds a client from
`settings.ai_provider`; `providers/` holds concrete implementations e.g. OpenAI/Azure/Ollama;
`client.py`/`base.py` define the interface; `health.py` for provider health checks). Consumed by
`resume/` (parsing, profile building, review), `cover_letter/`, `career/` (advice), `matching/`
(resume-to-job scoring), and the browser auto-apply question answerer.

### Cross-cutting infrastructure

- `smarthunt/core/config.py` — single `Settings` (pydantic-settings) object read from environment /
  `.env`, exposed as the module-level `settings` singleton. In `production` (`app_env=="production"`)
  it enforces required secrets are set and that debug mode is off.
- `smarthunt/core/lifespan.py` — FastAPI lifespan: runs Alembic migrations, then a DB health check,
  on every startup, before the app starts serving; closes the DB engine on shutdown.
- `smarthunt/database/session.py` — async SQLAlchemy engine/session (`AsyncSessionLocal`),
  `Base` declarative base, and the `get_db` dependency (auto-commits on success, rolls back on
  exception).
- `smarthunt/middleware/` — `RateLimitMiddleware` (skipped when `app_env=="test"`),
  `SecurityHeadersMiddleware`, `RequestIDMiddleware`, `RequestLoggingMiddleware`; all registered in
  `api/main.py` in a specific order (rate limit → security headers → request id → request logging →
  CORS).
- `smarthunt/events/` — an internal event log (`EventLog` model) that other services publish
  domain events to (`event_service.publish(db, event)`), instrumented with Prometheus counters.
- `smarthunt/audit/` — separate persisted audit trail (`AuditLog`) for security/compliance-relevant actions.
- `smarthunt/metrics/` — Prometheus metrics setup (`setup_metrics(app)` in `main.py`) plus
  per-domain metric definitions (business, audit, events, idempotency, scheduler).
- `smarthunt/tracing/` — OpenTelemetry tracer setup.
- `smarthunt/idempotency/` — idempotency-key support for write endpoints prone to duplicate
  submission (e.g. apply actions).

### Deployment

Container/K8s/OpenShift-oriented: `backend/Dockerfile`, `k8s/`, `helm/smarthunt/`, `gitops/`,
`docker-compose.yml` (local Postgres + Valkey + backend). `Makefile` targets (`build`, `deploy`,
`logs`, `status`, `test`) drive an OpenShift (`oc`) deployment, not local dev — `test` there hits a
live route, it's not the unit test suite.

`backend/Dockerfile` assumes a **repo-root** build context (`COPY backend/requirements.txt .`,
`COPY backend/ .`), matching how the OpenShift `BuildConfig`/`Makefile`'s `oc start-build ... --from-dir=.`
builds it. `docker-compose.yml`'s `backend` service must therefore use `context: .` +
`dockerfile: backend/Dockerfile`, not `context: ./backend` — the latter silently breaks the build
past the first cached layer (found and fixed 2026-07-31; watch for this if the Dockerfile or compose
file are touched independently, since nothing catches the mismatch except actually rebuilding).

On this dev machine, `postgres`/`valkey` actually run with `--network host` (not the compose bridge
network the file used to imply via `ports:` mappings) — `docker-compose.yml` now matches that with
`network_mode: host` on all three services, which is also why `.env`'s `DATABASE_URL`/`REDIS_URL`
can just say `localhost` with no per-service override needed. If this is ever moved to a machine
where postgres/valkey are set up differently, this will need revisiting.

`/home/badr/secrets/secret.env` (loaded as a second `env_file` after `.env`) must never define a key
with an **empty** value for something `.env` already sets for real — `env_file` merge order means a
present-but-empty line silently overrides and blanks out the real one (hit this with `SECRET_KEY`/
`JWT_SECRET_KEY` 2026-07-31: causes `jwt.exceptions.InvalidKeyError: HMAC key must not be empty` at
login, not at startup, so it doesn't fail fast). Only put a key in `secret.env` at all once it has a
real value to contribute.

**A successful `oc start-build` does NOT mean the fix is live** — found 2026-08-01 after several
builds in a row succeeded and pushed to the `smarthunt-backend:latest` image tag, yet the running
pod was still 3+ hours old and serving pre-fix code. `deployment.apps/smarthunt-backend` is a plain
Kubernetes `Deployment` with **no `ImageChange` trigger** (`oc get deployment smarthunt-backend -o
yaml` has no `triggers:` section) — pushing a new image to the same `:latest` tag doesn't change the
pod spec, so the Deployment controller sees no diff and never creates a new ReplicaSet on its own.
`imagePullPolicy: Always` only matters once a *new* pod actually starts. After any build you expect
to be live, run `oc rollout restart deployment/smarthunt-backend` and then `oc rollout status
deployment/smarthunt-backend --timeout=180s` — don't just check the build succeeded. Verify with a
real request afterward (e.g. curl a field/endpoint that only exists in the new code), not just a
generic health check, since the pod can be "Running" and healthy while still serving the old image.

## Frontend

`frontend/` is a Next.js 16 (App Router, Turbopack) + TypeScript + Tailwind v4 + shadcn/ui app, added
2026-07-31. **Next.js 16 has real breaking changes from older training data** — the scaffold's own
`frontend/AGENTS.md` flags this; when in doubt, check `frontend/node_modules/next/dist/docs/`. Known
deltas already hit: `params`/`searchParams` are `Promise`s with no sync-access fallback (unlike 15);
`cookies()`/`headers()`/`draftMode()` are async-only; `middleware.ts` is replaced by `proxy.ts`
(`export function proxy(request: NextRequest)`, Node runtime only, no `edge` option); Turbopack is
the default for both `next dev` and `next build`. shadcn/ui has also moved on from the classic
`form.tsx` (react-hook-form wrapper) to composable `Field`/`FieldGroup`/`FieldLabel`/`FieldError`
primitives (`npx shadcn add field`, not `add form`) — plain `react-hook-form` `useForm`/`register` is
used directly against them, no context-wrapper magic. This shadcn version has also switched its
underlying primitives from **Radix UI to Base UI** (`@base-ui/react`, imported per-component e.g.
`import { Dialog as DialogPrimitive } from "@base-ui/react/dialog"`) — there is no `asChild` prop on
triggers (`Dialog`, etc.); style the trigger directly with the exported `buttonVariants()` className
instead of wrapping a `<Button asChild>` around it.

```bash
cd frontend
npm run dev      # dev server on :3000 (Turbopack)
npm run build    # production build
npm run lint     # eslint
npx tsc --noEmit  # typecheck
```

- API calls go through `next.config.ts`'s `rewrites()`, which proxies `/api/:path*` to
  `${BACKEND_ORIGIN}/api/:path*` (defaults to `http://localhost:8000`) — the browser only ever talks
  to the Next.js origin, so there's no CORS to configure and no backend URL baked into client code.
  Override with `BACKEND_ORIGIN=http://localhost:PORT npm run dev` when testing against a
  non-default backend instance.
- `src/lib/api-client.ts` — shared `axios` instance (`baseURL: "/api/v1"`), attaches the bearer token
  from `src/lib/auth.ts` (`localStorage`, key `smarthunt_token`) to every request, clears it on a 401.
  This is a pragmatic single-user choice, not hardened against XSS token theft — revisit if that ever
  matters (e.g. move to an httpOnly cookie issued by the backend) before this stops being a
  local-only personal tool.
- `src/lib/query-provider.tsx` — TanStack Query provider, mounted once in `src/app/layout.tsx`.
- `src/lib/auth-api.ts` — typed wrappers (`login`, `getCurrentUser`) around the real
  `/api/v1/auth/*` endpoints from Sprint 0's auth fix.
- Root `/` (`src/app/page.tsx`) is a client-side auth gate: redirects to `/login` if no token, fetches
  `/auth/me` if one exists, and is the natural place each subsequent Sprint replaces with the real
  dashboard rather than a placeholder.

## Project status & roadmap

Full project history, vision, and rationale live in `/home/badr/SmartHunt-Project-document.docx`
(the project owner's living reference doc, referred to below as "the project doc") — read it for
context on *why*, not just *what*. As of the doc's last update (post "Sprint 42"): 228/228 backend
tests passing, backend deployed successfully on OpenShift. Per the doc's own completion table:
Backend architecture, DB, AI layer, resume/cover-letter/matching engines, scheduler, event bus,
notifications, audit, metrics, logging, health checks, OpenShift deployment, Docker, and test
infra are all listed as 100%; REST API foundation and browser-automation infra ~95%; **Frontend and
Web Dashboard are 0%, end-to-end user experience is ~10%.** (This was true as of the doc's last
update — **it is no longer true**: the frontend now exists and every page below has been built.
Don't re-scaffold it from scratch; check `frontend/src/app/(app)/` first.) The stated Phase 2
priority order is:

1. Finish converting any remaining multi-user-shaped code to the single-user model above.
2. Build a professional frontend (doc's proposal: Next.js + TypeScript + Tailwind + shadcn/ui +
   TanStack Query/Table + React Hook Form + Zod + Axios + Recharts).
3. Wire the frontend to the existing REST APIs (`/api/v1/...`) — no direct DB access from the frontend.
4. Build out the full dashboard (jobs, applications, resume, cover letters, AI assistant, scheduler,
   notifications, settings, system health).
5. Exercise the complete real-world scenario end to end (resume upload → discovery → matching →
   cover letter → apply via Playwright → track status → notify), including a real LinkedIn account.
6. UX polish.

**Current state (as of 2026-08-01, superseding the "0%" line above):** all of the above is built.
`frontend/src/app/(app)/` has: Dashboard (stats + a real Recent Activity feed), Jobs search
(with real resume-match scoring via `sort=score`, and a no-sponsorship-language badge),
Favorites (full job data via a joined query, not just bare IDs), Resume, Cover Letter,
Applications (with a needs-follow-up flag for stale ones), AI Assistant, Scheduler,
Notifications, Settings, System Health — each with a sidebar icon and matching page-header icon.
The AI layer is wired to a real local Ollama provider (not a mock), used for deep job analysis.
Dark mode is the permanent default (`className="dark"` on `<html>`, not user-toggleable).
Local dev mirrors prod via `docker compose build backend && docker compose up -d --no-deps backend`
(never `up -d backend` — that recreates `postgres`/`valkey` too, which conflicts with the
long-running host containers holding real data) — the frontend proxies to that container on :8000.
The frontend itself runs as a production server on this host (`npm run build && npm run start -- -p
3000`, backgrounded via `nohup ... & disown`), not `next dev` — switched 2026-08-01 specifically to
stop `frontend/.next` being continuously rewritten during `oc start-build`'s binary tar (see below).
After frontend changes, rebuild+restart: kill the `next-server` process, `npm run build`, relaunch.
OpenShift builds: `oc start-build smarthunt-backend --from-dir=. --wait`; a `FetchSourceFailed` or a
dropped `oc` connection mid-upload is usually transient — check `oc get builds`, the build often
keeps running server-side even after the CLI's own connection resets; retry only if it's genuinely
not progressing.
`smarthunt/search/` had ~11 files (cache*, deduplication, ranking, repository, database_router,
history*, models, schemas) that were dead scaffolding from an abandoned earlier attempt — removed
2026-08-01; the real search implementation is `services/search_service.py` + `search/filtering.py`.
If you find query params or sort/filter options that look plausible but don't affect results,
verify they're actually wired before trusting them — this codebase has had more than one of those.

**Do not treat the doc's "Production Ready" / "100%" labels as verified fact without checking the
code** — they describe architecture completeness, not necessarily wiring correctness.
`smarthunt/auth/router.py` returning a hardcoded mock JWT instead of calling the real `AuthService`
was one historical example of this (since fixed — it now properly uses
`smarthunt/auth/services/auth_service.py`). A second, more severe example found and fixed
2026-08-01: the three APScheduler-registered automatic discovery jobs
(`scheduler/jobs.py::discover_python/linux/devops`, meant to run every 1-3h per
`services/scheduler_service.py`) called `async with track_scheduler_execution(...)`, but that
function's actual signature took a handler callable and returned a plain dict — never an async
context manager. Every automatic run crashed immediately with a `TypeError` and did nothing;
APScheduler swallows job exceptions into its own logger, so **the product's core "discovers jobs
automatically" promise had not been happening in the background at all**, invisibly, for as long as
that mismatch existed. `scheduler/retry_worker.py`'s `scheduler_retry_worker` had the same
"looks wired, isn't" shape (also fixed 2026-08-01): `.process()` only called `prepare_retry()`
(flip status FAILED → RETRY_PENDING/FAILED_FINAL) and nothing ever consumed RETRY_PENDING to
actually re-run the job — its only test asserted the singleton wasn't `None`. It now does the full
loop and is registered as its own 30-minute scheduler job (`process_failed_scheduler_jobs`).
This category of bug — infrastructure/abstraction built, sometimes with a test that only asserts
`x is not None`, but never actually wired or exercised end-to-end — is the single most common gap
in this codebase. Verify before building on top of an existing module, and be suspicious of any
test whose only assertion is that an object exists.

Next known instance, not yet fixed: `smarthunt/idempotency/` (router + service + metrics) is a
fully-built generic idempotency-key system, mounted at `/api/v1/idempotency`, but nothing in
`apply_queue/router.py`'s `POST /apply-queue` (the endpoint CLAUDE.md's own architecture notes
say it's *for* — "write endpoints prone to duplicate submission (e.g. apply actions)") actually
depends on or calls it. `ApplyQueueItem.job_id` also has no unique constraint, so nothing currently
stops the same job being queued twice (double-click, a retry racing a legitimate re-queue, etc.).
Wiring this needs care, not a quick unique-constraint patch: a hard DB uniqueness on `job_id` would
also block legitimate re-queueing after a prior FAILED/CANCELLED attempt, which is presumably
wanted — the idempotency-key pattern (client sends a header, server dedupes only *that specific
request*, not the job generally) is the right tool, but needs frontend changes too (generate and
send the header) to be worth doing properly.

Other known, doc-recorded gaps (not exhaustive — treat as a starting list, re-verify against code):
- AI layer: needs a real provider wired in (OpenAI/Ollama) in place of mocks, per-task prompt
  tuning, cost tracking, and response caching.
- Job discovery: provider connectors exist per-site but need hardening against real site behavior
  and better duplicate-job detection.
- Resume/cover letter: multiple templates, real PDF/DOCX export, in-app preview.
- Playwright: more job sites, more robust cookie/session persistence across restarts.
- Scheduler/automation: no UI yet to trigger, pause, or monitor runs (API-only today).

Git note: local `master` was significantly ahead of `origin/master` as of doc writing (99 commits);
the doc recommends reviewing history and pushing/tagging a `v1.0.0` release before starting Phase 2
work — check current `git status` / `git log origin/master..master`, don't assume it's still true.

### Standing rules from the project owner (apply every session, not just when repeated)

These come directly from the project doc's "rules for any new chat" section and are treated as
binding, not suggestions:

- Treat this as an enterprise production system, not a prototype — no shortcuts that wouldn't ship.
- Never delete a stable, working feature without a clear architectural reason.
- Never break an existing passing test to land a new feature; run the relevant tests before calling
  work done.
- Keep changes backward compatible where reasonably possible.
- No secrets committed to the repo, ever — all config via environment variables (see
  `backend/.env.example`); production also expects secrets to live outside the repo
  (`/home/badr/secrets/` was the owner's stated target location for local secrets).
- Every new feature should be testable and observable (logs + metrics), consistent with the
  existing patterns in `smarthunt/metrics/` and structured logging in `smarthunt/logging/`.
- Work in small, self-contained increments; prefer finishing and validating one thing over
  spreading changes across many half-done things.
- Stability first, then performance, then new features — in that priority order when trading off.
