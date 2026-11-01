# CodeLeaf Full Storage Upgrade — Lessons + Portfolio ZIPs

This package adds course-level compressed lesson bundles in Zoho Catalyst Stratus and coordinates their copy with the existing project-ZIP migration. It is an application patch and migration toolkit; it does **not** contact Neon or upload/delete data during installation.

## What it changes

- Adds `course_content_bundles` metadata and Alembic revision `0011_course_content_bundles`.
- Adds deterministic gzip lesson bundles, one immutable bundle per course, with SHA-256 verification and a bounded in-process cache.
- Updates lesson-detail and knowledge-check reads to hydrate full lesson JSON from Stratus when a verified bundle exists; retained Neon lesson JSON is used as fallback before any cleanup.
- Updates the course importer so future course imports can publish a verified full-course bundle when `LESSON_CONTENT_STORAGE_PROVIDER=catalyst_stratus` is explicitly enabled.
- Adds read-only, copy, verify, cleanup, and restore commands for lesson bundles.
- Adds a coordinated runner that also invokes the existing project ZIP migration commands.
- Keeps exercises, lesson metadata, all relational records, and portfolio metadata in Neon.

## Important: staged rollout only

After installing and deploying the patch, keep these settings unchanged:

```env
PORTFOLIO_STORAGE_PROVIDER=database
CATALYST_STRATUS_ENABLED=false
LESSON_CONTENT_STORAGE_PROVIDER=database
```

This package does not activate Catalyst writes. First apply the additive Alembic migration and run dry-runs. Then review the Catalyst plan, commercial-use eligibility, current usage/charges, and a recent restorable Neon backup with a parent/guardian where applicable. Only then should the explicit copy operation be considered.

## Install

1. Extract this ZIP outside the CodeLeaf repository, for example to `E:\Downloads\CodeLeaf_Catalyst_Full_Storage`.
2. Open PowerShell in the extracted package folder.
3. If Windows blocks the downloaded script, unblock only this script:

   ```powershell
   Unblock-File .\Install-CodeLeaf-Catalyst-Full-Storage.ps1
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
   ```

4. Run:

   ```powershell
   .\Install-CodeLeaf-Catalyst-Full-Storage.ps1 -ProjectRoot "E:\Code_Leaf"
   ```

   Alternatively, run the Python installer directly:

   ```powershell
   python .\install_course_content_patch.py --project-root "E:\Code_Leaf"
   ```

The installer preflights all source anchors before writing, makes timestamped backups under `.codeleaf-catalyst-course-storage-backups`, and rolls back patched files if an edit fails. If it reports source-anchor mismatch, stop and inspect; do not force the patch.

## Validate and deploy application code

From `E:\Code_Leaf`:

```powershell
python -m py_compile backend\app\config.py backend\app\models.py backend\app\main.py backend\app\storage\course_content.py backend\scripts\import_course_files.py backend\scripts\migrate_lesson_content_to_stratus.py backend\scripts\run_catalyst_full_storage_migration.py
python backend\scripts\test_course_content_bundle.py
python backend\scripts\test_catalyst_stratus_adapter.py
python backend\scripts\test_migration_repeatability.py
python backend\scripts\test_portfolio_zip_upload.py
```

Review `git diff`, ensure `.env` is not staged, then commit/push the source changes and deploy the backend. Take a Neon branch snapshot or export and ensure it is restorable before any migration writes. After the code is deployed, apply the additive schema migration to the intended Neon DB:

```powershell
cd E:\Code_Leaf\backend
python -m alembic upgrade head
```

## Read-only dry-run

Run from `E:\Code_Leaf\backend` with the verified Production Catalyst credentials in `backend/.env` and Neon `DATABASE_URL`:

```powershell
python scripts\run_catalyst_full_storage_migration.py --dry-run
```

The runner checks the target production project/bucket, current database, schema revision, local regression tests, lesson inventory and project ZIP dry-run. It does not upload or delete objects in dry-run mode.

## Copy and verify

Course-level bundles are used to keep the object count low (one object per course, not one object per lesson or module). The real course count and compressed size are calculated from the connected database during dry-run; don't assume the older source snapshot's count.

Before copying, confirm the appropriate Catalyst commercial-use terms, potential charges and current storage/request quota. The student offer may have non-commercial restrictions; CodeLeaf has subscriptions/advertising, so eligibility must not be assumed. Also ensure a recent restorable Neon snapshot/export exists.

Only after those checks:

```powershell
python scripts\run_catalyst_full_storage_migration.py --execute --billing-reviewed --backup-ready
```

The runner repeats dry-runs immediately before transfer, then requires the exact phrase `MIGRATE ALL CONTENT`. It copies lesson bundles and project ZIPs, verifies them, and retains all Neon source payloads. It leaves both storage providers unchanged.

## Application validation / future writes

After copy and verification, deploy the backend and test lessons, knowledge checks, outlines, premium access and portfolio upload/download/delete using test accounts. Then configure new lesson imports to publish bundles by setting:

```env
LESSON_CONTENT_STORAGE_PROVIDER=catalyst_stratus
```

After independently validating portfolio API behaviour, future ZIP uploads can be routed to Catalyst by setting:

```env
PORTFOLIO_STORAGE_PROVIDER=catalyst_stratus
CATALYST_STRATUS_ENABLED=true
```

These are separate cutovers. Do not enable both just because the copy operation passed; use app-level tests and a staged rollout.

## Optional Neon cleanup — separate, destructive, not part of the one-go runner

Only when all application workflows pass, backups are restorable, and every relevant object verifies:

```powershell
python scripts\migrate_lesson_content_to_stratus.py --cleanup --confirm-cleanup --backup-ready
python scripts\migrate_portfolio_archives_to_stratus.py --verify
python scripts\migrate_portfolio_archives_to_stratus.py --cleanup --confirm-cleanup
```

Lesson cleanup removes full lesson-body JSON from Neon but keeps metadata and bundle pointers. ZIP cleanup removes the legacy ZIP payload/chunks. Neither cleanup should be performed until rollback has been rehearsed and the deployed app successfully reads the Catalyst objects.

## Rollback

The lesson tool supports restoring full lesson bodies from Catalyst while retaining Stratus objects:

```powershell
python scripts\migrate_lesson_content_to_stratus.py --restore-neon --confirm-restore
```

The existing ZIP migration tool supports the equivalent restore mode:

```powershell
python scripts\migrate_portfolio_archives_to_stratus.py --restore-neon --confirm-restore
```

Switch `LESSON_CONTENT_STORAGE_PROVIDER=database`, `PORTFOLIO_STORAGE_PROVIDER=database`, and `CATALYST_STRATUS_ENABLED=false` before redeploying rollback configuration.

## Scope / limitations

- Exercises remain in Neon; their inspected payload is comparatively small (~5.3 MB).
- This package does not migrate users, course/module/lesson metadata, progress, exams, subscriptions, billing, or payment records.
- The coordinated runner copies lesson bundles and portfolio ZIPs but does not clean Neon or switch active storage providers.
- Live transfer was not performed by building this package. The user must run the dry-run and separately authorize the copy from their secured local environment.
