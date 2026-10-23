# PostgreSQL course status

**Status: draft — not publication-ready.**

## Generated content counts

- Modules: 24 (all modules from Section B)
- Lessons: 220 (numbered continuously 1–220; each has one JSON file)
- Exercises: 26 (all briefs from Section C; each has a separate solution outline)
- Projects: 10 (all briefs from Section D; capstone included)
- Assessments: 1 final exam blueprint, plus 220 separate knowledge-check sets / 660 questions
- Visual assets: 39 original SVG diagrams (24 module overviews, roadmap, and focused concept diagrams)

## Validation state

- Source curriculum: all 51 pages rendered and reviewed; extracted topic count verified as 24 modules and 220 consecutive lesson IDs.
- Content files: generated with stable IDs/slugs, sequence links, previous/next references, prerequisites, separate answers, and draft status.
- Static validation: run with `python scripts/validate_course_content.py --course-slug postgresql` and dry-run import.
- Not run by generation: database import/write, PostgreSQL query execution, frontend build, live API calls, deployment, restore drill, replication drill, or production readiness/security review.

## Required review before publication

1. Execute and review code examples against PostgreSQL 18.6 in a disposable test database; some snippets intentionally show schema- or privilege-dependent DDL.
2. Review the supported static exercise grader; `contains_all` checks requested text tokens and does not execute SQL.
3. Review all 660 knowledge-check questions for pedagogical quality and ambiguity; answers remain in repository question files and the existing API is expected to omit them from GET responses.
4. Review all solution outlines and project starter briefs; these are guidance, not fully implemented reference applications.
5. Recheck official docs/version behavior before changing any content status from draft.

## Integration notes

- Uses existing backend/content/courses layout and current importer (`scripts/import_course_files.py`).
- Uses existing schema and server-side 20 base XP rules; no migrations, API routes, frontend files, dependency manifests, hosting configuration or XP overrides were added.
- SQL, shell and Python samples are not executed in the browser. CodeLeaf currently previews HTML/CSS/JavaScript only; Python examples require a separate isolated runner.
