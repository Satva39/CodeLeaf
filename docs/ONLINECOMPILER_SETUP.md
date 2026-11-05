# OnlineCompiler setup and routing

CodeLeaf talks to OnlineCompiler from the FastAPI backend only. The browser calls
CodeLeaf's authenticated `/api/runner/jobs` gateway; it never receives the provider
API key or calls `api.onlinecompiler.io` directly.

## Render backend environment

Set these on the **CodeLeaf API service** in Render:

```env
ONLINECOMPILER_ENABLED=true
ONLINECOMPILER_API_KEY=YOUR_NEW_PRIVATE_API_KEY
ONLINECOMPILER_BASE_URL=https://api.onlinecompiler.io
ONLINECOMPILER_TIMEOUT_SECONDS=65
```

Use a newly created key after revoking any key that has been exposed in screenshots,
chat messages, logs, or source files. Do not add the key to Vercel, `frontend/.env`,
Git, ZIP archives, or client-side code. Keep the existing CodeLeaf Runner and
JDoodle settings unchanged:

```env
RUNNER_SERVICE_URL=
RUNNER_SERVICE_TOKEN=
RUNNER_JDOODLE_FALLBACK_ENABLED=true
```

The OnlineCompiler setting defaults to disabled until explicitly enabled. The
backend checks the provider compiler registry, service health, and authenticated
usage endpoint before advertising compatible CodeLeaf runtimes as available. These
checks do not run learner code. The mapping covers every compiler currently listed in the provider catalogue,
including C, C++, Java, C#, Go, Rust, PHP, Ruby, TypeScript, R, Swift, Dart,
Kotlin, Bash, PowerShell, SQL/SQLite, and the other documented runtimes. The
exact language-key-to-compiler mapping is maintained in
`backend/app/onlinecompiler_client.py`; aliases and special variants such as
Pandas 2 and C++20 are preserved through provider selection.

## Provider routing

- Every mapped CodeLeaf language uses OnlineCompiler when the key is configured,
  the service/usage checks succeed, and the provider's live registry contains the
  mapped compiler ID.
- Languages without a compatible OnlineCompiler runtime keep their existing
  CodeLeaf Runner or JDoodle path. In particular, MySQL, PostgreSQL, MongoDB, Redis,
  Django/Flask/FastAPI/Express apps, Vue/React framework builds, and framework-specific runtimes are not falsely mapped
  to a generic compiler.
- Generic SQL and SQLite workspaces use OnlineCompiler's SQLite 3 runtime;
  DuckDB has its own `duckdb-1.5` runtime key. MySQL and PostgreSQL remain dedicated
  database-engine workflows on CodeLeaf Runner or their existing fallback.
- Existing JDoodle fallback remains available for languages/providers that OnlineCompiler
  does not support. OnlineCompiler errors are not automatically replayed through JDoodle.
- A request is not automatically re-executed on another provider after an
  OnlineCompiler timeout or transport failure. This avoids duplicate executions
  when the provider may already have started the submitted code.
- HTML, CSS, browser JavaScript, and React previews remain in the existing browser
  preview environment; they are not sent to OnlineCompiler as server programs.
- Framework lesson keys such as Django, Flask, FastAPI, Express, Vue, React, and
  PyTorch are not treated as plain Python/JavaScript because their packages or
  framework runtimes are not included in the provider images. They retain the
  configured Runner/JDoodle path where available.

## OnlineCompiler limits and Coding Battles

The battle judge sends all private cases in one synchronous `/api/run-tests/`
request. Private test cases are marked `hidden: true`; CodeLeaf stores and returns
only the safe verdict summary. An `incomplete`, `skipped`, or `internal_error`
evaluation cannot produce a win or award XP. CodeLeaf reserves one daily execution
unit per test because OnlineCompiler counts each test as one run. The integration
caps each batch at 8 tests, which is the documented Free-plan maximum. Check the
OnlineCompiler dashboard and its `/api/usage/` endpoint for current account usage;
provider limits and availability can change.

## Local development

Put the same variables in `backend/.env` only. Do not commit that file. Restart the
FastAPI process after changing environment variables. Without a key, the rest of
CodeLeaf continues using its existing configured providers and browser previews.

No deployment, Git commit, or production database change is performed by this update.
