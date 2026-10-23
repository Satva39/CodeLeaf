# AI Course Validation Report

Date: 2026-10-15  
Course slug: `ai`  
Status: **draft — not approved for publication**

## Generated content inventory

- 18 modules and 158 individual lesson JSON files, preserving the source PDF's 158 numbered lesson titles and all 1,039 listed subtopics.
- 24 exercises with 24 separate protected solution/review files.
- 10 projects (including the capstone) with 10 separate protected reference outlines.
- 158 protected per-lesson knowledge-check files containing 474 multiple-choice questions.
- 1 final exam blueprint; it is a blueprint, not a live exam engine or certificate-issuance claim.
- 18 original SVG module overview diagrams, each 1200 × 760 (30:19).
- 407 JSON files in the course content tree. All course content and solutions are marked draft.

## Results

| Check | Status | Evidence |
|---|---|---|
| PDF syllabus coverage | PASS | The extracted and reviewed Section B has 18 modules, 158 lessons, and 1,039 subtopics; generated lesson titles and subtopic counts match it. Sections A and C–G were also reviewed for course overview, exercises, projects, optional tracks, learning path, and quality checks. |
| CodeLeaf course-tree validator | PASS | `python scripts/validate_course_content.py --course-slug ai` returned 18 modules, 158 lessons, 24 exercises, 10 projects, 474 protected questions, 18 visuals, 407 JSON files, and “All referenced course files, IDs, relationships, graders, asset paths, and SVG XML passed validation.” |
| CodeLeaf import dry run | PASS | `python scripts/import_course_files.py --course-slug ai` validated the relational import tree and extended content checks; it explicitly reported `DRY RUN ONLY` and made no database changes. |
| Python teaching examples | PASS | All 158 generated Python snippets executed in fresh namespaces; actual stdout matched the stored expected output for every lesson. The snippets are deterministic learning examples, not trained models. |
| Question sets and answer keys | PASS | 158 sets × 3 questions; each answer key matches one listed option and each question set is draft/protected. |
| IDs, links, and protected files | PASS | Unique IDs, file references, exercise-to-lesson relationships, project solution references, and required status/visibility fields passed the course validator. |
| XP overrides in content | PASS | Automated scan found no `xp_reward`, `xp_points`, `xp_override`, `lesson_xp`, or `exercise_xp` keys in the course JSON. The platform's existing backend remains the owner of XP. |
| SVG asset validation | PASS | All 18 manifest entries exist; SVG files parse as XML. Module 11's rendered visual was visually inspected for readable labels and layout. |
| Python compilation | PASS | `py_compile` completed for the existing backend app and test scripts used during validation. |
| Protected knowledge-check API test | PASS | `python scripts/test_knowledge_check_api.py` passed all assertions for key withholding, server-side grading, invalid answers, and draft visibility using its temporary SQLite database. |
| CodeLeaf API contract test | PASS | `python scripts/test_course_api_contract.py` passed its contract, authorization, draft privacy, XP idempotency, and streak assertions using temporary SQLite. Its expected HTML test asset/metadata were supplied as temporary test fixtures only; those fixtures are not in the patch. |
| Frontend production build | NOT RUN SUCCESSFULLY | `npm run build` was attempted, but stopped with `vite: not found` because `frontend/node_modules` is absent in the inspected workspace. This patch adds no frontend code or dependencies. Run `npm install` then `npm run build` locally to verify the project build. |
| Database apply / migration | NOT RUN | No `--apply`, `--publish`, migration, or live-database command was executed. No live PostgreSQL database credentials were used. |
| Vercel / Render deployment | NOT RUN | This is a content-only patch. No production deployment or live service was tested. |

## Review and release notes

- All generated course and assessment content remains draft. Subject-matter review is required before publishing, especially for technical depth, the answer wording, lesson examples, and the simple keyword-based exercise graders.
- The source PDF's abbreviated citation callouts were replaced with direct official-resource links in `references/reference-index.json`; the review note documents this editorial choice.
- The code examples use Python's standard library and `static-validation` mode. They do not run in a browser, connect to a live model provider, or require API keys.
- The existing CodeLeaf backend is responsible for persisted XP, idempotency, access control, and answer-key withholding. No XP behavior or platform code was changed by this patch.
- No schema migration, dependency, environment variable, `render.yaml`, Vercel config, Docker config, or frontend change is included.
