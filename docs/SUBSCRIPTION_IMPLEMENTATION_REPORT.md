# CodeLeaf subscription and entitlements implementation report

## Scope and safety

Implemented against the supplied CodeLeaf source tree; existing React/Vite JSX, FastAPI, SQLAlchemy/Alembic, PostgreSQL, and Razorpay architecture was retained. No TypeScript migration, live payment, deployment, commit, push, production secret change, or production database migration was performed.

## Initial audit

The repository already contained Razorpay order/subscription creation, payment verification and webhook handling, payment records, an `Entitlement` model, billing status, server-side XP history, project ZIP chunk storage, and the external isolated runner. The uploaded pricing page did not clearly distinguish all four tiers or show authoritative usage. Workspaces were primarily browser-local; the backend had no consolidated plan allowance/usage API; project ZIP submissions did not persist actual storage bytes for quota accounting; the runner had short-window throttles but no plan-based daily quota; there was no configured, real AI tutor endpoint. AdSense was loaded unconditionally by `index.html`.

## Final plan and limits

| Plan | Price / billing | Storage | Workspaces | Saved snippets | Executions per UTC day | AI requests per UTC day | Ads | XP multiplier |
|---|---|---:|---:|---:|---:|---:|---|---:|
| Free | ₹0 | 1 GB | 3 | 10 | 50 | 0 | Enabled | 1× |
| Pro | ₹299/month | 10 GB | 25 | 100 | 300 | 0 | Enabled | 1× |
| Max | ₹699/month | 50 GB | 100 | 500 | 1,000 | 100 | Disabled | 1.5× |
| Full Access | ₹49,999 one-time, lifetime | 100 GB | 200 | 1,000 | 1,500 | 150 | Disabled | 1.5× |

The application-level maximum for an individual ZIP is 500 MiB (536,870,912 bytes) across tiers. Storage allowances cover persisted project submissions/archives and saved workspaces. Daily counters use UTC and reset at 00:00 UTC. Execution quotas apply only to the configured isolated-runner languages, currently advertised as Python and JavaScript. They do not imply that every language course has a working server runtime.

Free retains access to published standard learning, progress, available exams, earned certificates, project browsing, portfolio, and standard learning features. Pro adds advanced analytics, activity-based recommendations, premium practice and timed mock assessments, saved milestone checklists, weekly/all-time leaderboards, and expanded reusable snippets. Max adds premium projects, priority support triage, ad-free access, the 1.5× XP reward, and AI tutor/code review when a provider is configured. Full Access uses the same standard individual Pro/Max feature set with the highest individual quotas and no monthly renewal. Saved snippets count toward the same total project-storage allowance as saved workspaces and project archives. No AI provider is configured by this deliverable, so AI fails closed with a clear unavailable response rather than fabricated output.

## Implemented changes

