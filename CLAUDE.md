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

### The product vision is full automation — hold this as the target, not just discovery

Restated explicitly by the project owner 2026-08-01 because earlier work had drifted toward
"discover jobs and show them to the user": **the end state is that SmartHunt discovers jobs, scores
them, and applies to the good ones completely on its own on a schedule — no human clicking
"apply" — then tells the owner afterward** (notifications and/or email/messages: "applied to N jobs
today, here they are") rather than just surfacing a list for manual review. Discovery-only or
apply-only-on-manual-trigger is an intermediate state, not the goal — when extending the
scheduler/apply-queue/notifications, prefer designs that move toward "runs unattended end-to-end and
reports back" over ones that still need a human in the loop for routine cases. CAPTCHA/MFA/an
unanswerable application question remain the only cases that should ever pause and wait for the
owner — everything else should complete on its own.

**Telegram delivery is real, not yet activated.** `notifications/channels/telegram.py` sends via the
real Telegram Bot API when a `Notification` is created with `channel="TELEGRAM"` (hooked in
`NotificationService.create()`) — needs `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` in
`/home/badr/secrets/secret.env` (fields already exist on `Settings`, just unset as of 2026-08-01); a
missing/failed send is logged and swallowed, never breaks notification creation. Settings page has a
"ابعت إشعار تجريبي" button to verify once configured. No email/SMTP or WhatsApp sender exists yet —
build the same way (a `channels/` module + a `channel` value the service checks for) if/when needed.
This channel isn't wired to anything real *yet* since it's meant to fire when an application is
auto-submitted, and real auto-apply is still the explicitly-deferred, credentials-gated piece — see
above.

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

uv run alembic upgrade head                # apply DB migrations — see the warning below first
uv run alembic revision --autogenerate -m "message"   # new migration

uv run uvicorn smarthunt.main:app --reload --host 0.0.0.0 --port 8000   # run the API locally
```

**`uv run alembic upgrade head`, run bare from `backend/`, silently migrates the *test* database,
not the real dev one** — found 2026-08-01 chasing a schema-drift bug. `alembic/env.py` does
`load_dotenv(".env.test", override=False)` *before* `load_dotenv(".env", override=False)`, and
`backend/.env.test` sets its own `DATABASE_URL` (pointing at `smarthunt_test`) — `override=False`
means whichever file's value lands first in `os.environ` wins, and `.env.test` always loads first
whenever it exists. Real-world effect: a migration can report "Running upgrade ... -> ..." and look
completely successful while never touching the database the app (or `docker compose`'s backend
container) actually uses. To target the real dev DB from the host, either `cd backend && DATABASE_URL=$(grep ^DATABASE_URL ../.env | cut -d= -f2-) uv run alembic upgrade head`,
or — simpler and how this project actually keeps the dev DB current — **just rebuild and restart the
backend container** (`docker compose build backend && docker compose up -d --no-deps backend`):
`core/lifespan.py` runs `run_migrations()` on every container startup using the container's own
real environment (`env_file: .env` + `secret.env` via docker-compose, not `.env.test`), so that path
isn't affected by this bug at all. Verify a migration actually landed with a real `psql` check
against the dev DB, not just by trusting the alembic command's own "success" output.

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

**Found 2026-08-01, the biggest "looks real but is fake" finding in the project so far: all 11
providers' `search()` returned hardcoded fake data** — literal Python objects like `title="Senior
Linux Engineer", company="LinkedIn Demo"` or `{"title": "Cyber Security Specialist", "location":
"Doha", "salary": 15500, "score": 87}`, completely ignoring the `query`/`location` arguments. This
was true *before* the scheduler-jobs fix earlier that same day too — that fix made the discovery
*pipeline* run for real (scheduling → provider call → DB save → history), but every "discovered
job" it ever produced, including in that fix's own verification, was one of these hardcoded stubs
cycling through. Don't trust "it discovered N jobs" as proof of anything real without checking what
the provider's `search()` body actually does.

**`linkedin` is the first (and so far only) provider with a real implementation** — scrapes
LinkedIn's public job search (`https://www.linkedin.com/jobs/search/?keywords=...&location=...`),
which serves a first batch of real results before its sign-in wall, no login required. Selectors:
`.job-search-card` per listing, `.base-search-card__title` / `.base-search-card__subtitle` /
`.job-search-card__location` / `a.base-card__full-link` — verify these still match if LinkedIn
redesigns again (their login page's `#username`/`#password` IDs already broke once, see below).
Runs in its own `browser_manager.new_isolated_page()` context (not the shared, session-persisting
`get_page("linkedin")` used for login/apply) so a concurrent discovery job can't race it. The other
10 providers still return their original hardcoded stubs — building each for real is a per-site
scraper, not a quick fix; do not claim a provider is real without checking its `search()` body.

**Providers can be enabled/disabled** via `GET/PATCH /api/v1/providers` (`providers/settings/`,
table `provider_settings` — a provider with no row defaults to enabled) and the frontend's
Providers page (`/providers`). `DiscoveryService.discover()` filters `provider_registry.providers()`
down to enabled ones before calling `fetch_all_jobs(providers=...)` — a disabled provider is
genuinely excluded from discovery, not just hidden in the UI. The `real_discovery` flag returned by
that endpoint is a hardcoded set (`REAL_DISCOVERY_PROVIDERS` in `providers/settings/router.py`) —
add a provider's name there only once its `search()` is actually real, so the UI never claims a
still-fake provider is real.

**The 10 still-fake providers are disabled on the local dev DB as of 2026-08-01** (via the above
enable/disable, not a code change) after their stub data leaked past the Saudi-Arabia location
filter: several of them (`indeed`, `drjobs`) build their fake `Job.location` as `location or
"Remote"` — i.e. they *echo back whatever location the caller searched for* — so a query for
"Saudi Arabia" made their obviously-fake rows (`company="Indeed Demo"`) pass the exact substring
filter that's supposed to guarantee real, Saudi-only results. Others (`monstergulf`, `naukrigulf`,
`wzayef`, `tanqeeb`, `forasnagulf`) have a hardcoded non-Saudi fake location (`"Doha"`, `"Abu
Dhabi"`, etc.) and got filtered out correctly, but only by accident. Re-enable a provider only once
its `search()` is real — don't re-enable to "get more results," that's exactly how fake data gets
back into a real user's job list.

