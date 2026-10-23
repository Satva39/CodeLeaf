# CodeLeaf dynamic progress and course content

## XP policy

The backend in `backend/app/main.py` is the authority for verified account rewards:

- Completing a published lesson for the first time awards 20 base XP.
- Correctly completing a published exercise for the first time awards 20 base XP.
- A Max or Full Access entitlement applies a 1.5x server-side multiplier (30 XP per eligible activity).
- XP transactions have a uniqueness constraint on `(user_id, source_type, source_id)`, so retries and repeat visits do not farm duplicate XP.
- Exercise answers are graded by the server using each exercise's private `grading_config`; the browser never sends a trusted `correct` flag.

`GET /api/public/config` exposes only public reward display settings. Authenticated totals and effective rewards come from `GET /api/me/stats`. The `UserActivityDay` table records one date per user in their selected timezone. Current and longest streaks are derived from those dates; they are not initialized with a fake number.

For signed-out preview, the browser calculates guest metrics from actions actually recorded in localStorage. These values are preview-only and are not included in the authoritative database leaderboard. The base 20-XP fallback is for preview display only; a plan boost is never applied in the browser.

## Course file layout

Every technology is independent under `backend/content/courses/<slug>/`. `course.json` points to module files, module files list lesson paths, lesson files list exercise paths, and projects/exams/references each have their own documents. `docs/MASTER_COURSE_PROMPT.md` mandates this pattern for all 61 requested tracks and future courses.

Example HTML content currently includes one draft module, one draft lesson, one draft exercise, a project brief, and an exam blueprint. Run a dry run before import:

```powershell
cd backend
python scripts/import_course_files.py --course-slug html
```

Only after review should a maintainer write draft records with `--apply`; publish reviewed content with `--apply --publish`. Don't publish the starter sample just because the importer accepts it.

## Database rollout

The new SQLAlchemy models are covered by Alembic revision `0002_dynamic_gamification`. Render's configured start command already applies `alembic upgrade head`. For a local database, follow the existing backend setup and apply migrations intentionally after backing up any data you care about.
