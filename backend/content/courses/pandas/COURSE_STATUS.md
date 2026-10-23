# Pandas course status

- **Source PDF:** `Pandas.pdf` (52 pages).
- **Sections reviewed:** A through G, including the syllabus, practical exercises, projects, specialization guidance, learning path, and review checklist. Page renders were generated for all 52 pages; visual contact sheets were inspected to confirm that the document consists of formatted syllabus pages and callout/version references rather than unparsed data charts.
- **Syllabus coverage:** all 26 modules and 216 numbered main topics (1–216) are represented in `syllabus-map.json`; each nested subtopic is preserved in the matching lesson `subtopics` field.
- **Exercises:** 28 source-derived exercise files, each with a separate repository-only solution file.
- **Projects:** 9 project blueprints (8 projects + capstone), each with a separate repository-only reviewer approach file.
- **Assessments:** one final assessment blueprint and 216 protected knowledge-check files, three questions per lesson (648 questions).
- **Visual assets:** 243 original SVG files (26 module diagrams, 216 lesson diagrams, and one roadmap). See `assets/ASSET-CHECKLIST.md` for each path, dimensions, purpose, alt text, and status.
- **Version references:** official stable Pandas 3.0.6 documentation was checked on 2026-10-13. Local authoring environment has Pandas 2.2.3; do not interpret that as executing all examples against 3.0.6.
- **Publication status:** draft. Subject-matter review, complete target-version execution, dedicated exercise grader review, and production API QA remain required before publishing.
- **Integration impact:** no frontend, backend, migration, configuration, or dependency changes are needed; the repository already includes a schema-compatible course importer and filesystem validator.

## Known scope and review notes

1. The course intentionally preserves the PDF's main topic numbering and nested subtopics; see `syllabus-map.json` for the exhaustive map.
2. The target-version string dtype and Copy-on-Write material is explicitly flagged as version-sensitive. Examples were not all runtime-executed on Pandas 3.0.6 in this environment.
3. Examples using Excel, Parquet, SQL, HTML parsers, plotting, or a filesystem input require their corresponding optional local dependency / resource; these are labelled in the lessons.
4. The project starter tests and generic `contains_all` grading configuration are scaffolding, not a secure arbitrary-Python code runner. The existing CodeLeaf browser playground does not execute Python. Use an isolated runner before enabling automated execution.
5. XP is not assigned by content. The existing platform backend remains responsible for the 20 base XP / 30 boosted XP rules and idempotency.

## Validation performed before packaging

- **PASS:** `python scripts/validate_course_content.py --course-slug pandas` — 26 modules, 216 lessons, 28 exercises, 9 projects, 216 knowledge-check sets / 648 questions, 1 assessment blueprint, 243 SVG assets, 537 JSON files; all references, paths, IDs, relationship constraints, and SVG XML passed.
- **PASS:** `python scripts/import_course_files.py --course-slug pandas` — dry-run import completed; no database changes made.
- **PASS:** `python scripts/test_course_api_contract.py` — existing API privacy, authorization, XP idempotency, reward, and streak contract checks passed using a temporary SQLite test database.
- **PASS:** `python scripts/test_knowledge_check_api.py` — existing protected-question API contract checks passed using test settings.
- **PASS:** all 537 JSON files parsed; the syllabus map contains all 216 numbered topics and all 1,103 nested subtopics extracted from the source syllabus.
- **PASS:** all 243 manifest-listed SVG files exist; CodeLeaf's validator accepted their XML.
- **PASS:** 213 Python lesson examples parsed; 212 ran successfully in isolated smoke tests on local Pandas 2.2.3. Lesson 128's HTML-table example was skipped because the optional HTML parser dependency is not bundled in this environment. The three PowerShell examples were not Python snippets.
- **PASS:** all 28 exercise starter snippets ran successfully on local Pandas 2.2.3.
- **NOT RUN:** target-version runtime execution on Pandas 3.0.6, because that version is not installed in the authoring environment.
- **NOT RUN:** database `--apply`, publication, frontend build, or production deployment. No production database was touched.

The checks above validate file integrity and broad example smoke behavior, not substitute for expert review of every lesson, expected output, exam item, project rubric, or final assessment before publication.
