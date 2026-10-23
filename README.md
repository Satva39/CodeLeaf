# CodeLeaf — Responsive Learning Platform Starter

A responsive React/JSX UI scaffold and Python/FastAPI backend foundation for a visual-first programming education platform inspired by the *learning flow* of W3Schools without copying its branding or exact interface.

## Included in this starter

- Responsive homepage and course catalog with search/category filters.
- Course reader with grouped/collapsible sidebar, previous/next navigation, visual concept flows, code panes, task hints, recap, bookmarks and an ad-slot placeholder.
- References, exercises/challenges, guided project catalog, web playground with sandboxed preview, progress dashboard, weekly leaderboard, certificate catalog/exam demo, profile/avatar customization, and plan comparison page.
- Account registration, login/logout, verified email, one-time password recovery, change-password/email, data export and account deletion; HttpOnly revocable sessions, signed double-submit CSRF protection, hashed tokens and persistent auth rate limits.
- PostgreSQL/SQLAlchemy schema for courses, modules, lessons, user accounts, lesson progress, bookmarks, XP transactions, exam attempts, certificates, project submissions, payment records, entitlements and webhook events.
- API routes for profile stats, bookmarks, lesson completion/XP, plan catalog, billing display, subscription cancellation request, payment signature verification and signed/idempotent payment webhook handling.
- Razorpay Checkout wiring for one-time Full Access Orders and recurring Pro/Max Subscriptions. The server owns prices and verifies orders/subscription metadata; the browser never sends a price.
- `docs/PROJECT_BLUEPRINT.md`: full product inventory, base architecture, visual and learning flow, feature priorities, schemas and launch checklist.
- `docs/MASTER_COURSE_PROMPT.md`: reusable master prompt to generate a full syllabus, lesson manifest, visuals, practice, projects and exam for each language/technology. It uses the uploaded HTML curriculum PDF as a *depth/organization reference*, not as a syllabus to copy verbatim for every course.

> **This is a base scaffold, not a finished production LMS.** Several dashboard numbers, the leaderboard, certificate/exam experience and some learning interactions are demonstration UI. Demo progress/bookmarks use `localStorage`; account API progress/bookmark endpoints begin syncing only after published course/module/lesson records are imported. A content-admin panel, real multi-language code runner, robust certificate PDF generation and production ad network integration are future phases. Live Razorpay transactions have not been run from this environment.

## Languages and main technology choices

| Use | Technology |
|---|---|
| Website structure | HTML5 |
| Styling and responsive UI | CSS3 |
| Application source | JavaScript (modern ECMAScript) and React **JSX** — no TypeScript |
| Backend | Python 3 + FastAPI + Pydantic |
| Database | PostgreSQL; SQL for queries and schema |
| ORM / migrations | SQLAlchemy 2 + Alembic (initial reviewed production migration still required) |
| Payments | Razorpay Checkout + Orders + Subscriptions + signed webhooks |
| Course manifests / API payloads | JSON |
| Local service config | YAML (`docker-compose.yml`); shell commands vary by Windows PowerShell or Bash |

The starter catalog currently includes HTML, CSS, JavaScript, Python, SQL, React, C++, Java, PostgreSQL, Git, Docker and AI Foundations. That is the *seed catalog*, not a maximum; use the master prompt once per language, framework, database or tool.

## 1. Start PostgreSQL

Install Docker Desktop, then from this project directory run:

```bash
docker compose up -d postgres
```

For local development only, `docker-compose.yml`, the root `.env.example`, and `backend/.env.example` agree on database `codeleaf`, user `codeleaf`, password `dev_only_password_change_me`, and PostgreSQL port `5432`. Compose binds the port to `127.0.0.1` only. From the repository root, optionally copy `.env.example` to `.env` to override Compose defaults; copy `backend/.env.example` to `backend/.env` separately for the API. These are local-only example credentials—never expose the database port publicly or reuse them in production.

## 2. Run the Python API

Python 3.11+ is recommended.

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux instead:
# source .venv/bin/activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` with at least:

```dotenv
APP_ENV=development
FRONTEND_ORIGINS=http://localhost:5173
DATABASE_URL=postgresql+psycopg://codeleaf:dev_only_password_change_me@localhost:5432/codeleaf
JWT_SECRET=REPLACE_WITH_A_LONG_RANDOM_SECRET
COOKIE_SECURE=false
```