- Added a centralized server-side plan catalog and effective-entitlement resolver. Feature checks, quota accounting, plan snapshots, storage usage, and usage limits share `backend/app/plan_entitlements.py`.
- Added `GET /api/me/entitlements`; authenticated CRUD for `/api/me/workspaces`; `POST /api/me/ai/tutor`; `POST /api/me/ai/code-review`; and gated `GET /api/me/analytics/advanced` in `backend/app/plan_routes.py`.
- Added UTC daily reservations and idempotency for provider-backed AI requests and accepted runner jobs. Failed calls release reservations; successful requests consume usage once. User-row locks serialize quota changes on PostgreSQL.
- Added actual stored-byte tracking for project submissions, durable saved workspaces, plan usage counters, and usage reservations. Premium exercise flags and premium project metadata are enforced on API requests; existing published project manifests with `capstone`, `advanced-capstone`, `professional`, `specialist`, or `interview-prep` tiers are treated as Max+ content even when they omit an explicit premium boolean. Ordinary standard projects stay free. Course imports do not erase an existing premium flag when the optional manifest property is omitted.
- Added backend limits for workspaces, storage, execution usage, AI usage, and supported runner languages. The primary API does not execute code in a local shell; it still uses the configured isolated runner.
- Preserved Razorpay's existing integration and extended verification/idempotency behavior for Full Access as a separate ₹49,999 one-time order. Verified Full Access has no expiry; refunded/reversed lifetime orders cannot be reactivated by a repeated checkout callback or a late `order.paid` webhook. Monthly plan state changes are synchronized through signed provider events. A past-due subscription only preserves its already-recorded paid period and never becomes an indefinite grant.
- Updated the pricing page with all four prices, server-backed plan/limit comparison, current plan, real account usage, checkout/billing states, upgrade controls, and cancellation warnings. The playground can persist workspaces and reusable code snippets to the signed-in account; snippets are private, byte-accounted against storage, and count-limited by plan. Added an AI Coach screen with real-provider-only behavior.
- Added timed Pro+ practice mock exams based on the published course question pool (20 distinct questions, 20 minutes), server-side grading, per-topic reports, answer review, attempt ownership, duplicate-submit prevention, and server-enforced deadline handling. Mock results do not grant XP or certificates and do not replace standard certification exams.
- Added account-backed project milestone checklists for Pro+ with backend feature gates and persistence. Added a support request workflow with learner request history, a support-staff queue/reply API, open-ticket limits, and queue priority derived from verified plan at submission; Max and Full Access enter the priority queue.
- Gated the weekly/all-time leaderboard API to Pro+; the frontend shows an upgrade path for locked Free accounts. Standard published practice and standard course exams/earned certificates remain available according to the existing availability rules.
- Removed the globally loaded AdSense script and added a route/entitlement-aware loader. It only loads on selected public learning routes for accounts without `ad_free`; it avoids billing, profile, portfolio, exam, workspace, and code-output routes and reloads into a no-script document when navigating away from an eligible route.

## Database migration

Added `backend/alembic/versions/0008_plan_entitlements_usage.py`, descending from `0007_portfolio_zip_chunks`. It adds:

- `project_submissions.stored_bytes` with a backfill from persisted legacy archive/code data;
- `runner_jobs.request_key` and its idempotency uniqueness constraint;
- `exercises.is_premium` with a default of false;
- `saved_workspaces`, `plan_usage`, and `usage_reservations` tables with ownership, uniqueness, and accounting constraints/indexes.

Added `backend/alembic/versions/0009_snippets_support_mock_assessments.py`, descending from `0008_plan_entitlements_usage`. It adds the `saved_snippets`, `support_requests`, `project_milestone_progress`, and `mock_assessment_attempts` tables with ownership foreign keys, indexes, uniqueness rules, and a downgrade path. The chain now has one head, `0009_snippets_support_mock_assessments`; both Alembic upgrades passed twice on an isolated temporary SQLite database. A PostgreSQL/Neon staging migration was not run here.

## Main files changed or added

**Backend:** `app/models.py`, `app/config.py`, `app/auth_security.py`, `app/main.py`, `app/phase5_routes.py`, `app/plan_entitlements.py`, `app/plan_routes.py`, Alembic revisions `0008_plan_entitlements_usage.py` and `0009_snippets_support_mock_assessments.py`, `scripts/import_course_files.py`, and new/extended test scripts including `test_subscription_remaining_features.py`, `test_plan_entitlements.py`, `test_payment_security.py`, `test_course_import_safety.py`, `test_portfolio_zip_upload.py`, and `test_migration_repeatability.py`. Updated `backend/.env.example` with the optional isolated-runner variables.

**Frontend:** `src/data.js`, `src/App.jsx`, `src/components/layout/Header.jsx`, `src/components/monetization/AdSenseController.jsx`, `src/pages/PlansPage.jsx`, `src/pages/PlaygroundPage.jsx`, `src/pages/AIAssistantPage.jsx`, `src/pages/MockExamPage.jsx`, `src/pages/SupportPage.jsx`, `src/pages/LeaderboardPage.jsx`, `src/pages/LessonPage.jsx`, `src/pages/ChallengesPage.jsx`, `src/pages/ExerciseDetailPage.jsx`, `src/pages/ProjectsPage.jsx`, `src/pages/ProjectGuidePage.jsx`, `src/styles/pages.css`, `src/styles/learning-workspaces.css`, `index.html`, and `scripts/test_subscription_remaining_features.mjs` plus the existing subscription/course contracts.

