# CodeLeaf subscription implementation — remaining-work completion report

Date: 2026-10-29

## Outcome

The code-level remaining items identified during the subscription implementation have been addressed in this patch. This includes the Render Alembic revision-length hotfix, Learning Hub upgrade-error handling, the responsive More navigation menu, the home-page category filter, workspace import/export assertions, explicit Full Access fair-use terms, and a Vercel-safe chunked ZIP-upload path. No production deployment, Git commit/push, live payment, production database migration, or production environment change was performed.

## Remaining items that were found and addressed in code

1. **Vercel ZIP uploads:** A single request could not reliably transport an archive near the advertised 500 MiB limit through Vercel's 4.5 MB function request-body limit. Portfolio ZIP upload now uses 4 MiB binary chunks through the same-origin API proxy. The backend reserves the whole archive's storage allowance before accepting chunks, checks ownership and sequence, permits idempotent retries for identical chunks, rejects conflicting/oversized chunks, reconstructs and validates the ZIP before marking it complete, and supports cancel/24-hour stale-session cleanup. Incomplete uploads are hidden from owner/public portfolio listings and cannot be made public, edited, or downloaded.
2. **Learning Hub 403 display:** Structured `FEATURE_REQUIRES_UPGRADE` responses are converted to a readable upgrade notice instead of `[object Object]`. Recommendations fail independently, so learning preferences, reviews, and roadmaps can still render.
3. **Main navigation:** Tutorials, References, Projects, and Practice remain visible. Other top-level destinations are grouped in an accessible responsive **More** menu with outside-click/Escape handling.
4. **Home category filter:** Replaced the long category button strip with a compact controlled select, course count, and clear-filter action.
5. **Workspace import/export contract:** The playground has a bounded JSON workspace import, project export, path/duplicate checks, and updated export tooltip. Import accepts only the app's versioned workspace JSON, caps the JSON at 2 MiB and at 100 files, and rejects unsafe filenames.
6. **Lifetime purchase terms:** The plan page now explains that lifetime access is tied to continued operation of CodeLeaf's standard individual learning service and lists fair-use allowances before purchase: 100 GB project storage, 200 saved workspaces, 500 MiB per ZIP, 1,500 supported executions per UTC day, and up to 150 AI requests per UTC day only when a real AI provider is configured and available.
7. **Migration revision ID:** `0009_snippets_support_mock_assessments` was shortened to `0009_snippets_support` so PostgreSQL can store it in Alembic's standard 32-character `version_num` column. The revision file's filename remains unchanged; its parent is still `0008_plan_entitlements_usage`.
8. **Frontend contract regressions:** Updated/fixed the certificate route contract, Vercel proxy contract, exercise solution path validation contract, safe lesson reference URL filtering, 12-second lesson loading timeout/error state, workspace import/export contracts, Learning Hub upgrade state, navigation contract, and pricing-page terms coverage.
9. **Subscription and entitlement baseline:** The patch retains the centralized server-side plan catalog, verified entitlements, payment/webhook protections, storage/workspace/snippet limits, daily AI/runner quotas, premium content checks, project milestones, timed mock assessments, support tickets/priority queue, leaderboard gates, conditional ad loading, and Max/Full Access 1.5× XP logic.
10. **Real exercise-tier differentiation:** The catalog's difficulty metadata is now translated into server-enforced plan tiers. Standard/beginner/intermediate exercises remain Free; `advanced` and `hard` require Pro; `professional`, `specialist`, `specialization`, and `capstone` require Max or Full Access. Legacy database `is_premium` flags continue to require Pro. The same rule applies to exercise listing, lesson exercise lists, featured practice, progress visibility, worked-solution retrieval, and answer submission. The UI shows the required plan instead of hard-coding every lock as Pro. This uses the current difficulty values and does not require mass-editing thousands of manifests or adding a migration.

The source library currently contains 3,807 exercise manifests in course module exercise directories: 2,295 use standard difficulty labels, 1,353 are `advanced`/`hard`, and 159 are in the professional/specialist/capstone group. These are manifest counts, not a claim that every record is an eligible MCQ/code challenge; the existing practice policy continues to expose only supported exercise types.

## Configured initial plan allowances

| Allowance | Free | Pro | Max | Full Access |
|---|---:|---:|---:|---:|
| Price | ₹0 | ₹299/month | ₹699/month | ₹49,999 one-time |
| Max individual ZIP | 500 MiB | 500 MiB | 500 MiB | 500 MiB |
| Project storage | 1 GiB | 10 GiB | 50 GiB | 100 GiB |
| Saved workspaces | 3 | 25 | 100 | 200 |
| Saved snippets | 10 | 100 | 500 | 1,000 |
| Supported code executions/day | 50 | 300 | 1,000 | 1,500 |
| AI requests/day | 0 | 0 | 100 | 150 |
| Ads | Yes | Yes | No | No |
| XP multiplier | 1× | 1× | 1.5× | 1.5× |

Usage windows reset at 00:00 UTC. Runner quotas apply only to configured, supported isolated runtimes. The UI/API must not imply that every language or package environment is actually executable.

## Validation executed

### Backend checks passed

