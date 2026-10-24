# CodeLeaf consolidated implementation — verification status

This document describes the integrated source patch built from the latest available CodeLeaf project snapshot and the previously produced Phase 2–5 feature patches. It is not a claim that live provider, deployment, or production acceptance tests have completed.

## Included in the consolidated patch

- Tutorial overview sections are opt-in and only enabled by tutorial landing pages; compact course headers remain usable for References, Projects, and Practice.
- Course catalog and collection pages retain API-backed availability/status and scoped item flows.
- Reference details use shared metadata enrichment, course-outline lesson suggestions, safe HTTPS source links, and full available content width. Existing CSS imports are preserved, including `phase5.css` and `ui-polish.css`.
- Lesson pages include sandboxed HTML/CSS/JavaScript previews and lesson-aware topic demonstrations for other subjects. The W3Schools-style sidebar uses single-open module behavior.
- Learner home/resume states, progress page, review queue/rating/snooze/preferences, bookmarks, profile preferences, and privacy-aware analytics are integrated in one source tree.
- Phase 5 routes are preserved alongside review routes: Learning Hub, Portfolio, Content Studio, and Review.
- Backend phase-5 APIs include review schedule ownership, portfolio path validation, draft content staging, dynamic diagram validation, privacy-minimized analytics, analytics summary, and an authenticated gateway to a separately deployed runner.
- The playground now checks a non-sensitive `/api/runner/status` endpoint and disables server-side execution while the separate runner is unconfigured.
- Production configuration checks, session/authentication lifecycle tests, server-side XP idempotency, exam/certificate controls, mocked payment/webhook security tests, and a repeatable Phase 5 migration test are included.
- A regression test covers the analytics summary item-key projection bug; runner status tests confirm that no URL or shared runner token is returned.
- `scripts/Verify-CodeLeaf.ps1` is a simplified Windows check runner. It has not been executed by PowerShell in this Linux validation environment; run it on Windows and treat its output as authoritative for that checkout.

## Checks passed in the isolated integrated source tree

- Python compilation: `python -m compileall -q app scripts alembic`.
- Alembic graph check: one head, `0004_phase5_capabilities`.
- Production config validation tests.
- Authentication/session lifecycle tests with isolated fixtures.
- API contract, server-controlled XP, authorization, unpublished-content privacy, and exercise grading tests.
- Course import idempotency and transaction rollback tests.
- Repeatable Alembic migration test against temporary SQLite (no Neon database touched).
- Phase 2 reference/project/starter ZIP and exam/certificate tests.
- Mocked Razorpay order/signature/webhook idempotency tests; no real provider requests were made.
- Phase 5 contract, dynamic diagram compatibility, and diagram fixture tests.
- Review rating/queue tests, runner status endpoint tests, and privacy-aware analytics summary tests using temporary SQLite.
- Mocked SMTP delivery tests; they do not establish that Brevo accepts the live sender or delivers to inboxes.
- Isolated runner unit tests (9 tests); these do not prove that an actual Docker host is safe for untrusted public workloads.
- Frontend catalog, cache, API client/proxy, auth UI, course overview, review queue, Phase 3C preferences/bookmarks, learning path, Phase 2 content/reference, live examples, route registration, runner status UI, and UI polish contract tests.
- JSX/JS/MJS parsing (50 files) and CSS brace balance (21 files).

## External or machine-specific gates still required

- Run `npm ci` and `npm run build` on the actual Windows checkout. The Linux validation sandbox does not have a usable Vite install; no successful production build is claimed.
- Inspect the user’s working-tree diff before overlaying this patch. The archive supplies actual replacement/new files and an installer with automatic backups; it intentionally does not contain a unified `git apply` patch.
- Confirm production Neon is at migration `0004_phase5_capabilities` after verifying a current backup. Do not apply migrations blindly from a local terminal.
- Live Brevo sender approval, authorized outbound IP ranges, test email delivery, registration verification, password reset, and account-change emails remain unverified.
- Live Razorpay test-mode plans, webhook delivery from the provider, subscription renewal/cancellation/refund lifecycle and actual provider confirmation remain unverified.
- Isolated runner deployment and security testing on a dedicated disposable host remain unverified. Keep `RUNNER_SERVICE_URL`/token unset and the Run button disabled until deployment hardening and provider configuration are complete.
- Real browser smoke tests for responsive UI, accessibility, course content, learner bookmarks/progress across devices, and live account flows must be performed after local build and deployment.
- Backup/restore against a separate disposable Postgres target and production monitoring/alerts remain operational tasks. No production database or real payment was changed by these isolated tests.

## Safety constraints

- No `.env`, `.venv`, `node_modules`, database dumps, or secrets are included in the patch archive.
- Existing `vercel.json`, environment settings, course content files, and CSS imports are not overwritten by this patch unless explicitly listed in the manifest.
- Do not use the review self-rating as mastery evidence or XP. XP remains awarded only by server-verified completion and grading logic.
- Do not deploy the isolated runner beside the main API or any workload containing production secrets.
