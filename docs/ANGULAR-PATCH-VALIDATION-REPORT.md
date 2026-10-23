# Angular course patch — validation report

## Deliverable scope

- New course directory only: `backend/content/courses/angular/`.
- Root-level support files: `PATCH-INSTRUCTIONS.txt` and this report.
- No existing application code, schema/migration, frontend route, dependency manifest, deployment config or unrelated course was changed.
- Authored status is `draft`; content is not publication-approved.

## Course inventory

| Item | Verified count |
|---|---:|
| Modules | 26 |
| Numbered syllabus topics / lesson files | 349 |
| Extracted subtopics preserved from Section B of the supplied 59-page PDF | 1,378 |
| Exercises | 48 |
| Projects (12 course projects + the capstone) | 13 |
| Lesson knowledge-check sets | 349 |
| Lesson knowledge-check questions | 1,047 |
| Final assessment question file | 45 questions |
| Total protected knowledge-check + assessment questions reported by validator | 1,092 |
| Assessment blueprints | 1 |
| Original SVG diagrams | 375 (26 module overviews + 349 lesson diagrams) |
| JSON files validated in the course | 855 |

## Tests run in this workspace

- **PASS** — `python scripts/validate_course_content.py --course-slug angular`. Validated counts, IDs, relationships, grader configuration, local file references, SVG XML, and draft status.
- **PASS** — `python scripts/import_course_files.py --course-slug angular`. Extended validation succeeded; importer reported `DRY RUN ONLY` and explicitly made no database changes.
- **PASS** — `python scripts/test_course_api_contract.py`. API contract suite passed draft-publication visibility, answer-key privacy, SVG asset serving, authorization, XP reward rules/idempotency, and streak checks.
- **PASS** — `python scripts/test_knowledge_check_api.py`. Knowledge-check suite passed answer-key withholding, server-side grading, invalid answer/question rejection and draft visibility checks.
- **PASS** — additional inventory scan confirmed every listed asset exists, SVG XML is parseable, all referenced local course files exist, and no forbidden course XP override keys are present (the bundled CodeLeaf validator also checks these rules).

## Not run / not claimed

- **NOT RUN** — import with `--apply` against a database. No database records were changed.
- **NOT RUN** — `npm run build` for the React frontend; this is a content-only patch and frontend code was not changed.
- **NOT RUN** — compiling or executing all 349 Angular lesson snippets in a real Angular CLI workspace. Snippets are static instructional content and some need surrounding project context; run them against a pinned compatible Angular version before publication.
- **NOT RUN** — production deployment, external code runner, certificate issuance, manual accessibility audit or human technical review.

## Version/source notes

The reference index records official Angular docs checked on 2026-10-14 and identifies Angular v22 as the primary baseline and v21 as LTS at that time. It covers version compatibility, components, templates, control flow, signals/resources, forms, routing, HTTP, RxJS, testing, SSR/hydration, security, accessibility, CLI, updates and modern animation migration. Re-check the compatibility table for the exact target patch release before publishing.

## Publication gates

Review the content and source links, pin a supported Angular/Node.js/TypeScript/RxJS combination, run the snippets and tests in a disposable workspace, validate accessibility, then intentionally approve and change statuses before any publication. Do not describe the current draft as a verified production-ready Angular course.