- `python -m compileall -q app scripts alembic/versions`
- `python scripts/check_alembic_heads.py` — 9 revisions, one head: `0009_snippets_support`.
- `python scripts/test_migration_repeatability.py` — two upgrades on an isolated temporary SQLite database.
- `python scripts/test_course_import_safety.py` — safe/idempotent import, premium flag preservation, and rollback checks.
- `python scripts/test_phase5_contract.py` — 8 tests passed.
- `python scripts/test_runner_config_status.py` — 2 tests passed.
- `python scripts/test_exam_question_bank_compatibility.py` — checked all 62 course tracks; readiness is not true for every track because some published banks do not yet contain 80 distinct valid prompts.
- `python scripts/test_practice_exercise_policy.py` — passed.
- `python scripts/test_plan_entitlements.py` — passed using an isolated SQLite database.
- `python scripts/test_payment_security.py` — passed with a mocked Razorpay provider; no live payment calls.
- `python scripts/test_portfolio_zip_upload.py` — archive safety and legacy download checks passed.
- `python scripts/test_subscription_remaining_features.py` — passed with new chunked-upload, quota reservation, incomplete-upload privacy, snippet, support, milestone, leaderboard, capstone, and mock-exam assertions.
- Exercise-tier integration checks in `python scripts/test_subscription_remaining_features.py` — standard exercises available to Free; advanced exercises available to Pro; professional exercises denied to Pro and accepted for Max; direct submit calls are checked server-side.

### Frontend source-contract checks

- 35 of 35 runnable `.mjs` source-contract scripts passed, including plans, AdSense, proxy, Learning Hub, More menu, category filter, workspace import/export, certificate routing, lesson timeout, exercise tier messaging, and portfolio contracts.
- `scripts/validate_phase1_syntax.mjs` was skipped because `@babel/parser` was missing. Attempted `npm ci --no-audit --no-fund`, but npm registry requests failed with `EAI_AGAIN`; the environment did not have a working Vite binary. The Vite production build has therefore **not** been verified.

## Remaining work outside the source patch

These are genuine external/deployment tasks rather than code claims. They still need action and cannot safely be completed without your provider access and explicit deployment authorization.

1. **Apply and deploy:** Review this patch, merge it into `E:\Code_Leaf`, then commit/push to the configured GitHub branch. Render and Vercel must deploy that commit. No commit, push, or deployment was made by this task.
2. **Vercel proxy variable:** In Vercel Project Settings → Environment Variables, set the server-only `CODELEAF_API_ORIGIN=https://codeleaf-api.onrender.com` for Production and for Preview if Preview deployments are used. Keep it free of a path or `/api` suffix, do not prefix it with `VITE_`, and redeploy Vercel.
3. **Retry Render migration:** The current Render log failed on the old oversized revision name. After this fixed migration revision is pushed, let Render retry `alembic upgrade head` and confirm it advances to `0009_snippets_support` before Uvicorn starts. Do not manually edit `alembic_version`.
4. **Staging PostgreSQL/Neon:** Back up the target database, run the migration against a separate staging PostgreSQL/Neon database, test restore/rollback procedures, and verify there is one migration head. The migration tests in this environment used SQLite only.
5. **Razorpay test-mode lifecycle:** Supply the real test-mode `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `RAZORPAY_PRO_PLAN_ID`, and `RAZORPAY_MAX_PLAN_ID` in Render only. Configure the webhook endpoint `https://codeleaf-api.onrender.com/api/payments/webhook`, then test monthly checkout, renewal, cancellation-at-period-end, failed renewals, duplicate/out-of-order events, Full Access one-time payment, and refunds. Use dashboard-created plan IDs, never guessed ones. Live transaction verification has not been done.
6. **AI provider:** To enable Max/Full Access AI, configure server-only `AI_API_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` (plus the optional timeout/output settings). Verify budget/rate limits and provider failures. With missing configuration, AI is intentionally unavailable rather than simulated.
7. **Isolated code runner:** Configure `RUNNER_SERVICE_URL` and `RUNNER_SERVICE_TOKEN` only if the dedicated isolated runner service is actually deployed and secured. The main API does not safely run arbitrary code itself. Actual advertised server-side runtimes are limited by the configured runner; this patch does not add C/C++/Java/NumPy execution environments.
8. **Production ZIP smoke test:** On staging, upload a representative small ZIP, a multi-chunk ZIP, and (only if storage capacity/cost permits) an archive approaching 500 MiB. Verify chunk retries, cancellation, quota release, completed downloads, timeout behavior, PostgreSQL storage, Render request/resource limits, and Vercel function logs. Chunking avoids sending a 500 MiB file as one Vercel function request, but the full production path has not been load-tested here.
9. **AdSense and support operations:** Check live AdSense publisher configuration/placement after deployment. Priority support currently means priority placement in the application queue; CodeLeaf still needs staff who review and reply to those requests, and no response-time SLA is implied.
10. **Frontend build and browser QA:** On a network-enabled local machine run `cd frontend`, `npm ci`, `npm run build`, then test the plans page, checkout states, Learning Hub for Free and Pro accounts, More menu on mobile, Free/Pro/Max exercise tier presentation, and portfolio ZIP flow. A direct build attempt returned `vite: not found`; dependency installation could not complete because npm registry requests failed with `EAI_AGAIN`, so a production build is not verified.

## Commands to run locally (PowerShell)

```powershell
cd E:\Code_Leaf\backend
python -m compileall -q app scripts alembic\versions
python scripts\check_alembic_heads.py
python scripts\test_migration_repeatability.py
python scripts\test_plan_entitlements.py
python scripts\test_payment_security.py
python scripts\test_portfolio_zip_upload.py
python scripts\test_subscription_remaining_features.py

cd ..\frontend
npm ci
npm run build
node scripts\test_subscription_ui.mjs
node scripts\test_learninghub_upgrade_more_nav.mjs
node scripts\test_language_workspace.mjs
node scripts\test-home-category-tabs-css.mjs
```