Generate a secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`; paste the result as `JWT_SECRET`. Leave `COOKIE_SECURE=false` only for local HTTP development. Set it to `true` on an HTTPS deployment.

Create the development schema and seed the catalog:

```bash
python scripts/init_db.py
```

This helper uses SQLAlchemy `create_all()` and is intentionally blocked in `APP_ENV=production`. Use the included Alembic baseline migration for deployment; review and replace the compact metadata-based baseline with explicit operations before making ongoing production schema changes.

Start the API:

```bash
uvicorn app.main:app --reload
```

- API health: `http://localhost:8000/api/health`
- Interactive API docs: `http://localhost:8000/docs`

The API can start without a database for the health/course/plan catalog routes, but authentication, user data, and payments require `DATABASE_URL`.

## 3. Run the React/JSX frontend

Open another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Optional `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Visit the Vite URL printed in the terminal (normally `http://localhost:5173`). The React app uses JavaScript/JSX; do not rename files to `.ts`/`.tsx` or add TypeScript as the platform source language.

## 4. Razorpay test-mode setup

Do **not** put secret credentials in `frontend/.env` or in browser code.

1. Finish Razorpay merchant onboarding and use test-mode credentials first.
2. In Razorpay, create recurring monthly plans priced at exactly ₹299 and ₹699. Add their `plan_...` values as `RAZORPAY_PRO_PLAN_ID` and `RAZORPAY_MAX_PLAN_ID` in `backend/.env`.
3. Add `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` to the backend environment. Set `RAZORPAY_SUBSCRIPTION_TOTAL_COUNT` to a provider-supported cycle count and make the renewal policy clear to customers. The example value `1200` is a long horizon, **not a substitute for a reviewed billing policy**. Razorpay requires a finite number of cycles on a subscription; cancel-renewal is exposed as an API action and the paid period is kept separately from subscription state.
4. Register the exact HTTPS webhook URL `/api/payments/webhook` and enable the events relevant to orders/payments and subscription lifecycle (activation, charged, cancellation, pause/halt/resume as applicable).
5. Test success, failure, duplicate webhook delivery, cancellation at cycle end, renewal failure, refunds and reconciliation before going live.

The backend confirms one-time payment signatures and then fetches the provider payment to confirm captured status, amount and currency. Subscription checkout signatures are checked, but subscription entitlements are activated through the signed webhook path. Treat this as integration scaffolding until it has passed provider test-mode transactions and an independent security review. Confirm Razorpay's latest API limits and subscription lifecycle behavior before production. Reference docs: [Razorpay Python integration](https://razorpay.com/docs/server-integration/python/test-app/) and [Subscriptions API](https://razorpay.com/docs/api/payments/subscriptions/create-plan/?preferred-country=IN).

## Phase 1 hardening checks

Run these read-only checks from `backend/` before publishing content or deploying:

```powershell
python scripts/check_alembic_heads.py
python scripts/check_repository_hygiene.py
python scripts/validate_course_manifests.py --course html
python scripts/validate_course_manifests.py
python scripts/test_phase1_config.py
python scripts/test_dynamic_diagram_compatibility.py
python scripts/test_course_api_contract.py
python scripts/test_knowledge_check_api.py
python scripts/test_import_slug_rename.py
python scripts/test_course_import_safety.py
python scripts/test_migration_repeatability.py
python scripts/publish_all_courses.py
python scripts/check_release_readiness.py --skip-content-validation
```

From `frontend/`, run the serverless proxy's offline request/response contract tests with `node scripts/test_api_proxy.mjs`; syntax-check its route with `node --check 'api/proxy/[...path].js'`. A frontend production build requires `npm ci` to finish successfully first.

The publisher command is a dry run unless both `--apply --publish` are explicitly supplied. For deployment review, use `python scripts/check_release_readiness.py --production`. Add `--check-db` only when you intend to connect to the configured database. Add `--require-payments` to require Razorpay environment values (this does not make provider requests). The readiness script prints which external checks remain unverified. The original `0001_initial_schema` migration is a compact metadata baseline; do not rewrite an already-applied migration, and use explicit forward migrations for future schema changes.

## CodeLeaf course roadmap

The requested roadmap contains **62 tracks** across Web Development, Programming, Backend & APIs, Databases, Data & Analytics, AI & Machine Learning, Cloud & DevOps, Data Formats, Computer Science and Security. See `docs/COURSE_ROADMAP.md` for the complete categorized list. The tracks are marked as roadmap placeholders until reviewed curriculum manifests are imported; they are not represented as 62 completed courses.

## Deployment architecture