**Discovery scope is Saudi Arabia only** — an explicit, current requirement from the project owner
(2026-08-01), not a technical default that happened to land there. `scheduler/jobs.py`'s
`DISCOVERY_LOCATION` constant (kept duplicated in `scheduler/retry_worker.py` for the same value,
to avoid a circular import) and `DiscoveryService.discover()`'s post-fetch location filter (`needle
in job.location.lower()`) both enforce this. If broadening beyond Saudi Arabia is ever wanted,
that's a deliberate scope change to confirm with the owner first, not just deleting the filter.

**Only 4 of the 11 providers currently set `supports_login`/`supports_apply` to `True`: LinkedIn,
Bayt, GulfTalent, Wuzzuf.** The other 7 (Indeed, NaukriGulf, MonsterGulf, Wzayef, Tanqeeb, DrJobs,
ForasnaGulf) inherit the `BaseProvider` defaults (all `False`) — they are discovery/search-only
today (and currently fake even at that, per above). Auto-apply (`recruitment/auto_apply_worker.py`,
`apply_queue/`) only works where `supports_apply` is `True` and credentials for that site exist in
`Settings` (currently only `linkedin_email`/`linkedin_password` — Bayt/GulfTalent/Wuzzuf credential
fields still need adding). Even within a supported site, not every posting is auto-appliable: many
job boards (LinkedIn included) mix native "Easy Apply"-style postings with ones that redirect to
the employer's own external ATS (Greenhouse, Workday, etc.), which the current Playwright layer
does not handle.

**`PlaywrightEngine.apply()` (`browser/playwright/engine.py`) is real as of 2026-08-01** — it now
composes the pre-existing `login()` → `open_job()` → `detect_form()` → `easy_apply()` steps into a
full unattended application instead of the old no-op stub that always returned `{"status":
"SUCCESS"}` without opening a browser. Each step's failure short-circuits into a `FAILED` with a
`reason` (`login_failed`, `job_page_unavailable`, `no_application_form`,
`external_ats_not_supported`) rather than raising, so one bad posting can't take down a scheduled
batch; a `MANUAL_REQUIRED` login (CAPTCHA/MFA) and `easy_apply()`'s `PAUSED_UNKNOWN_QUESTION` are
the only two statuses that propagate through unflattened, matching the vision doc's "only these two
things should ever pause for the owner" rule. `AutoApplyWorker.process_next()`
(`recruitment/auto_apply_worker.py`) was also fixed the same day: it used to call
`playwright_engine.apply(job_url=f"job:{item.job_id}")` — a literal placeholder string, never a real
URL — so even a "successful" run never actually navigated anywhere; it now looks up the queued
`Job` row and passes its real `url`/`item.provider`, and on a real `SUCCESS` creates a `channel=
"TELEGRAM"` `Notification` (via `NotificationService`) so the owner is told afterward, matching
"discovers, scores, and applies on its own, then tells the owner" from the vision section above. A
notification-send failure is caught separately and logged rather than flipping an already-successful
application back to `FAILED`. **Still unverified end-to-end with real credentials** — the stored
LinkedIn password is wrong (see the standing-blocker note below), so this has only been exercised
against mocks (`tests/test_playwright_engine.py`, `tests/test_auto_apply_worker.py`); confirm a real
apply the first time the password is fixed rather than assuming the composition is correct just
because it's unit-tested.

**`browser_manager.launch()` (`browser/playwright/manager.py`) now has a 30s timeout — found
2026-08-01 chasing a full test-suite hang.** `BrowserManager` is a process-wide singleton
(`__new__`-based), and `launch()`/`close()` are real (unmocked) in several tests
(`tests/test_discovery.py`, `tests/test_linkedin_provider.py`, `tests/test_easy_apply.py`) that each
get their own event loop under pytest-asyncio's `asyncio_default_fixture_loop_scope="function"`.
Running the full suite sequentially on this dev machine, a real `chromium.launch()` deep into the
run would occasionally hang indefinitely with no error — traced to genuine CPU contention on this
shared host (a long-lived, unrelated root-owned Playwright/chromium process, most likely the live
`smarthunt-backend` container's own browser session from a real scheduled discovery run, was already
competing for the same machine's resources — confirmed via `ps -eo pid,ppid,user,etime,cmd`, not a
leak from the test run itself). `launch()` now wraps both `async_playwright().start()` and
`chromium.launch()` in `asyncio.wait_for(..., timeout=30)` and raises a clear `RuntimeError` instead
of hanging forever — callers that already catch broadly (`LinkedInProvider.search()`) degrade
gracefully; callers that don't (most `PlaywrightEngine` methods) now surface a fast, diagnosable
500 instead of an unbounded hang. This is a safety net, not a fix for the underlying resource
contention — `get_page()`/`new_isolated_page()`'s `browser.new_context()` calls are still
unprotected; if hangs recur there, apply the same `asyncio.wait_for` pattern. When running the full
suite locally, prefer `--deselect` on the handful of real-network tests
(`test_discovery.py::test_discovery_run_records_scheduler_history`,
`test_linkedin_provider.py`'s two tests, `test_easy_apply.py::test_easy_apply`) to get a fast, clean
signal, then verify those specific tests separately in isolation — each passes standalone in
10-20s; it's only deep in a long sequential run under real machine load that they've been seen to
stall.

**Bayt, GulfTalent, and Wuzzuf cannot be scraped anonymously the way LinkedIn was — found
2026-08-01 while trying to extend LinkedIn's real-search treatment to them.** A plain headless
Playwright request to Bayt's or Wuzzuf's public search page gets served a Cloudflare "Just a
moment..." interstitial (a bot challenge, not real content); GulfTalent returns a flat "Access
Denied". This is a materially different problem than LinkedIn's case (LinkedIn only walls off
*login*, not the first page of anonymous search results) — do not attempt to defeat these
challenges (headless-detection bypasses, residential proxies, CAPTCHA-solving services); that is
anti-bot evasion against these sites' own protections, not the kind of scraping this project should
be doing. If these three are ever made real, the credentialed **login** path (`supports_login=True`
already set for all three, though the credential fields don't exist in `Settings` yet) is the more
plausible route in — an authenticated session may not face the same anonymous-bot challenge — but
that's unverified, needs real credentials to test, and even then may not work. Don't re-attempt the
anonymous-scrape approach for these three without a genuinely different technique in hand.

`smarthunt/providers/registry.py` (`provider_registry`) fan-outs `search()` across every provider
concurrently via `asyncio.gather(..., return_exceptions=True)` and normalizes results to
`DiscoveredJob` — a single provider failing/raising does not fail the whole search.
`fetch_all_jobs()` accepts an optional `providers=` override list (used by `DiscoveryService` to
pass only the enabled ones); omit it to fall back to the full `providers()` list.
`smarthunt/providers/manager.py` (`provider_manager`) is dead code — a separate registration-based
registry that's never populated (`register_provider()` has no callers) and never imported by
anything; don't build on it, it's not what actually backs provider metadata (that's
`providers/settings/` now). `smarthunt/providers/circuit_breaker.py` and `circuit_registry.py`
guard against a flaky provider being hammered repeatedly.

**LinkedIn's login page markup changes over time** — `browser/providers/linkedin/login.py` used to
target `#username`/`#password`/`button[type='submit']`, which broke when LinkedIn switched to
per-request-random React `id`s and a JS-driven `<button type="button">` (not a real form submit).
Fixed by locating fields via stable `autocomplete` attributes
(`input[autocomplete*="username"]:visible`, `input[autocomplete*="current-password"]:visible`) and
submitting via `Enter` in the password field instead of clicking a specific button — both survive
markup/locale changes (LinkedIn serves the page in the visitor's detected locale; this host got
Arabic). If login starts failing again, screenshot the actual page
(`page.screenshot(path=..., full_page=True)`) before assuming the credentials are wrong — check the
markup first.

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

