# Java course patch status

- Status: **Draft, structurally validated and locally checked; not imported to the database or published.**
- Source: `Java.pdf`, 69 pages; all pages rendered and reviewed, including the project mock-up illustrations on pages 60–61.
- Ordered curriculum: 32 modules and 336 separate lesson files; all 336 numbered lessons and their subtopic outlines are represented in `syllabus-map.json`.
- Exercises: 48 individual exercise files across beginner/intermediate/advanced tracks, each with a separate protected solution file, acceptance criteria, hints, and test-case outline.
- Projects: 10 project briefs (nine progressive projects plus the capstone), each with a 100-point rubric and separate protected design notes.
- Knowledge checks: 336 separate question sets × 3 questions = 1,008 questions; answer keys and explanations are kept in repository-only question files.
- Visuals: 368 original SVGs (32 module roadmaps + 336 lesson concept maps). Every file is enumerated in `assets/ASSET-CHECKLIST.md` and `assets/asset-manifest.json`.
- Baseline: Java SE 25 LTS; JDK 27 primitive-type-pattern material is explicitly preview-only in lesson 335.
- Validation: CodeLeaf validator and importer dry run pass. 330 standalone lesson examples compiled with JDK 21; 47 single-file exercise reference solutions compiled with JDK 21; 20 representative lesson runtime smoke tests and 12 protected reference-solution runtime smoke tests passed. See `backend/content/courses/java/VALIDATION-REPORT.md`.
- Integration: Uses the existing generic CodeLeaf content importer, database model, catalog/lesson APIs, and asset route; no Java-specific backend/frontend source changes, schema migration, dependency change, or deployment configuration change is included.
- Limitations: JDK 25/27, live PostgreSQL writes, deployed APIs/frontend rendering, and a Java execution sandbox were not available/tested. Token-based exercise grading remains only a smoke check; behavioral grading requires a separately isolated Java runner and task-specific tests. Everything remains draft pending human review.

See `backend/content/courses/java/references/curriculum-review-notes.md`, `backend/content/courses/java/VALIDATION-REPORT.md`, and `backend/content/courses/java/assets/ASSET-CHECKLIST.md` for details.