- **Frontend:** Vercel, rooted at `frontend/`; `frontend/vercel.json` provides SPA route fallback. The Vercel rewrite sends `/api/*` through the same-origin serverless proxy at `frontend/api/proxy/[...path].js`. Configure `CODELEAF_API_ORIGIN` in Vercel Project Settings to the actual Render API origin (for example, `https://your-real-api-host.onrender.com`, with no path). This server-only variable is not bundled into browser JavaScript. Leave `VITE_API_BASE_URL` unset in Vercel so API requests use the same-origin proxy and session cookies remain first-party. The proxy forwards raw request bodies for signature-verified webhooks; it does not itself prove that a live webhook or deployment works.
- **Backend:** Render, configured by root `render.yaml` with `backend/` as the service root. Configure `DATABASE_URL` using the PostgreSQL connection URI from Neon, `FRONTEND_ORIGINS` to the exact deployed frontend origin, and use a generated `JWT_SECRET`.
- **Database:** Neon managed PostgreSQL. For the first Render deployment, use the direct PostgreSQL connection URI with SSL enabled; consider Neon’s pooled URI if concurrency later requires it. Never commit database credentials.
- **Schema:** Render's start command runs `alembic upgrade head` before starting Uvicorn. The included initial migration creates the current starter schema; review and replace its compact metadata-based baseline with explicit migrations before ongoing production schema changes.
- **CI:** `.github/workflows/checks.yml` uses `npm ci`, syntax-checks and tests the Vercel proxy, builds the frontend, compiles Python, checks the Alembic head and repository hygiene, validates HTML and all course manifests/diagrams, and runs offline configuration/API/import/migration regressions. CI never publishes all courses or claims remote provider readiness.
- **Payments:** Keep Razorpay credentials in Render backend environment settings. Use test mode until webhook, failure, renewal, cancellation and reconciliation flows have all been validated.
- **Code execution:** The current playground is only an HTML/CSS/JS iframe preview. A separately isolated runner is required before supporting user-submitted Python, C/C++, Java or other server-executed languages.

### Deploy order

1. Push this repository to GitHub.
2. Create a Neon PostgreSQL project and copy its connection URI.
3. Deploy the API service on Render using `render.yaml`; set `DATABASE_URL` to Neon’s direct SSL connection URI and set `FRONTEND_ORIGINS` to the exact deployed Vercel origin after it exists.
4. Deploy `frontend/` on Vercel with root directory `frontend`, build command `npm run build`, and output directory `dist`. In Vercel Project Settings, set the server-only `CODELEAF_API_ORIGIN` to the Render service origin (HTTPS, no path). Leave `VITE_API_BASE_URL` unset so `/api/*` uses the Vercel proxy.
5. Redeploy the frontend after setting `CODELEAF_API_ORIGIN`; the source configuration intentionally contains no deployment-specific Render hostname.
6. Once you know the Vercel domain, set Render's `FRONTEND_ORIGINS` to that exact origin (no trailing slash) and redeploy the API.
7. Test health, account, progress, and payment flows in test mode before sharing publicly.

For production, a custom domain with frontend and API on the same site (for example `codeleaf.example` and `api.codeleaf.example`) can reduce cross-site cookie issues. Use HTTPS. Render free web services may spin down after inactivity and can have cold starts; check the provider's current plan limits before launch.

## Authentication and email setup (Phase 4 P4-1)

The backend now requires email verification for newly registered accounts. Existing accounts are marked verified by the forward migration to avoid unexpectedly locking out current learners. JWT session cookies are HttpOnly; a separate signed CSRF cookie is sent as `X-CSRF-Token` on browser writes. Session digests are stored in PostgreSQL so logout, password changes, email changes, and account deletion can revoke sessions. Apply the migration before starting the upgraded API.

For local work, configure `FRONTEND_BASE_URL=http://localhost:5173` and `EMAIL_TEST_MODE=true` in `backend/.env`. Test mode **does not send email**: the API explicitly returns a local-only action URL for manual testing. Never enable test mode in production. For real delivery, set `EMAIL_TEST_MODE=false`, `FRONTEND_BASE_URL` to the public HTTPS frontend origin, `EMAIL_FROM`, `SMTP_HOST`, and the provider's appropriate `SMTP_PORT`/`SMTP_USE_TLS`; set `SMTP_USERNAME` and `SMTP_PASSWORD` when the SMTP relay requires authentication. Email service errors are reported as failures; the API does not claim that a message was delivered when it was not. Keep these values in the backend host's secret/environment settings, never in Vite/browser variables.

