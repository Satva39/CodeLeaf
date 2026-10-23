# Node.js course status

- **Course slug:** `nodejs`
- **Source:** `NodeJS.pdf` (57 pages; sections A–G reviewed using extracted text and page visuals)
- **Status:** Draft — not approved for public publication.
- **Modules:** 29
- **Lessons:** 263; all source lesson numbers 1–263 are mapped into separate files with the original titles and subtopics preserved.
- **Exercises:** 24 separate tasks matching Section C; each has a protected reference solution. The CodeLeaf exercise grader currently performs limited static pattern checks rather than executing learner code.
- **Projects:** 9 (8 progressive projects plus the production-ready commerce capstone), matching Section D.
- **Assessments:** 1 final exam blueprint with 60 draft questions.
- **Knowledge checks:** 263 lesson sets × 3 questions = 789 draft questions; the final exam adds 60 protected questions.
- **Visuals:** 293 original SVGs (1 roadmap, 29 module overviews, 263 lesson concept maps). All are included and declared in `assets/asset-manifest.json`.

## Scope and version decisions

Use a supported Node.js LTS runtime as the primary learner setup (Node.js 24 LTS checked on 2026-10-13). Node.js 26 is Current and Node.js 22 is also listed as LTS on the official release page. API, CLI, SQLite, TypeScript integration, and stability details can be version-sensitive. Express and Socket.IO-style material is identified as ecosystem/framework integration rather than Node.js core; TypeScript and specialist runtime APIs remain optional/version-sensitive.

The permission-model lessons explicitly state that Node.js permissions are not a complete sandbox for malicious code. Arbitrary learner code is not executed inside CodeLeaf's FastAPI process.

## Validation

See `VALIDATION-REPORT.md` for the validation inventory, exact command results, covered API regression tests, and checks that were not run. The content validator, snippet syntax check, importer dry run, syllabus parity check, and existing temporary-SQLite API regression tests passed on 2026-10-13. The course remains draft and was not imported into a configured production database.
