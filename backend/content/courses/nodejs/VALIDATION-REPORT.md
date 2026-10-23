# Node.js course validation report

**Validation date:** 2026-10-13  
**Course status:** Draft; not published  
**Database writes:** None. The importer ran in its default dry-run mode. API regression tests used temporary SQLite files that were removed at exit.

## Course inventory

| Check | Result |
|---|---:|
| Modules | 29 |
| Lessons | 263 |
| Source syllabus lesson titles/subtopic lists mapped exactly | 263 / 263 |
| Exercises | 24 |
| Projects | 9 |
| Lesson knowledge-check sets | 263 |
| Lesson knowledge-check questions | 789 (3 per lesson) |
| Final assessment | 1 blueprint, 60 questions |
| All question files | 849 questions total, including the final assessment |
| Original visual assets | 293 SVG files |
| JSON files validated | 626 |

## Results

- **PASS — `python scripts/validate_course_content.py --course-slug nodejs`**: verified 29 modules, 263 lessons, 24 exercises, 9 projects, 263 knowledge-check sets, 849 questions across lesson and exam files, 1 assessment, 293 visual assets, 626 JSON files, IDs/references/grader constraints, file paths, and SVG XML. Course status remains `draft`.
- **PASS — `python scripts/validate_nodejs_course_examples.py`**: `node --check` accepted all 287 lesson/exercise JavaScript snippets with Node.js v22.16.0. This is a syntax check only; snippets were not executed and external packages/services were not contacted.
- **PASS — `python scripts/import_course_files.py --course-slug nodejs`**: importer validated the course in **dry-run** mode. It made no database changes.
- **PASS — `python scripts/test_course_api_contract.py`**: 20 checks passed, including authenticated progress, draft privacy, answer/solution protection, asset serving, 20 base XP, 30 boosted XP, zero XP for incorrect answers, duplicate-reward prevention, transaction totals, and streak-gap behavior. This test used its temporary SQLite database.
- **PASS — `python scripts/test_knowledge_check_api.py`**: 8 checks passed, including answer-key withholding before submission, server-side grading, invalid/unknown answer rejection, and hiding draft question sets. This test used its temporary SQLite database.
- **PASS — syllabus parity check**: compared the imported course files against the PDF-extracted syllabus; found no missing lesson numbers, lesson-title mismatches, or subtopic-list mismatches.
- **PASS — Python syntax compilation**: changed validation script and existing importer/course validator compile successfully.

## Not run / limits

- **Not run:** actual PostgreSQL import (`--apply`), migration upgrade, production deployment, Vercel build, frontend browser rendering, and end-to-end testing against deployed services. This patch changes course content and adds one backend validation script; it does not change frontend application code, dependencies, database schema, migrations, or deployment configuration.
- CodeLeaf's current exercise grader checks configured text patterns; it does **not** execute arbitrary Node.js learner submissions. Project and exercise solutions remain protected-content files and the course remains draft until technical/instructional review.
- The official documentation and supported-release page should be checked again before publication because runtime versions and API stability change over time.
