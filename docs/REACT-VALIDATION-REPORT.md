# React course patch — validation report

## Deliverable scope

- Target: React only, slug `react`.
- Status: **draft / not ready to publish until human review**.
- PDF reviewed: `React.pdf`, all 67 pages. Section B lesson titles/subtopics were extracted; Sections C–G informed exercises, projects, advanced scope, roadmap, and quality checklist.
- The course content lives in separate files under `backend/content/courses/react/` and follows the repository's file-based importer contract.

## Content counts

| Item | Count |
|---|---:|
| Modules | 29 |
| Numbered lessons | 333 |
| Exercises | 30 |
| Project briefs | 10 |
| Lesson knowledge-check sets | 333 |
| Knowledge-check questions | 999 |
| Final exam questions | 60 |
| Total assessment questions | 1,059 |
| Assessment blueprints | 1 |
| Original SVG visuals | 362 (29 module overview + 333 lesson-level) |
| Course JSON files, as reported by validator | 780 |

## Checks actually run

- **PASS** — `python scripts/validate_course_content.py --course-slug react`: validates file paths, JSON, IDs/relationships, grader structures, asset references, SVG XML, and required fields; reports 29 modules, 333 lessons, 30 exercises, 10 projects, 1,059 questions, 362 visuals, and draft status.
- **PASS** — `python scripts/import_course_files.py --course-slug react`: importer dry run validated 29 modules, 333 lessons, 30 exercises, 10 projects, 1,059 protected question items, and 362 assets. Output confirmed **no database changes made**.
- **PASS** — `python -m py_compile app/main.py scripts/validate_course_content.py scripts/import_course_files.py scripts/test_course_api_contract.py scripts/test_knowledge_check_api.py`.
- **PASS** — `python scripts/test_course_api_contract.py`: draft visibility, local-preview guard, answer-key privacy, authentication, published metadata shape, protected solution filtering, XP base/boost, no reward for incorrect exercise answer, idempotent duplicate protection, transaction uniqueness, and streak gap behavior.
- **PASS** — `python scripts/test_knowledge_check_api.py`: hidden answers on GET, correct server-side grading, feedback only after submission, invalid answer/question rejection, and draft hiding.
- **PASS** — `node --check frontend/src/data.js`.
- **PASS** — generator-side audit: 29 modules, 333 lesson titles, all 30 exercise tasks and 10 projects written, 333 lesson question sets, 999 lesson questions, 60 final exam questions, and 362 referenced assets present.
- **PASS** — all referenced lesson and module SVG files were checked to exist and XML validation passed through the course validator.

## Blocked or not run

- **BLOCKED / NOT RUN** — frontend `npm ci --ignore-scripts --no-audit --no-fund` could not complete because requests to `registry.npmjs.org` repeatedly failed with `EAI_AGAIN` (DNS/network resolution). The production `npm run build` did not run because dependencies could not be installed. Re-run from `frontend/` when network/package registry access works:

  `npm ci --ignore-scripts --no-audit --no-fund`

  `npm run build`

- **NOT RUN** — database `--apply`: no database write was attempted, to avoid unintended changes to configured data. A user-controlled development database is needed.
- **NOT RUN** — production deployment, live database migration, real authentication session, browser-level visual regression, and actual interactive code execution of the snippets.

## Compatibility and technical notes

- The PDF's React 19.3 baseline and Sep 9, 2026 release date match the official React release notes: https://react.dev/blog/2026/09/09/react-19-3
- The PDF's Create React App legacy guidance matches the official deprecation note: https://react.dev/blog/2025/02/14/sunsetting-create-react-app
- Existing CodeLeaf manifests use React and React DOM 18.3.1. No package or lockfile was changed. React 19.3-only samples (including Fragment Refs and View Transitions) need a separate version-compatible runtime and remain draft pending review.
- Server Components/Functions are explicitly described as framework/runtime-dependent, not a universal client-only Vite feature.
- No database schema migration, secrets, `.env`, `.venv`, `node_modules`, credentials, DB dumps, or build artifacts are included.
- No arbitrary code runner was added. Exercises use existing bounded static pattern checking and state that meaningful behavior should be human-reviewed. No XP override was added; platform reward rules remain server-authoritative.

## Deployment/configuration impact

- No required environment variable or deployment configuration change for the content patch itself.
- Database import requires the existing configured `DATABASE_URL` and backend dependencies.
- Local draft previews may be enabled only in development using `APP_ENV=development` and `PREVIEW_DRAFT_COURSES=true`; never enable this in production.
- The frontend production build remains unverified due to the package-registry DNS blocker documented above.
