# PHP course validation report

Generated 2026-10-11 from the supplied `PHP.pdf` and current CodeLeaf repository.

| Check | Result | Evidence / boundary |
|---|---|---|
| PDF coverage | PASS | All 48 pages reviewed; 28 modules and 290 numbered source topics represented in ordered syllabus map. |
| Course JSON, IDs, paths, relationships, graders and SVG XML | PASS | `python scripts/validate_course_content.py --course-slug php`; 696 JSON files validated. |
| Importer integration | PASS | `python scripts/import_course_files.py --course-slug php` completed as validation-only dry run; no database writes. |
| PHP snippet syntax | PASS | 360 snippets passed `php -l` under PHP 8.4.24. This is not a PHP 8.5 compatibility claim. |
| Lesson example outputs | PASS | 290 repository-authored lesson snippets executed in temporary directories under PHP 8.4.24; 0 output mismatches. This is not learner-code execution. |
| Quiz output answer alignment | PASS | All 290 output-tracing questions aligned to their lesson's expected output. |
| Knowledge-check API privacy and grading | PASS | Temporary-SQLite API test passed: prompts/options only on GET, server-side grading, feedback after submission, invalid inputs rejected, drafts hidden without preview. |
| Existing API contract regression | PASS | Existing contract tests passed, including course visibility, protected content, base/max XP values, idempotency, and streak cases. |
| Frontend changed-file syntax | PASS | Changed JSX/JS files parsed with the available TypeScript JavaScript/JSX parser; no TypeScript files were added. |
| Production frontend build | NOT RUN | Frontend dependencies were unavailable offline; npm registry installation did not finish. Run `npm ci` and `npm run build` in a network-enabled environment. |
| Live PostgreSQL import / migrations | NOT RUN | No production/local project PostgreSQL write was attempted. Patch adds no schema migration. |
| PHP 8.5 execution / Render or Vercel deployment | NOT RUN | Local runtime is PHP 8.4.24; no deployment was attempted. |

All course records remain draft. The complete review and publication caveats are in `references/curriculum-review-notes.md` and `COURSE_STATUS.md`.
