# CodeLeaf C# Course Patch — Validation Report

## Content inventory

- Course slug: `csharp`
- Status: draft
- Modules: 25
- Lessons: 195
- Formal exercises: 30
- Project artifacts: 9 (8 staged projects and one capstone)
- Knowledge-check sets: 195, with 3 questions per set (585 total)
- Exam blueprints: 1
- Original SVG teaching visuals: 43 (25 module overview diagrams and 18 lesson diagrams)
- Course JSON files validated: 499

## Checks run in the supplied working environment

| Check                                         | Result                        | Evidence / scope                                                                                                                                                                  |
| --------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CodeLeaf course content validator             | PASS                          | `python scripts/validate_course_content.py --course-slug csharp`; validates JSON, relationships, IDs, local references, grading config, asset paths, SVG XML.                     |
| Importer dry run                              | PASS                          | `python scripts/import_course_files.py --course-slug csharp`; validated the course with no database changes.                                                                      |
| Knowledge-check API contract tests            | PASS                          | `python scripts/test_knowledge_check_api.py`; 8 assertions passed, including hidden answer keys/explanations and draft visibility.                                                |
| Backend API / reward / privacy contract tests | PASS                          | `python scripts/test_course_api_contract.py`; 20 assertions passed, including authorization, draft privacy, 20 XP base, server-side 1.5× boost, idempotency, and streak behavior. |
| SVG/XML and path verification                 | PASS                          | Performed by the CodeLeaf course validator; all 43 asset references resolve.                                                                                                      |
| Patch archive integrity                       | Verify after archive creation | ZIP archive is checked with `unzip -t` / `7z t` during packaging.                                                                                                                 |

## Not run / not claimed

- C# snippet compilation or execution: not run; this environment has no .NET SDK or C# compiler.
- Frontend production build: not run; no frontend code is changed by this content-only patch.
- Database import with `--apply`: not run; no database writes were performed.
- Production deployment, production DB integration, and external runner execution: not run.
- Human curriculum review: still required. All authored course content is intentionally draft.

## Review caveats

- Examples use `static-validation`, not remote execution. Validate code snippets with .NET 10 and any required packages/frameworks before publishing.
- The current exercise grader uses the platform's configured acceptance/token checks rather than compiling and running arbitrary C# code.
- Project starters are small scaffolds and project solution files are outlines, not complete production applications.
- The source PDF's stated modern baseline is C# 14 and .NET 10. Official Microsoft Learn links and the review notes are included under the course reference files.
