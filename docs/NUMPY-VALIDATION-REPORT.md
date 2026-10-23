# NumPy CodeLeaf validation report

**Generated:** 2026-10-13  
**Course slug:** `numpy`  
**Course status:** `draft`  
**Project:** uploaded CodeLeaf ZIP; no production service was modified.

## Final content counts

| Artifact | Count |
|---|---:|
| Modules | 22 |
| Lessons | 220 |
| Exercises | 40 |
| Repository-only exercise solution files | 40 |
| Projects | 10 |
| Lesson knowledge-check sets | 220 |
| Knowledge-check questions | 660 |
| Final assessment blueprints | 1 |
| SVG visuals | 242 |
| JSON files in course tree | 570 |

## Checks

| Check | Status | Evidence / detail |
|---|---|---|
| CodeLeaf course content validator | **PASS** | Exit code 0; 22 modules, 220 lessons, 40 exercises, 10 projects, 220 question sets, 660 questions, 1 assessment, 242 visuals; all referenced paths, IDs, relationships, grading modes, XP-key restrictions, and SVG XML passed. |
| Packaged patch smoke test | **PASS** | Re-extracted the final ZIP into a clean temporary checkout alongside the existing CodeLeaf validator/importer, then reran both commands successfully. |
| Existing directory-based importer, dry run | **PASS** | Exit code 0; reports DRAFT / DRY RUN ONLY and confirms no database changes. |
| Python snippets from lessons | **PASS** | 216 of 216 Python examples executed in separate temporary working directories under Python 3.13.5 / NumPy 2.3.5; no runtime exceptions. |
| Existing API contract test | **PASS** | `scripts/test_course_api_contract.py` passed all checks for draft privacy, authenticated progress, lesson response protection, SVG asset serving, idempotent XP, incorrect/correct exercise submissions, server-side boost, and streak handling; temporary SQLite only. |
| Existing protected knowledge-check API test | **PASS** | `scripts/test_knowledge_check_api.py` passed tests for prompt retrieval, answer/explanation protection, server-side grading, feedback timing, invalid submissions, and draft visibility; temporary SQLite only. |
| Asset checklist | **PASS** | Lists every one of the 242 SVG filenames with format, dimensions, ratio, purpose, alt text, and inclusion status. |
| JSON/SVG syntax and source relationships | **PASS** | Covered by course validator. |
| Production database import (`--apply`) | **NOT RUN** | No production/staging database credentials or writes were used. |
| Render deployment / Vercel build | **NOT RUN** | No deploy/config/dependency changes were made and no production deployment was attempted. |
| NumPy 2.5 execution matrix | **NOT RUN** | Only NumPy 2.3.5 was installed in the generation environment; re-run examples on NumPy 2.5 before publication. |
| Secure online execution of arbitrary Python | **NOT PROVIDED** | No isolated runner exists in the current project inspected; examples are explicitly local/static-validation. |

## Interpretation

- No course validator or final dry-run check failed.
- The API contract and knowledge-check integration tests ran locally against temporary SQLite databases and did not touch the configured production database.
- The Python example pass establishes that each included Python snippet ran without an exception in the available validation runtime. It does not prove cross-version equivalence or exercise every possible input.
- The subprocess environment printed a spreadsheet-runtime warm-up traceback to standard error even for successful commands; each listed passing command returned exit code 0 and printed its success report. This warning is external to the course files.
- All generated content stays `draft`; counts passing structural validation are not the same as an instructional or accessibility approval.
