# CodeLeaf Runner integration and deployment setup

This setup connects the existing CodeLeaf backend to the separate `CodeLeaf-Runner` service. It does not require a frontend rebuild or a database migration: the current CodeLeaf backend already has the authenticated Runner client, `/api/runner/status`, `/api/runner/jobs`, polling/cancellation routes, and the Render environment-variable entries.

## 1. Confirm the two repositories

- CodeLeaf website/backend: `Satva39/CodeLeaf` (branch `master`)
- Execution service: `Satva39/CodeLeaf-Runner` (branch `main`)

Keep them as separate deployments. Do not copy the Runner's `docker-compose.yml` into the CodeLeaf website deployment, and do not run learner code inside the Render API service.

## 2. Configure the Runner host

In the root `.env` of the `CodeLeaf-Runner` checkout, set a long random service token and a different Docker-gateway token. Generate them locally in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Run the command twice. Store the first value as `CODELEAF_RUNNER_SERVICE_TOKEN`; store the second as `RUNNER_DOCKER_GATEWAY_TOKEN`. Do not paste either value into chat, commit them, put them in Vercel, or expose them in browser JavaScript.

Example variable names (replace the values with the generated secrets):

```dotenv
CODELEAF_RUNNER_SERVICE_TOKEN=<first-generated-secret>
RUNNER_DOCKER_GATEWAY_TOKEN=<different-second-generated-secret>
RUNNER_PRODUCTION_MODE=false
```

Keep the production-mode setting `false` only during local validation. For a production host, follow `docs/PHASE_5_SECURITY_SCALING.md` in the Runner repository, set `RUNNER_PRODUCTION_MODE=true`, configure exact HTTPS WebSocket origins, pin external images to immutable digests, and run the security preflight. Do not use placeholder digests.

The Runner's regular API is port `8080` inside the Compose network. Redis, Piston port `2000`, the Docker gateway, and the Piston admin endpoint must not be publicly exposed.

## 3. Local development connection

The ARM64 overlay supplied for validation maps the Runner API to `127.0.0.1:8081`. Once `/health/ready` succeeds, add these values to `CodeLeaf/backend/.env`:

```dotenv
RUNNER_SERVICE_URL=http://127.0.0.1:8081
RUNNER_SERVICE_TOKEN=<same-first-generated-secret>
RUNNER_SERVICE_TIMEOUT_SECONDS=8
RUNNER_JDOODLE_FALLBACK_ENABLED=true
```

`RUNNER_SERVICE_URL` is the base URL only. Do not append `/v1/jobs` or `/api`.

The local Runner Redis service was previously restarting on the AMD64 Docker Desktop host because that environment selected the AMD64 Redis image while the Compose overlay requested ARM64 and the emulated kernel emitted the Redis `ARM64-COW-BUG` warning. Until Redis and `/health/ready` are healthy, the local integration check cannot pass. Do not work around this by exposing Redis or weakening service isolation. Re-run the integration check only after the Runner stack is healthy on a suitable host.

## 4. Configure the deployed CodeLeaf backend on Render

After the Runner is deployed on a dedicated Linux ARM64 host and a protected Render-to-Runner network path is available, configure these environment variables on the existing `codeleaf-api` Render service:

```dotenv
RUNNER_SERVICE_URL=https://<protected-runner-api-origin>
RUNNER_SERVICE_TOKEN=<same-first-generated-secret>
RUNNER_SERVICE_TIMEOUT_SECONDS=8
RUNNER_JDOODLE_FALLBACK_ENABLED=true
```

Use the HTTPS base origin only; no path, query, fragment, username, or password. The production CodeLeaf settings validator rejects a non-HTTPS Runner URL and requires the URL and token to be configured together.

Important networking detail: the Runner Compose port is bound to host loopback (`127.0.0.1`). A Render service cannot reach another host's loopback address. Connect Render and the Runner host through a private overlay/tunnel or a carefully restricted TLS reverse proxy. Restrict the route to the Runner API only, and apply an allowlist where the chosen network/provider supports it. Never publish Redis `6379`, Piston `2000`, or Docker gateway `2375` to the internet.

Keep JDoodle credentials available during rollout. `RUNNER_JDOODLE_FALLBACK_ENABLED=true` lets CodeLeaf use JDoodle for languages not yet installed in Piston. A job that is accepted by an available Runner runtime is not silently re-submitted to JDoodle if the Runner later fails; this avoids duplicate execution. Disable fallback only after all intended languages and database engines pass real production tests.

## 5. Verify the Runner before enabling it for learners

On the Runner host, first run:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health/ready
```

Use port `8081` instead if the ARM64 validation overlay is active. Readiness must report `status: ready`, including Redis, Piston, the execution worker, and the database worker when database execution is enabled.

From the CodeLeaf backend folder, run the read-only integration check:

```powershell
cd E:\Code_Leaf\backend
python scripts\check_runner_integration.py
```

To submit a harmless Python smoke job and verify polling/results as well:

```powershell
python scripts\check_runner_integration.py --execute-smoke --language python
```

The script prints capability counts and bounded test output only. It does not print the service token. Run it only after the Runner readiness check succeeds.

Then start CodeLeaf locally and request:

```text
GET http://127.0.0.1:8000/api/runner/status
```

Expected fields include `runner.configured`, `runner.reachable`, `supported_languages`, `providers_by_language`, and `database_engines`. The supported-language list is based on live installed Piston runtimes, not every language in the registry.

## 6. End-to-end CodeLeaf verification

Sign in to CodeLeaf and open the Playground. Test one installed language at a time:

1. Run a short Python program that prints a known string.
2. Confirm the result reaches the Terminal panel, including `stdout`, `stderr`, and exit code.
3. Test one compiled runtime (for example C++), including a compile-error sample.
4. Test stdin with a simple input-reading program.
5. Test a multi-file project using flat root-level filenames.
6. Test SQLite, MySQL, and PostgreSQL only when their entries report `available: true`; these are disposable exercise databases and must never point to CodeLeaf's production database.
7. Verify another account cannot retrieve the first account's job ID.
8. Confirm HTML/CSS/React remain browser previews and unsupported server languages are not shown as executable.

CodeLeaf routes requests through its authenticated backend. The shared Runner token and Runner origin must never be sent to the browser.

## 7. Rollback

If a rollout issue occurs, unset both `RUNNER_SERVICE_URL` and `RUNNER_SERVICE_TOKEN` together on the CodeLeaf backend, or point them back to a known-good protected Runner origin. Keep `RUNNER_JDOODLE_FALLBACK_ENABLED=true` and the existing JDoodle credentials until the Runner has passed the full rollout checklist. Do not remove the JDoodle fallback as part of the initial connection.

## 8. Scope and remaining deployment gate

The CodeLeaf-to-Runner HTTP job integration is already implemented in the current CodeLeaf repository. This document and the accompanying check script make the connection repeatable and verifiable. They do not claim that the ARM64 stack has passed native ARM64 execution testing: the earlier local validation ran under AMD64 Docker Desktop emulation, and Redis was not healthy there. Production deployment still requires a healthy native ARM64 Linux host, image pinning, security preflight, protected networking, installed runtimes, and live smoke tests.