Rate limiting is stored as short-lived keyed digests in PostgreSQL and configured with `AUTH_RATE_LIMIT_WINDOW_SECONDS` and `AUTH_RATE_LIMIT_MAX_ATTEMPTS`. It keys requests by client address and account/action. Ensure the hosting platform forwards client IPs through a trusted proxy configuration before relying on IP-based limits; do not accept arbitrary client-supplied forwarding headers. Login failures and recovery responses use generic messages to reduce account enumeration. Password-reset and verification links are one-use and expire; only their SHA-256 digests are persisted.

Account export is available at `GET /api/me/export`. `POST /api/me/delete` requires the current password, removes learning-progress/profile data, disables the account, revokes sessions, cancels recorded entitlements, and anonymizes identity fields. Payment/audit records may be retained in anonymized form for accounting and legal obligations. Review privacy, retention, and customer-support policies for the deployment jurisdiction before public launch.

The new auth migration is `0003_auth_lifecycle`. Apply with `alembic upgrade head` after backing up production data. JWT sessions created before this migration are intentionally not accepted by the new revocable-session check; users will need to sign in again once the migration is deployed.

## 5. API route overview

| Route | Purpose |
|---|---|
| `GET /api/health` | Health check/config status |
| `GET /api/courses`, `GET /api/plans` | Public starter catalog and server-side prices |
| `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout` | Account session flows |
| `POST /api/auth/verify-email`, `POST /api/auth/verification/resend` | Verify and resend email confirmation |
| `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` | One-time password recovery |
| `POST /api/auth/change-password`, `POST /api/auth/change-email`, `POST /api/auth/verify-email-change` | Secure account credential/email changes |
| `GET /api/me/export`, `POST /api/me/delete` | Account data export and verified deletion |
| `GET /api/me`, `PATCH /api/me/profile` | Profile, summary stats, preferences |
| `GET /api/me/progress`, `POST /api/me/progress/{course_slug}/{lesson_slug}` | Completion and non-repeatable XP award after content is published |
| `GET /api/me/bookmarks`, `PUT/DELETE /api/me/bookmarks/{course_slug}/{lesson_slug}` | Saved lessons after content is published |
| `GET /api/me/billing` | Active entitlements and subscription status |
| `POST /api/payments/create` | Server-owned order or monthly subscription creation |
| `POST /api/payments/verify`, `POST /api/payments/verify-subscription` | Checkout callback signature and provider-status checks |
| `POST /api/payments/{subscription_id}/cancel` | Request cancellation at the end of the billing period |
| `POST /api/payments/webhook` | Validates Razorpay's webhook HMAC and deduplicates events |
| `GET /api/me/certificates`, `GET /api/certificates/verify/{public_id}` | Certificate data model endpoint and verification lookup |

## 6. Curriculum workflow

1. Use `docs/MASTER_COURSE_PROMPT.md` and attach `HTML(1).pdf` as the example of expected curriculum depth.
2. Replace `[COURSE_NAME]`, `[COURSE_TYPE]`, official docs URL and supporting sources. Request the entire syllabus/manifest *before* the detailed lesson batches.
3. Review the course path and QA notes; then expand Module 1 and continue in controlled batches without changing IDs.
4. Store each approved manifest as JSON in version control; build a validated importer/admin CMS to populate `courses`, `course_modules`, and `lessons`.
5. Publish a lesson only after content, examples, visuals, solution handling, sources and accessibility have been reviewed.

## Production acceptance checklist

- Apply reviewed Alembic migrations and test backups/restore; configure production CORS origins, HTTPS-only secure cookies, rate limiting and monitoring.
- Add CSRF/session hardening, email verification, password reset, account deletion/export, privacy notice, terms and support process.
- Enforce every plan entitlement server-side, including ad suppression and XP boost; add refunds, invoices/tax handling, renewal failures, chargebacks and subscription reconciliation.
- Keep ads out of lesson code, authentication, exams, checkout, results and certificate verification; show no ads for Max and Full Access; implement privacy/consent controls before connecting an ad network.
- Add admin roles/content publishing, question bank, secure timed exam attempts, server-side pass scoring and certificate ID/PDF generation.
- Use an isolated code runner for Python/C/C++/Java/etc.; never execute submitted code inside FastAPI or the same container as production data. The current web playground uses a sandboxed iframe preview only.
- Add automated tests for auth, progress/XP idempotency, payment callbacks/webhooks, subscription cancellation, exam grading, accessibility and responsive breakpoints.
- Test desktop/mobile, keyboard navigation, zoom, contrast, screen readers, empty/error/loading states, and a realistic low-bandwidth experience.
