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
usage endpoint before advertising Python or JavaScript as available. These checks
do not run learner code. Compiler identifiers are `python-3.14` and `nodejs-24`.

## Provider routing

- Python and JavaScript use OnlineCompiler when its live checks succeed.
- Other installed languages and database execution continue to use CodeLeaf Runner.
- Existing JDoodle fallback remains enabled only for its existing supported languages
  when neither preferred runtime provider can handle that language.
- A request is not automatically re-executed on another provider after an
  OnlineCompiler timeout or transport failure. This avoids duplicate executions
  when the provider may already have started the submitted code.
- HTML, CSS, browser JavaScript, and React previews remain in the existing browser
  preview environment; they are not sent to OnlineCompiler as server programs.

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