**A successful `oc start-build` did NOT used to mean the fix was live** — found 2026-08-01 after
several builds in a row succeeded and pushed to the `smarthunt-backend:latest` image tag, yet the
running pod was still 3+ hours old and serving pre-fix code. `deployment.apps/smarthunt-backend` is
a plain Kubernetes `Deployment`, which had no `ImageChange` trigger — pushing a new image to the
same `:latest` tag doesn't change the pod spec, so the Deployment controller saw no diff and never
created a new ReplicaSet on its own. **Fixed the same day**: an `smarthunt-backend` ImageStream
already existed and was being updated on every push (`oc get imagestream smarthunt-backend`
showed `latest` updating), so
`oc set triggers deployment/smarthunt-backend --from-image=a-badr-dev/smarthunt-backend:latest -c backend`
now auto-restarts the pod whenever a new build lands (verified: build → new pod within ~30s, no
manual restart needed) — this should now be permanent, but if a future build ever again doesn't
show up live, check `oc get deployment smarthunt-backend -o jsonpath='{.metadata.annotations.image\.openshift\.io/triggers}'`
first (empty/missing means the trigger got dropped somehow) before assuming the fix itself is
wrong. Either way, still verify with a real request after a deploy you care about (e.g. curl a
field/endpoint that only exists in the new code), not just a generic health check — the pod being
"Running" and healthy doesn't by itself prove which image it's running.

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
