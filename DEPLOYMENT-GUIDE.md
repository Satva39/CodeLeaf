# CodeLeaf Deployment Guide (Vercel + Render + Neon)

This guide deploys the existing React/Vite frontend, FastAPI backend, and PostgreSQL database. It does not claim that every curriculum is published, that the isolated code runner is production-ready, or that Razorpay live payments have passed an end-to-end test.

## 0. Apply and verify the privacy/settings patch

From `frontend/` run:

```powershell
npm ci
npm run test:privacy-settings
npm run test:deployment-config
npm run test:ui-polish
npm run test:workspace
npm run test:exercise-ui
npm run test:catalog
npm run test:api-cache
npm run test:api-client
npm run test:auth-ui
npm run test:course-overview
npm run test:lesson-timeout
npm run build
```

The Profile page links to the existing persisted `/api/me/learning-preferences` controls for analytics consent and review preferences. This does not add controls for public-profile or certificate visibility, which are not currently implemented.

## 1. Clean the repository and push to GitHub

1. Review `git status --short`.
2. Confirm `.gitignore` excludes `.env`, `backend/.env`, `frontend/.env`, `.venv/`, `node_modules/`, and `dist/`.
3. Before committing, inspect `git diff --cached --name-only` and never commit real credentials, database URLs, API keys, private user data, database dumps, or `.env` files. If a secret has ever been committed, rotate it; adding it to `.gitignore` does not erase Git history.
4. Commit and push the reviewed project to a GitHub repository. Connect that repository to both Vercel and Render.

## 2. Create a production database in Neon

1. Create a separate production Neon project/database; do not reuse a development database.
2. Select a region close to the Render service region.
3. Use the Neon Connect dialog to copy a PostgreSQL connection string with SSL (`sslmode=require`). For the first deployment, turn connection pooling off and use the direct connection URL for migrations.
4. Save the URL privately. You will add it only to Render as `DATABASE_URL`; never place it in a frontend variable or GitHub.
5. Back up any existing production database before any schema migration. The Render start command runs `alembic upgrade head` before Uvicorn starts.

## 3. Deploy the frontend to Vercel first

The first frontend deployment is used to establish the exact production HTTPS origin needed by the backend. API calls can return a configuration error until the backend is deployed.

1. In Vercel, import the GitHub repository.
2. Set **Root Directory** to `frontend`.
3. Use **Build Command** `npm run build` and **Output Directory** `dist`. Vercel can install dependencies from `frontend/package-lock.json`.
4. Deploy and copy the exact HTTPS site origin, e.g. `https://your-project.vercel.app`. Do not include a page path or trailing slash in the environment values.
5. Keep `VITE_API_BASE_URL` unset in Vercel. The frontend should use the same-origin `/api/*` route. The Vercel rewrite routes those requests to the serverless proxy.

## 4. Deploy the API to Render

1. In Render, create a Blueprint from the same repository's root `render.yaml`.
2. Provide these values when prompted or under the API service's **Environment** settings:
   - `DATABASE_URL`: the Neon direct PostgreSQL connection string with SSL.
   - `FRONTEND_ORIGINS`: the exact Vercel origin, no trailing slash. If multiple frontend origins are genuinely used, comma-separate exact HTTPS origins.
   - `FRONTEND_BASE_URL`: the primary Vercel origin; it must also appear in `FRONTEND_ORIGINS`.
   - `EMAIL_FROM`: a verified sender address from your email provider.
   - `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`: values from your SMTP/email provider.
3. The Blueprint sets `APP_ENV=production`, `PREVIEW_DRAFT_COURSES=false`, `COOKIE_SECURE=true`, and `EMAIL_TEST_MODE=false`, and generates `JWT_SECRET`. Do not override these to development/test values in production.
4. The Blueprint supplies default SMTP settings (`SMTP_PORT=587`, `SMTP_USE_TLS=true`) and bounded auth rate-limit settings. Confirm your mail provider's exact port and TLS requirements; use the provider's instructions if they differ.
5. Deploy and inspect logs. The API must start successfully and `/api/ready` must return 2xx with the required database schema present. Fix configuration or migration errors rather than bypassing the readiness check.

## 5. Connect the frontend to the deployed API

1. In Vercel Project Settings → Environment Variables, add `CODELEAF_API_ORIGIN` for **Production**. Its value is the Render service origin only, e.g. `https://codeleaf-api.onrender.com`—no `/api` suffix, path, credentials, query, or trailing slash.
2. Keep `VITE_API_BASE_URL` unset for Vercel production.
3. Redeploy the frontend after saving the environment variable.
4. Confirm the `frontend/vercel.json` rewrite sends `/api/:path*` to `/api/proxy/:path*`; do not hard-code a real service hostname into frontend source or Vercel's rewrite target.

## 6. Test the live system before public launch

Replace the hostname below with the exact Render hostname:

```powershell
Invoke-RestMethod https://your-render-service.onrender.com/api/health
Invoke-RestMethod https://your-render-service.onrender.com/api/ready
```

Then visit the Vercel site and test all of the following with test accounts:

- Register, receive and click the email verification link, log in, log out, reset password and change password.
- Open a published course and lesson; complete a lesson and exercise; confirm XP is awarded once and progress survives reload.
- Save and reload privacy/review preferences; opt out of analytics and confirm the setting persists.
- Verify account A cannot read account B's progress, preferences, portfolio, or runner jobs.
- Verify private portfolio projects stay private, account export works, and account deletion requires password confirmation.
- Inspect browser Console, Network and Render logs for errors, CORS failures, 401/403/404/500/503 responses, and slow database requests.

Because `PREVIEW_DRAFT_COURSES=false`, unpublished content is intentionally hidden. Publish only reviewed courses, using manifest validation and the existing import workflow; never publish every draft merely to make the catalog look full.

## 7. Email, payments, and the code runner

- **Email:** Before production, verify your sender/domain with your SMTP provider and test registration, verification, password reset, and email change. `EMAIL_TEST_MODE` must remain `false`.
- **Razorpay:** Configure `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `RAZORPAY_PRO_PLAN_ID`, and `RAZORPAY_MAX_PLAN_ID` in Render only after creating the matching plans. Start with Razorpay test-mode credentials and verify successful/failed checkout, webhook signatures, subscription activation/cancellation, and idempotency. Change to live credentials only after test-mode validation and merchant/provider approval. Never put secrets in Vite variables.
- **Code execution:** The browser HTML/CSS/JavaScript preview is not the same as a secure multi-language runtime. Do not expose server-executed code running through the main FastAPI app. The separately isolated runner needs a dedicated Docker-capable environment, a long shared token, strict network/resource isolation, and independent security tests before configuring `RUNNER_SERVICE_URL` and `RUNNER_SERVICE_TOKEN`.
- **Content:** Some curriculum cards represent draft/roadmap content. A successful deployment does not mean every course, exam, certificate, or framework has reviewed and published content.
- **Availability:** Render free web services can spin down after inactivity and have cold starts. Choose an appropriate plan if consistent response times are required.

## 8. Keep it healthy

- Use HTTPS everywhere and a custom domain only after the default domains work correctly.
- Create and test a database backup/restore routine before real learner data is stored.
- Monitor Render deploy logs and service events, and check Vercel function logs for proxy errors.
- Keep a staging database/project separate from production, test migrations in staging first, and keep secrets in provider environment settings rather than source files.
- Do not announce a fully production-ready platform until payment flows, privacy/legal notices, course publishing, accessible mobile workflows, and isolated execution have been independently verified.