## Validation results

### Passed

- `python -m compileall -q app scripts alembic/versions`.
- `python scripts/check_alembic_heads.py` — 9 revisions, one head (`0009_snippets_support_mock_assessments`).
- `python scripts/test_migration_repeatability.py` — repeat upgrade passes on temporary SQLite.
- `python scripts/test_plan_entitlements.py` — plan definitions/prices/limits, Free access, workspace count/ownership, AI and analytics denial, expired and lifetime states, past-due period handling, and quota idempotency/reservations.
- `python scripts/test_subscription_remaining_features.py` — saved-snippet ownership, byte accounting and plan cap; support ticket priority/admin reply; Free/Pro leaderboard gate; Pro milestone persistence; explicit capstone-tier project denial/unlock; and server-graded, gated, owner-scoped timed mock assessment with timeout and duplicate-submit checks. Uses an isolated SQLite DB and mocked question bank only.
- `node scripts/test_subscription_remaining_features.mjs` — route, pricing, snippet, project-checklist, mock-exam, support, leaderboard, and styling source-contract checks.
- `python scripts/test_payment_security.py` — mocked checkout/signature checks, lifetime entitlement persistence, webhook signature and deduplication, and refund reactivation protections. No live Razorpay requests.
- `python scripts/test_course_import_safety.py` — importer idempotency/rollback plus preservation of an existing premium flag.
- `python scripts/test_phase5_contract.py` — 8 tests passed after restoring the roadmap JSON fixture from the original archive into the validation copy.
- `python scripts/test_runner_config_status.py` — 2 tests passed.
- `python scripts/test_exam_question_bank_compatibility.py` — all 62 course question banks were inspected; readiness is reported per bank and only banks with at least 80 distinct valid prompts satisfy the certification MCQ readiness gate.
- `python scripts/test_portfolio_zip_upload.py` — archive validation, chunked-storage contract, and legacy download checks.
- `python scripts/test_practice_exercise_policy.py` — practice type policy checks passed against supplied course manifests.
- Frontend targeted scripts passed: `test_learning_workspaces.mjs`, `test_phase3c_personal_learning.mjs`, `test_phase5_routes.mjs`, `test_certificates_exam_availability.mjs`, `test_playground_output_modes.mjs`, `test_course_catalog_filters.mjs`, and new `test_subscription_remaining_features.mjs`. Earlier broad source-contract run had 27 passed and 5 existing mismatches noted below.

### Not green / not verified

Five existing frontend source-contract scripts failed in the earlier broad run against this uploaded snapshot:

1. `test_certificate_view.mjs` assumes a single-line JSX route expression while the valid route in `App.jsx` is formatted across lines.
2. `test_deployment_config.mjs` expects `/api/proxy/:path*`, while the uploaded Vercel config uses a different API rewrite shape.
3. `test_exercise_page_contract.mjs` expects an `allowed_roots` marker that is not present in this repository's external-runner implementation.
4. `test_language_workspace.mjs` expects `usableReferenceSources(content.sources)`, which is absent in the current `LessonPage.jsx`.
5. `test_lesson_loading_timeout.mjs` expects a bounded 12-second timeout not present in the current lesson loader.

These files/behaviors were not rewritten as part of the subscription scope. The frontend production build was attempted again but could not start: `npm run build` returned `sh: 1: vite: not found`. The present `frontend/node_modules` directory is incomplete (about 520 KB and no Vite binary), so `vite build` has not been verified. `test_exam_question_bank_compatibility.py` was rerun separately and passed for all 62 published course banks. No browser end-to-end session, deployed AdSense behavior, live Razorpay transaction, or live AI-provider call was performed.

## Environment variables and provider setup

Use only backend/server-side secrets. The exact names referenced by this code are:

