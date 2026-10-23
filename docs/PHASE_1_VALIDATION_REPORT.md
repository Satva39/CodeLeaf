# Phase 1 Validation Report

Generated during the CodeLeaf foundation-hardening patch build.

## Passed checks

- Python compilation: `python -m compileall -q app scripts alembic`
- Alembic graph: 2 migrations, one head (`0002_dynamic_gamification`)
- Production configuration tests: valid settings accepted; weak/placeholder JWT secret, missing/non-PostgreSQL database URL, insecure cookie, localhost origins, and draft preview are rejected
- API contract suite: draft privacy, authentication, readiness, SVG assets, dynamic diagram JSON assets, arbitrary JSON blocking, project privacy, 20 XP base awards, idempotency, 1.5x paid boost, and streak calculations
- Knowledge-check API suite: answer-key protection on GET, server-side grading, invalid option/ID rejection, and draft quiz hiding
- Stable lesson slug update: existing row is updated without creating a duplicate, and stable manifest ID is persisted
- Course manifests: 62 checked, 62 passed, 0 failed; 1,455 modules, 14,580 lessons, 3,778 exercises, 661 projects, 6,274 assessment files, 14,599 dynamic diagram models; 0 validator warnings
- Bulk publishing dry run: 62 discovered, 62 preflight-ready; no source files or database rows changed
- Release-readiness check in development mode: settings and migration graph passed; it correctly warns that the Vercel API rewrite still has a placeholder Render hostname

## Not verified from this environment

- `npm ci` did not finish because registry access timed out; therefore the Vite production build was not verified here.
- No migration or publishing write was executed against the user's PostgreSQL instance.
- No live Render, Vercel, Neon, or Razorpay transaction was performed.
- Git tracked-file hygiene cannot be fully verified against the user's local repository because this extracted source is not a Git checkout. The workflow will run the tracked-file check in GitHub Actions.

## Required before production deployment

1. Replace `https://your-codeleaf-api.onrender.com` in `frontend/vercel.json` with the real Render service URL.
2. Set `DATABASE_URL`, a unique random `JWT_SECRET`, `COOKIE_SECURE=true`, and the exact HTTPS `FRONTEND_ORIGINS` in Render. Keep draft previews off.
3. Run `python scripts/check_release_readiness.py --production --check-db` from `backend/` after deployment settings and database tables are configured.
4. Only run `python scripts/publish_all_courses.py --apply --publish` after reviewing the full dry-run output and backing up the database.
5. Treat `backend/.env` and `frontend/.env` as local-only. The supplied project archive included non-empty, non-placeholder-looking values in those files; if any were live credentials, rotate them. This patch ZIP excludes both files and all virtual environments.
