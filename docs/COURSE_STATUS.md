# NumPy course status

**Course slug:** `numpy`  
**Status:** Draft — not approved for publication  
**Reference check date:** 2026-10-13  
**Source:** the attached 46-page NumPy curriculum PDF plus the current CodeLeaf project ZIP.

## Generated content inventory

| Item | Count | Status |
|---|---:|---|
| Modules | 22 | Draft |
| Ordered lesson pages | 220 | Draft |
| Lesson knowledge-check sets | 220 | Draft |
| Knowledge-check questions | 660 | Draft; answer keys live in course JSON and must remain server-side |
| Exercises mapped from PDF Section C | 40 | Draft |
| Protected exercise-solution files | 40 | Repository-only |
| Projects mapped from PDF Section D | 10 | Draft |
| Final assessment blueprints | 1 | Draft |
| SVG visuals | 242 | Included; see `assets/ASSET-CHECKLIST.md` |

## What is ready

- Course and module metadata; separate file per lesson, exercise, project, and knowledge-check set.
- PDF syllabus numbers and subtopic mappings preserved in `references/full-syllabus.json`.
- Original SVG overview/lesson diagrams, including labeled synthetic teaching charts.
- Official documentation index and explicit technical review notes.
- Lesson/example content marks Python snippets as local/static-validation, not as server-executable.

## Publication blockers / limitations

- Every content item intentionally remains `draft`. Review the technical accuracy, writing, exercise grading, visual rendering, and accessibility before publication.
- The supplied curriculum PDF is an outline, not fully authored textbook content; generated lesson prose and assessments are original expansions and need subject-matter review.
- The test environment available during generation had NumPy 2.3.5, not NumPy 2.5. Re-run code examples in the version baseline before publishing.
- CodeLeaf does not currently supply an isolated arbitrary-Python runner. Learner snippets must only be run locally or in a future isolated service.
- Production database import, API requests against the live deployment, Vercel build, and Render deployment were not performed in this patch-generation step.

## Status counts must be revalidated

Run `python scripts/validate_course_content.py --course-slug numpy` before any import. The command is file-system-only and does not need the database. Then use `python scripts/import_course_files.py --course-slug numpy` as the dry run. Only after human review, environment/database readiness, and a status change approved by course maintainers should an apply/publish command be considered.