- Core deployment: `DATABASE_URL`, `JWT_SECRET`, `APP_ENV`, `FRONTEND_ORIGINS`, `FRONTEND_BASE_URL`, `COOKIE_SECURE`.
- Razorpay: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `RAZORPAY_PRO_PLAN_ID`, `RAZORPAY_MAX_PLAN_ID`, `RAZORPAY_SUBSCRIPTION_TOTAL_COUNT`.
- Optional real AI provider: `AI_API_BASE_URL`, `AI_API_KEY`, `AI_MODEL`, `AI_TIMEOUT_SECONDS`, `AI_MAX_OUTPUT_TOKENS`. For an OpenAI-compatible API the base URL should include the correct API prefix, such as `/v1`, and the code appends `/chat/completions`.
- Existing isolated runner: `RUNNER_SERVICE_URL`, `RUNNER_SERVICE_TOKEN`.
- Frontend API base where needed: `VITE_API_BASE_URL` (never use a Vite variable for a secret).

In Razorpay, configure valid **test-mode** monthly plans matching ₹299/month and ₹699/month exactly (INR, monthly interval 1), then put their real plan IDs in `RAZORPAY_PRO_PLAN_ID` and `RAZORPAY_MAX_PLAN_ID`. Do not use guessed plan IDs. Configure a webhook at `https://codeleaf-api.onrender.com/api/payments/webhook`, use the same server-side `RAZORPAY_WEBHOOK_SECRET`, and enable the event types handled by this code where available: `order.paid`, `payment.failed`, `payment.refunded`, `refund.processed`, `subscription.activated`, `subscription.charged`, `subscription.updated`, `subscription.cancelled`, `subscription.halted`, `subscription.paused`, `subscription.resumed`, `subscription.completed`, and `subscription.expired`. Validate the lifecycle in test mode before considering production configuration.

`RAZORPAY_SUBSCRIPTION_TOTAL_COUNT` is finite because Razorpay subscriptions require a count; confirm its allowed value and published billing terms before production. Full Access is not connected to a recurring subscription. Leave AI variables blank until a supported provider and budget are intentionally configured; Max AI will remain unavailable until all required AI values exist. The app publisher meta tag was preserved; the AdSense script is now loaded conditionally, but the publisher account's Auto ads configuration still needs a dashboard review.

## Commands to continue locally

Run from `E:\Code_Leaf` in PowerShell, first with a disposable/staging database and never against production without a backup/review:

```powershell
cd .\backend
python -m compileall -q app scripts alembic\versions
python scripts\check_alembic_heads.py
python scripts\test_migration_repeatability.py
python scripts\test_plan_entitlements.py
python scripts\test_subscription_remaining_features.py
python scripts\test_payment_security.py
python scripts\test_course_import_safety.py
python scripts\test_portfolio_zip_upload.py
python scripts\test_practice_exercise_policy.py
# Only after backup and against the intended staging DB:
python -m alembic upgrade head

cd ..\frontend
npm ci
npm run build
node scripts\test_subscription_ui.mjs
node scripts\test_practice_exercise_types.mjs
```

Before relying on the 500 MiB ZIP limit in production, verify the whole inbound path (Vercel/Render/proxy, request-body and timeout limits). This patch keeps ZIP storage chunked in the database, but does not add an external object-storage or resumable-upload service. If the deployed request path cannot reliably accept large uploads, direct/resumable object-storage upload is still needed.

## Remaining operational work

1. Run the migration against a staging PostgreSQL/Neon database and exercise rollback/recovery procedures before production.
2. Configure Razorpay test subscriptions and webhooks, then verify activation, renewal, cancellation-at-period-end, failed renewal, retries, out-of-order events, and refunds end to end.
3. Install dependencies successfully and run the frontend production build. Resolve the five existing frontend contract mismatches separately.
4. Configure a real AI provider only if intended, then test rate/budget limits and failure paths. Confirm the isolated runner runtime list in the deployed runner service.
5. Check production upload body-size/time limits and AdSense account behavior before treating those parts as operational.
