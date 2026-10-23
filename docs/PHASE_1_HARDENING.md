# CodeLeaf Phase 1 — Foundation Hardening

This patch hardens the current starter before Phase 2 course-completion work.

## Included

- Production configuration now fails closed if `JWT_SECRET` is missing/placeholder/short, PostgreSQL is missing or local-only, `COOKIE_SECURE` is false, draft preview is enabled, or `FRONTEND_ORIGINS` is not a real HTTPS origin. Diagnostics never print secret values.
- Local Docker and `backend/.env.example` database settings now agree on `codeleaf` / `codeleaf` / `dev_only_password_change_me`.
- Alembic no longer silently uses a dummy `user:password` URL. Migrations require `DATABASE_URL` explicitly.
- Added `/api/ready`, which checks PostgreSQL connectivity and the minimum required schema; `/api/health` remains a liveness endpoint. Render uses `/api/ready` for readiness.
- Course-manifest validation checks course/module/lesson/exercise/project/assessment paths, safe relative paths, stable and unique slugs, diagram asset presence, dynamic diagram model shape, node IDs and edge references, and protected question/reference file paths.
- The bulk publish script runs that read-only graph validator before it changes any source statuses or imports a course.
- Lesson import now persists stable lesson IDs and updates an existing lesson row when its slug changes, avoiding duplicate rows/stale routes after a manifest correction.
- Regression tests cover the dynamic diagram JSON URL, non-public JSON blocking, readiness, production config, and lesson-slug migration.
- CI uses `npm ci`, validates the single Alembic head, validates all course manifests/diagram models, runs backend API contracts, and performs a publisher dry run.

## Local Phase 1 checks

Run from PowerShell in `E:\Code_Leaf\backend` with the existing virtual environment activated:

```powershell
python scripts/check_alembic_heads.py
python scripts/check_repository_hygiene.py
python scripts/validate_course_manifests.py
python scripts/test_phase1_config.py
python scripts/test_course_api_contract.py
python scripts/test_knowledge_check_api.py
python scripts/test_import_slug_rename.py
python scripts/publish_all_courses.py
```

The publisher command above is a dry run and must not change any course file or database row.

For deployment review, run:

```powershell
python scripts/check_release_readiness.py --production
python scripts/check_release_readiness.py --production --check-db --require-payments
```

This validates production settings present in environment variables / `backend/.env` without displaying their values and rejects the placeholder Vercel API hostname. It does not deploy remotely. Add `--check-db` when the configured database should be connected to, and `--require-payments` only when the Razorpay credentials and provider plan IDs for that environment have been configured.

## Database / migration note

The existing migration history has one head: `0002_dynamic_gamification`. The original `0001_initial_schema` migration creates tables from SQLAlchemy metadata. Do not rewrite an already-applied migration in a deployed database; keep future schema changes in new, explicit forward migrations and rehearse them against a staging database before production.

## Secret hygiene

`backend/.env` and `frontend/.env` must remain local and must not be committed or included in a shared ZIP. Only `.env.example` templates belong in source control. The project archive supplied for this audit included actual values in both `.env` files; this patch deliberately excludes both files and the Python virtual environment. If any value was real, rotate it in its provider/dashboard and update the local environment file. Removing the file from a later ZIP does not revoke an already shared credential.

## Not claimed by this patch

- No live Render/Vercel/Neon deployment or live Razorpay payment was performed.
- No local PostgreSQL migration was run against your machine.
- Historical production schema integrity, backups, restore, rate limiting, external error reporting, and a full external security review still require environment-specific verification.
