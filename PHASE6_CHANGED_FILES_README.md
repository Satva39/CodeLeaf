# CodeLeaf Phase 6 — Runner Integration (changed files only)

This archive contains the Phase 6 integration patch for the existing CodeLeaf repository. It is designed to be extracted into the **repository root** (the directory containing `backend/`, `frontend/`, and `render.yaml`). It does not contain `.env`, database data, `node_modules`, `.git`, or a full project copy.

## Included changes

- Backend-only authenticated client for the separate CodeLeaf Runner.
- Live discovery of installed Runner languages and available SQLite/MySQL/PostgreSQL engines.
- Authenticated code-job, multi-file job, database-job, polling, and cancellation routing.
- Runner-first execution with explicit JDoodle rollback for supported single-file languages when the Runner does not advertise the requested runtime.
- No duplicate JDoodle submission after the Runner has accepted a runtime selection and a Runner submission fails.
- Existing quotas, per-user job ownership, idempotency, and existing `runner_jobs` table are retained. No database migration is included or required.
- Playground and Try-It database setup SQL support, multi-file submissions, byte/file limits, and result metadata.
- Backend environment and Render configuration entries; service token remains backend-only.
- Focused backend and frontend regression tests plus an integration guide.

## Apply on Windows

1. Make a backup or commit your current CodeLeaf changes first.
2. Extract this ZIP into `E:\Code_Leaf` (or your actual CodeLeaf repository root), allowing the listed files to replace their matching paths.
3. Do **not** replace your existing `backend/.env` with `.env.example`. The archive does not include `.env`.
4. Review the changed files with Git before committing:

   ```powershell
   cd E:\Code_Leaf
   git status --short
   git diff -- backend/app/config.py backend/app/phase5_routes.py frontend/src/pages/PlaygroundPage.jsx frontend/src/pages/TryItPage.jsx render.yaml
   ```

5. Install backend dependencies only if your environment is missing them. `httpx` is already in the existing backend requirements.
6. Add the local Runner settings to `backend/.env` (do not commit this file):

   ```dotenv
   RUNNER_SERVICE_URL=http://127.0.0.1:8080
   RUNNER_SERVICE_TOKEN=<same secret as CODELEAF_RUNNER_SERVICE_TOKEN on the Runner host>
   RUNNER_SERVICE_TIMEOUT_SECONDS=8
   RUNNER_JDOODLE_FALLBACK_ENABLED=true
   ```

   The local URL is only for development when the CodeLeaf backend can reach the Runner's loopback proxy on the same machine. Production configuration intentionally requires HTTPS.

7. On the Runner host, configure `CODELEAF_RUNNER_SERVICE_TOKEN` with the **same newly generated random secret**. Keep it distinct from `JWT_SECRET`, database credentials, and all other secrets.
8. Restart the local Runner and CodeLeaf backend, then verify `GET /api/runner/status` while authenticated. It should only advertise currently installed Runner runtimes and available database engines, and JDoodle languages only when fallback is enabled and its credentials are configured.

## Test commands

From `E:\Code_Leaf\backend`:

```powershell
python -m pytest -q --ignore=content/courses
python scripts/test_runner_config_status.py
python scripts/test_jdoodle_integration.py
python scripts/test_phase6_runner_integration.py
```

From `E:\Code_Leaf\frontend`:

```powershell
npm run test:runner-status
npm run test:playground-output-modes
npm run test:language-workspace
npm run test:phase6-runner-integration
npm ci
npm run build
```

`--ignore=content/courses` excludes generated lesson/course starter folders whose standalone sample tests reuse module names and cause collection collisions; it does not exclude the backend application's test suite.

## Production rollout requirements

On the **CodeLeaf backend service only**, set these Render environment variables:

- `RUNNER_SERVICE_URL`: HTTPS origin of the production Runner API, without `/v1` path.
- `RUNNER_SERVICE_TOKEN`: same secret as Runner's `CODELEAF_RUNNER_SERVICE_TOKEN`.
- `RUNNER_SERVICE_TIMEOUT_SECONDS`: `8` by default.
- `RUNNER_JDOODLE_FALLBACK_ENABLED`: `true` throughout rollout.

The local Windows Docker setup is not a production execution host. Before public launch, deploy Runner on a dedicated Linux host with cgroup-backed isolation, immutable runtime image digests, private/restricted HTTPS ingress, production secret management, and the full production security preflight. Do not expose Piston, Redis, Docker gateway/socket, database worker, or database containers publicly.

## Acceptance checks before retiring JDoodle

1. Confirm the backend Runner status response contains no Runner URL or token.
2. Submit and poll a small installed-language code job with a test account.
3. Submit and verify a two-file program using a helper file.
4. Test SQLite, MySQL, and PostgreSQL query/setup results.
5. Verify a queued-job cancellation and a running-job cancellation response.
6. Verify a language not installed on Runner uses JDoodle only when the fallback toggle and credentials are enabled.
7. Verify a Runner submission failure is not silently sent to JDoodle a second time.
8. Verify cross-user job access is denied.

Keep JDoodle credentials and the fallback enabled until all production acceptance checks pass. For an emergency full Runner rollback, clear both `RUNNER_SERVICE_URL` and `RUNNER_SERVICE_TOKEN` on the CodeLeaf backend, leave the JDoodle fallback enabled, and restart/redeploy the backend.

## Validation performed while preparing this archive

- Backend: `60 passed` using `python -m pytest -q --ignore=content/courses`.
- Dedicated Phase 6 bridge tests: `13 passed`.
- JDoodle adapter/fallback regression tests: `15 passed`.
- Runner status tests: `3 passed`.
- Existing frontend Runner status, Playground output-mode, and language-workspace tests passed.
- New frontend Phase 6 contract test passed.
- Modified `PlaygroundPage.jsx` and `TryItPage.jsx` passed JSX syntax transpilation.
- `render.yaml` parsed successfully and backend `.env.example` contains the documented Runner settings.

The full Vite production build was not run in this preparation environment because frontend dependencies were not installed in the supplied project snapshot. Run `npm ci` and `npm run build` locally before deployment. These tests do not replace end-to-end testing against a deployed production Runner or production isolation certification.
