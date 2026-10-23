# SQL course status

**Status: DRAFT — generated package; requires technical/editorial review before publication.**

- Source PDF inspected: `SQL.pdf` (60 pages rendered and text-extracted).
- Source curriculum: 24 modules and 261 numbered lesson topics; all nested subtopics retained in `syllabus-map.json` and lesson files.
- Practical exercises: 32 separate files with protected repository-only solution files.
- Projects: 9 source projects plus the Production-Ready Commerce Database capstone (10 total), each with a protected reference-solution note.
- Knowledge checks: 261 separate files × 3 draft questions = 783 questions; answer keys remain in repository-only files and are not imported into public responses.
- Visual assets: 285 original SVG diagrams (261 lesson visuals + 24 module overview visuals).
- Data: synthetic PostgreSQL lab schema and seed data; setup script deliberately drops and recreates only the local course tables, so it must be run solely in the disposable course database.
- Default execution mode: static validation. The scaffold has no SQL execution service; do not imply that the frontend preview executes SQL.
- XP: no course-authored XP fields or overrides. The platform's existing server-side lesson/exercise XP policy remains authoritative.
- API/database integration: existing generic catalog, outline, lesson, project, asset, and importer support is reused; no backend/frontend schema or deployment configuration change was required.
- Validation status (2026-10-11): local course content validation **PASS**; importer dry run **PASS** with no database changes; existing API contract suite **PASS**. See `VALIDATION-REPORT.md` for the exact boundaries. PostgreSQL execution and application-database `--apply` were not run; the local environment has no `psql`/PostgreSQL service. Frontend build did not run successfully because Vite dependencies are not installed.

## Required review before publication

1. Run each SQL example with the target PostgreSQL version, the included lab data, and any stated optional extension.
2. Review all 261 lessons and 783 knowledge-check questions for technical accuracy and pedagogical clarity.
3. Replace/supplement `contains_all` exercise smoke checks with engine-backed tests before making the XP-granting graded activities public.
4. Verify public routes never expose repository-only question answers or project/exercise solutions.
5. Review project rubrics and verify the full importer dry-run/apply path against a disposable PostgreSQL database.
6. Never set published status until the review and database-backed integration tests pass.
