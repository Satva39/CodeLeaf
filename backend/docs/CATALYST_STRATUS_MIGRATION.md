# CodeLeaf portfolio archive storage: Neon PostgreSQL + Catalyst Stratus

## What this change does

- Keeps Neon PostgreSQL as the relational source of truth. Users, authentication, lessons, exercises, progress, XP, exams, certificates, payment records, subscriptions, entitlements, workspaces, snippets, runner records, support records, and project metadata stay in PostgreSQL.
- Adds Catalyst Stratus object storage for project ZIP archives only.
- Keeps the existing project upload-session API and its browser-side chunking. The browser still sends small chunks to the CodeLeaf API; the API finalizes the archive and uploads it to Stratus. No permanent Catalyst credentials or public object URLs are sent to the browser.
- Retains PostgreSQL fallback: Stratus writes are used only when `PORTFOLIO_STORAGE_PROVIDER=catalyst_stratus` and `CATALYST_STRATUS_ENABLED=true`. If credentials are incomplete or a Stratus upload fails, the application retains the Neon archive instead.
- Uses private object keys such as `projects/<submission-uuid>/archive.zip`. Existing owner-only and public-portfolio download rules remain enforced by CodeLeaf before streaming a file.

This is an object-storage migration, not a PostgreSQL-to-Catalyst-Data-Store replacement. Do not change `DATABASE_URL`, remove SQLAlchemy, remove psycopg, or remove Alembic.

## Current implementation boundary

The repository snapshot contained two PostgreSQL binary formats: `project_submissions.zip_bundle` and ordered rows in `project_submission_zip_chunks.payload`. The migration tool supports inline `BYTEA` and chunk rows. It stages one archive to a disk-backed temporary file and does not assemble the complete archive in Python RAM.

The SDK adapter configures the India data-centre endpoints before importing the SDK and applies a narrowly scoped URL-joining compatibility shim for SDK 1.5.0 requests that concatenate a base URL with a leading-slash path. It leaves requests that already have a service prefix or an absolute URL unchanged. The shim is installed once at runtime; no files in `site-packages` are edited.

The SDK adapter uses documented Stratus operations:

- `bucket.put_object(...)` for small objects.
- `initiate_multipart_upload`, `upload_part`, and `complete_multipart_upload` for objects at least 100 MiB.
- `TransferManager.get_iterable_object(...)` for streaming downloads.
- `bucket.get_object(key, {"range": "start-end"})` for range reads.
- `bucket.head_object`, `bucket.object(key).get_details()`, `bucket.list_paged_objects`, and `bucket.delete_object` for checks, metadata, listing, and deletion.

The current official Python SDK documentation does not document a multipart-abort method. A failed multipart upload therefore records the upload ID and object key for manual reconciliation; this code deliberately does not call an invented SDK method. `head_object(..., throw_err=False)` can return false for either a missing object or insufficient permission, so false is not treated as proof that the object is absent.

## 1. Catalyst Console setup

Do this in a non-production Catalyst project first.

