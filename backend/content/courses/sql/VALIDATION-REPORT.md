# SQL Course Validation Report

**Date:** 2026-10-11  
**Status:** Content checks passed; live SQL/database integration remains unverified. The course and all activity content remain draft.

## Checks run

| Check | Result | Evidence / boundary |
|---|---|---|
| Course filesystem validator | **PASS** | `backend/scripts/validate_course_content.py --course-slug sql`: 24 modules, 261 lessons, 32 exercises, 10 projects, 261 knowledge-check sets / 783 questions, 1 assessment blueprint, 285 SVGs, 635 JSON files. Validator reports IDs, relationships, graders, asset paths and SVG XML valid. |
| Importer dry run | **PASS** | `backend/scripts/import_course_files.py --course-slug sql`: validates relational import tree and extended course content; explicitly reports dry-run only and no database changes. |
| Existing API contract tests | **PASS** | `backend/scripts/test_course_api_contract.py`: all contract checks passed, including draft privacy, protected question/solution paths, exercise response safety, authorization, XP reward idempotency/boost rules, and streak boundaries. Uses its own temporary SQLite database. |
| SVG visual spot-check | **PASS** | Rendered and visually inspected the relational model, INNER JOIN and row-level security diagrams. The validator parsed all 285 SVG files. |
| Generator syntax check | **PASS** | `python -m py_compile /mnt/data/generate_sql_course.py`; generator itself is not included in the patch. |
| Frontend production build | **BLOCKED / NOT COMPLETED** | `npm run build` exited 127: `vite: not found`; frontend dependencies were not installed in the environment. No frontend file changed in this patch. |
| PostgreSQL setup script and lesson SQL execution | **NOT RUN** | No `psql`, PostgreSQL server binary/service, or Docker command was available in the environment. Examples remain marked `static-validation`; they have not been executed in PostgreSQL. |
| Import with `--apply` / Alembic against a development database | **NOT RUN** | No dedicated CodeLeaf application development database was configured. No database mutation or production import was attempted. |
| Deployment / production smoke test | **NOT RUN** | No Render, Vercel or managed database deployment was changed or tested. |

## Known review items before publication

1. Review all generated lesson explanations, examples and 783 question/answer explanations with an SQL subject-matter expert.
2. Execute examples against the chosen PostgreSQL version and separately test examples that require privileged roles, PL/pgSQL, PostGIS, or other extensions.
3. Exercise grading currently uses the platform's `contains_all` token smoke check, which is not an SQL parser and cannot establish semantic correctness. Replace or supplement it with an isolated database runner and behavioral tests before publishing XP-granting exercise activities.
4. Run the database importer against a disposable CodeLeaf application database, inspect imported draft records, and use local draft preview only after confirming protected answer files are not accessible.
5. Keep all content in draft until the above technical, pedagogical, privacy, and integration reviews are complete.
