# CodeLeaf Runner — Phase 6 integration and rollout

This phase connects the CodeLeaf FastAPI backend to the separate CodeLeaf Runner service. Learner source code is sent from the authenticated CodeLeaf backend to the private Runner API; it is never sent directly from the browser to Piston, Redis, the Docker gateway, or the database worker.

## Architecture

```text
Browser (React/Vite)
  | authenticated /api/runner/* requests
  v
CodeLeaf API (FastAPI + existing PostgreSQL)
  | X-Runner-Key + X-CodeLeaf-User
  | HTTPS server-to-server only
  v
CodeLeaf Runner API
  | Redis Streams / isolated workers
  +--> Piston runtime sandbox
  +--> disposable SQLite / MySQL / PostgreSQL database jobs
```

The CodeLeaf application database schema is unchanged. Runner job ownership and idempotency are recorded in the existing `runner_jobs` table. The backend owns the Runner token and adds both authentication headers; no Vite variable or browser bundle contains a Runner secret.

## Provider selection

1. The public `GET /api/runner/status` endpoint reads the live authenticated Runner language catalogue and database-engine catalogue.
2. Only languages with `available: true` and database engines with `available: true` are advertised as CodeLeaf Runner capabilities.
3. Code and multi-file submissions use `POST /v1/jobs`; database submissions use `POST /v1/database/jobs`.
4. The backend polls or cancels jobs using the matching code or database endpoint and scopes every job request to the authenticated CodeLeaf user ID.
5. JDoodle remains an explicitly configured rollback provider for supported single-file languages when the Runner does not advertise that language. SQLite does not fall back to JDoodle.
6. Once a live Runner runtime has been selected for a submission, a Runner submission error is returned to the caller. The same source is not silently submitted to JDoodle as a second execution, avoiding duplicate work or unexpected side effects.

The Runner accepts at most 10 files per code job, 64 KiB per file, 128 KiB total source and 16 KiB stdin under the default deployment configuration. File names must be flat root-level names. The Playground submits the active file first with compatible same-language source files and common text/data assets. The Try-It page remains a single-file workflow. Browser HTML/CSS/React preview behavior is unchanged.

## Environment variables

### On the CodeLeaf Runner host

Set the existing Runner secret:

```dotenv
CODELEAF_RUNNER_SERVICE_TOKEN=<long-random-secret-at-least-32-characters>
```

Use a newly generated random secret. Do not reuse `JWT_SECRET`, a database password, or any other application key.

### On the CodeLeaf backend deployment (Render)

Set these variables on the **backend service only**:

```dotenv
RUNNER_SERVICE_URL=https://<private-runner-api-origin>
RUNNER_SERVICE_TOKEN=<the-same-runner-service-secret>
RUNNER_SERVICE_TIMEOUT_SECONDS=8
RUNNER_JDOODLE_FALLBACK_ENABLED=true
```

`RUNNER_SERVICE_URL` is the HTTPS origin only. Do not append `/v1/jobs`, `/v1/languages`, or any other path. The backend appends API paths itself. The URL must be reachable from the Render backend; `localhost`, `127.0.0.1`, a developer workstation address, and the local Windows proxy are not production addresses.

The Runner API must be reachable through a private network path or a restricted HTTPS endpoint with TLS. Restrict ingress to the CodeLeaf backend where the hosting platform permits it. Do not expose Piston, Redis, the Docker socket gateway, database-worker, database containers, or the local Piston admin proxy to the public internet. Keep `X-Runner-Key` required at the Runner API and keep the token out of URLs, logs, browser configuration, and client responses.

`RUNNER_JDOODLE_FALLBACK_ENABLED=true` preserves the existing JDoodle fallback for supported languages that are not currently installed on the Runner. Set it to `false` to disable that fallback after the Runner rollout has been validated. The actual JDoodle fallback also requires the existing `JDOODLE_CLIENT_ID` and `JDOODLE_CLIENT_SECRET` values.

The same keys are included in `backend/.env.example`. Do not copy secrets into `frontend/.env`, `VITE_*` variables, source files, or this document.

## Local development

The Runner repository's local Compose overlay publishes a loopback-only proxy at `127.0.0.1:8080`. This is for local diagnostics and local backend development only. If the CodeLeaf backend runs on the same Windows host, a local `.env` can use:

```dotenv
RUNNER_SERVICE_URL=http://127.0.0.1:8080
RUNNER_SERVICE_TOKEN=<same-local-runner-token>
```

Production configuration intentionally requires HTTPS. Do not carry the local HTTP URL into Render.

## Verification checklist

1. On a trusted machine, verify Runner readiness at `/health/ready`.
2. With `X-Runner-Key`, verify `/v1/languages` and `/v1/database/engines`.
3. On the CodeLeaf backend, verify `GET /api/runner/status`. It must list only currently available Runner runtimes/engines, plus JDoodle-supported languages only when fallback is enabled and credentials are configured. The response must not contain either service token or the Runner URL.
4. With a test CodeLeaf learner account, submit a small supported code job, poll it to completion, and verify stdout, stderr, exit code, and ownership isolation.
5. Submit an allowed multi-file project (for example, a main source file plus a helper file), and verify the helper is available to the execution engine.
6. Submit SQLite, MySQL, and PostgreSQL test queries and verify results, row limits, and cancellation behavior.
7. Verify an unsupported Runner language routes to JDoodle only when the fallback toggle and credentials are enabled.
8. Verify an accepted Runner job is not re-submitted to JDoodle after a Runner submission error.
9. Keep the current JDoodle path available until these end-to-end checks succeed in the deployed environment.

Local unit tests and the Runner security preflight do not certify production isolation. Before public launch, run the Runner on a dedicated Linux host with the production Docker/cgroup settings, immutable image digests, private API ingress, network restrictions, and the full production security preflight. Do not use the Windows development Docker environment as the production execution host.

## Rollback

For a temporary full Runner rollback on the CodeLeaf backend, clear both `RUNNER_SERVICE_URL` and `RUNNER_SERVICE_TOKEN`, leave `RUNNER_JDOODLE_FALLBACK_ENABLED=true`, and retain the existing JDoodle credentials. Restart/redeploy the backend. `/api/runner/status` will then report the JDoodle capabilities that are configured. This does not delete Runner jobs already created on the Runner host.

For a selective rollback, set `RUNNER_JDOODLE_FALLBACK_ENABLED=false` to stop fallback submissions while leaving the Runner active. Do not remove JDoodle credentials until the new Runner integration has passed the production acceptance checks.