1. Sign in to the [Catalyst Console](https://console.catalyst.zoho.in/) and open or create a dedicated CodeLeaf project.
2. In **Project Settings → General**, copy the **Project ID**.
3. Obtain the project **ZAID** from the Catalyst CloudScale authentication setup described in Zoho's third-party Python SDK integration guide. The SDK parameter is named `project_key`, but the value is the ZAID.
4. Open CloudScale **Stratus** and create a dedicated bucket, for example `codeleaf-project-archives-dev`. Use a private bucket. Do not enable public read access or configure public object URLs.
5. Open the [Zoho API Console](https://api-console.zoho.in/) and create a **Self Client** application.
6. Configure the OAuth permissions for the Stratus operations CodeLeaf needs, then generate a grant token and exchange it for a refresh token. Save the **Client ID**, **Client Secret**, and **Refresh Token** in a password manager. The refresh token is shown during the token-generation flow; do not put it in source control.
7. Zoho's operation pages specify **Admin** scope for object listing, object details, and deletion. Use the current Stratus SDK operation documentation and the scopes offered in your API Console to select the required scopes; do not guess a scope string from an unrelated example.
8. Record whether the project environment is `Development` or `Production` and the exact Catalyst API domain for the Catalyst data centre where the project is hosted. For the CodeLeaf India project configured here, use `https://api.catalyst.zoho.in`, `https://accounts.zoho.in`, and `.zohostratus.in`. Do not infer a project's data centre from a user's physical location.
9. Generate the Self Client grant/refresh token in the Zoho Accounts data centre that corresponds to the Catalyst project's data centre. A token generated in a different Accounts region can fail even when the Client ID and secret look correct. Use Zoho's [multi-data-centre documentation](https://docs.catalyst.zoho.com/en/cloud-scale/help/multi-dc/) to confirm the matching Catalyst API and Accounts domains.

Keep the development bucket separate from the production bucket. Do not run the migration or smoke test against real learner data while testing credentials.

## 2. Environment variables

Add these to `backend/.env` for local development, or to the Render backend service's environment-variable settings for deployment. Never add them to `frontend/.env`, JavaScript bundles, GitHub, issue comments, or logs.

| Variable | Where it comes from / purpose |
|---|---|
| `PORTFOLIO_STORAGE_PROVIDER` | `database` initially; switch to `catalyst_stratus` only after smoke testing. |
| `CATALYST_STRATUS_ENABLED` | `false` initially; set `true` to enable new Stratus uploads. |
| `CATALYST_PROJECT_ID` | Catalyst Console → Project Settings → General. |
| `CATALYST_PROJECT_ZAID` | ZAID from the CloudScale authentication setup. |
| `CATALYST_ENVIRONMENT` | `Development` or `Production`, matching the selected Catalyst project environment. |
| `CATALYST_CLIENT_ID` | Zoho API Console → Self Client credentials. |
| `CATALYST_CLIENT_SECRET` | Zoho API Console → Self Client credentials. |
| `CATALYST_REFRESH_TOKEN` | OAuth refresh token generated for the Self Client. |
| `CATALYST_STRATUS_BUCKET` | Exact name of the private Stratus bucket. |
| `CATALYST_PROJECT_DOMAIN` | Catalyst API domain for this India project: `https://api.catalyst.zoho.in`. |
| `CATALYST_ACCOUNTS_URL` | Matching OAuth Accounts data centre: `https://accounts.zoho.in`. |
| `CATALYST_STRATUS_RESOURCE_SUFFIX` | Matching India Stratus hostname suffix: `.zohostratus.in`. |
| `CATALYST_MULTIPART_PART_SIZE_MB` | Optional; default `25`, allowed `5`–`100`. |
| `CATALYST_MAX_RETRIES` | Optional; default `3`. |
| `CATALYST_VERIFY_UPLOAD_CHECKSUM` | Keep `true` so upload verification streams the remote object and compares SHA-256. |

A safe initial configuration is:

```dotenv
PORTFOLIO_STORAGE_PROVIDER=database
CATALYST_STRATUS_ENABLED=false
CATALYST_PROJECT_ID=
CATALYST_PROJECT_ZAID=
CATALYST_ENVIRONMENT=Development
CATALYST_CLIENT_ID=
CATALYST_CLIENT_SECRET=
CATALYST_REFRESH_TOKEN=
CATALYST_STRATUS_BUCKET=codeleaf-project-archives-dev
CATALYST_PROJECT_DOMAIN=https://api.catalyst.zoho.in
CATALYST_ACCOUNTS_URL=https://accounts.zoho.in
CATALYST_STRATUS_RESOURCE_SUFFIX=.zohostratus.in
CATALYST_MULTIPART_PART_SIZE_MB=25
CATALYST_MAX_RETRIES=3
CATALYST_VERIFY_UPLOAD_CHECKSUM=true
```

Do not replace the existing `DATABASE_URL`. Catalyst Stratus credentials are backend-only.

## 3. Local Windows setup

From PowerShell:

```powershell
cd E:\Code_Leaf\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env`, then fill in your local PostgreSQL `DATABASE_URL` and the Catalyst development values. Do not send or commit the resulting `.env` file.

Apply the additive schema migration:

```powershell
alembic upgrade head
alembic heads
```

The expected single Alembic head is `0010_catalyst_stratus`. If the project reports multiple heads, stop and reconcile migration history before proceeding.

## 4. Audit existing Neon storage (read-only)

Run from `backend/` against the exact database you intend to audit:

```powershell
python scripts\audit_neon_storage.py
python scripts\audit_neon_storage.py --json | Out-File -Encoding utf8 neon-storage-audit.json
```

The audit uses read-only PostgreSQL statements and reports database size, table and index sizes, all reflected `LargeBinary` columns, the number/bytes of inline ZIPs and chunk payloads, and the 20 largest legacy archives. The audit is not part of application startup and never changes records.

## 5. Test Catalyst connectivity (test bucket only)

Before enabling Stratus uploads, set the Catalyst values for the development project and run:

```powershell
python scripts\catalyst_stratus_smoke_test.py
```

This creates one uniquely named temporary text object under `smoke-tests/`, checks existence, metadata size, range download, and streamed SHA-256, then attempts to delete that exact test object. It does not read or modify learner records. If cleanup reports a warning, remove only the exact temporary key printed by the script in the Catalyst Console.

The automated adapter test is mocked and does not prove real Catalyst connectivity:

```powershell
python scripts\test_catalyst_stratus_adapter.py
```

Do not proceed to production until the real smoke test passes with a development bucket.

## 6. Migration commands

All commands below run from `backend/` and use the database configured in `DATABASE_URL`.

**Dry run (default, no writes):**

```powershell
python scripts\migrate_portfolio_archives_to_stratus.py --dry-run
```

**Transfer archives (keeps all original Neon payloads):**

```powershell
python scripts\migrate_portfolio_archives_to_stratus.py --execute --batch-size 10
```

The operation is resumable: rows already marked `storage_provider='catalyst_stratus'` and `object_status='verified'` are not uploaded again. Failed transfers leave Neon bytes intact. When a multipart upload fails, the upload ID and object key are recorded in `portfolio_metadata` for manual reconciliation.

**Verify object existence, size, and SHA-256 before cleanup:**

```powershell
python scripts\migrate_portfolio_archives_to_stratus.py --verify
```

**Remove legacy Neon ZIP bytes only after reviewing the report and taking a Neon backup:**

```powershell
python scripts\migrate_portfolio_archives_to_stratus.py --cleanup --confirm-cleanup
```

Cleanup re-checks the remote object and its checksum immediately before clearing `zip_bundle` and deleting `project_submission_zip_chunks`. It retains the PostgreSQL submission row and Stratus object reference. Do not run cleanup based only on the transfer summary; run `--verify` first and review the result.

## 7. Orphan-object and incomplete multipart report

Read-only report:

```powershell
python scripts\cleanup_stratus_orphaned_objects.py
```

This compares the Stratus `projects/` listing with active PostgreSQL object references. It lists only canonical `projects/<uuid>/archive.zip` keys. The default report never deletes anything.

To remove orphaned objects older than at least 30 days, review the report first and explicitly run:

```powershell
python scripts\cleanup_stratus_orphaned_objects.py --delete-orphans --confirm-delete --older-than-days 45
```

Objects without a parseable `last_modified` value are never automatically deleted. Catalyst's list response documents a human-readable timestamp without a timezone; the 45-day default is a grace period, not a substitute for reviewing the candidate list. Do not lower the threshold below 30 days.

Known incomplete multipart uploads are printed with their recorded object key and upload ID. The current documented Python SDK does not include multipart abort, so inspect and clear these exact pending uploads using the Catalyst Console or Zoho support. Never delete a completed referenced object to try to clean up a multipart session.

## 8. Enable new Stratus uploads and deploy to Render

Only after the schema migration and development smoke test succeed:

1. In Render, open the CodeLeaf backend web service → **Environment**.
2. Add the `CATALYST_*` variables listed above using the production project, production bucket, and production OAuth credentials. For the India data centre, also set `CATALYST_PROJECT_DOMAIN=https://api.catalyst.zoho.in`, `CATALYST_ACCOUNTS_URL=https://accounts.zoho.in`, and `CATALYST_STRATUS_RESOURCE_SUFFIX=.zohostratus.in`.
3. Set `PORTFOLIO_STORAGE_PROVIDER=catalyst_stratus` and `CATALYST_STRATUS_ENABLED=true` when you are ready for new archives to use Stratus.
4. Keep `DATABASE_URL` pointing at Neon PostgreSQL.
5. Deploy the backend normally through your existing release process. This patch does not deploy anything itself.
6. Test a small private project upload, owner download, public share/download, and delete using test accounts before switching real users over.
7. Keep an eye on application logs for Stratus upload/download failures and the `object_status` values in the portfolio table.

The existing browser upload-session uses small client chunks, avoiding one huge browser-to-Render request for the 500 MiB application limit. The Stratus upload is performed server-side. Render's current request-body and timeout limits were not independently validated in this code change; do not increase or remove the existing upload cap without checking your Render service plan and testing a full-size file in staging.

## 9. Rollback

### Before Neon cleanup

The original inline or chunked Neon payloads are retained. Run:

```powershell
python scripts\migrate_portfolio_archives_to_stratus.py --restore-neon --confirm-restore
```

For each verified Stratus-backed row that still has Neon data, this switches the authoritative storage provider back to Neon without deleting the Stratus copy.

### After Neon cleanup

The same command downloads each verified object to a disk-backed temporary file, verifies its size and SHA-256, rebuilds ordered Neon chunks, and switches the storage provider back to Neon. It does not delete Stratus objects. Confirm Neon has enough available storage before restoring large archives.

Then set the Render/local configuration to:

```dotenv
PORTFOLIO_STORAGE_PROVIDER=database
CATALYST_STRATUS_ENABLED=false
```

Keep the Stratus bucket and object references until the rollback has been fully tested. The retained Stratus backup can be cleaned later using the orphan-object procedure, after the grace period.

If Catalyst is unavailable during rollback, do not delete the Stratus bucket or references. Restore access to Catalyst first or recover from a separate verified backup.

## 10. Security, file handling, and operational notes

- The backend generates all object keys; client-supplied keys are not accepted.
- The bucket must remain private. Backend authentication and CodeLeaf's owner/public sharing checks authorize downloads.
- Object downloads stream through the backend. The adapter also supports SDK range reads.
- Upload size remains capped by existing CodeLeaf validation at 500 MiB. Existing ZIP structure/path validation continues to run before the archive is marked complete.
- Stratus multipart uploads buffer at most one configured part in memory (default 25 MiB), not the complete archive. The 100 MiB multipart threshold follows the current SDK guidance.
- Project deletion and account deletion mark external deletion intent before removing relational metadata. A failed Stratus delete keeps the PostgreSQL reference so an operator can retry.
- If bucket versioning is enabled, the documented `delete_object(key)` operation without a version ID can delete all versions. Confirm your versioning policy before enabling deletion workflows.
- The checksum is verified by reading the remote object and calculating SHA-256. Stratus ETag is not treated as SHA-256.
- Catalyst student usage is not unlimited. Usage allowances, eligibility, and any restrictions can change. The current student offer is tied to eligible non-commercial student projects; CodeLeaf includes monetization/subscription functionality, so confirm in your Catalyst account/with Zoho whether your intended use qualifies before relying on a student offer. Check the live Catalyst pricing and usage page for current quotas, request limits, and charges.
- No production Neon connection, real Catalyst credentials, learner archive, or Render deployment was used for this patch. The real Neon audit, smoke test, migration, and cleanup must be run by you in the intended environment.

## 11. Useful official references

- [Catalyst Stratus overview](https://docs.catalyst.zoho.com/en/cloud-scale/help/stratus/introduction/)
- [Catalyst Python SDK: third-party application integration](https://docs.catalyst.zoho.com/en/sdk/python/v1/integrate-sdk-in-third-party-apps/)
- [Catalyst Python SDK: upload objects](https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/stratus/upload-object/)
- [Catalyst Python SDK: download objects](https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/stratus/download-object/)
- [Catalyst Python SDK: list objects](https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/stratus/list-objects/)
- [Catalyst Python SDK: object details](https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/stratus/object-details/)
- [Catalyst Python SDK: delete objects](https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/stratus/delete-objects/)
- [Catalyst student developer offer](https://catalyst.zoho.com/students/)
- [Catalyst pricing and usage](https://www.zoho.com/catalyst/pricing.html)
- [Catalyst multi-data-centre configuration](https://docs.catalyst.zoho.com/en/cloud-scale/help/multi-dc/)

---

## Important completion gate

Do not declare migration complete until the live Neon audit is reviewed, the real Catalyst development smoke test succeeds, test-account upload/download/share/delete flows pass, all intended archives verify, and the explicit cleanup step has been separately approved and completed. This repository patch only prepares the application and scripts; it does not perform that live migration.
