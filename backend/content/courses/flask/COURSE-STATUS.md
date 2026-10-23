# Flask course package status

**Status: draft; not learner-published.** This package contains the complete 21-module / 237-lesson curriculum drawn from the attached 45-page `Flask.pdf`, plus 14 practical exercises, 10 projects, one final-exam blueprint, 237 lesson knowledge-check sets, and 37 authored SVG diagrams.

## Source review

- The PDF cover says 22 modules, but the detailed syllabus and its own Section G identify 21 modules and 237 numbered lessons. The package follows the detailed numbering.
- Third-party tools such as Flask-SQLAlchemy, Flask-Login, Flask-WTF, Celery, Redis and hosting services are identified as extensions/infrastructure rather than Flask built-ins.
- Older file-response API names are recorded in a dedicated migration note rather than treated as preferred current usage.
- Official links and the Flask 3.1.x baseline are listed in `references/reference-index.json`. Verify versions and extension compatibility again before publishing.

## Integration boundary

- The existing CodeLeaf importer and generic course, lesson, exercise, knowledge-check, asset, and project routes are compatible with the file layout. No database migration, dependency change, frontend edit, or deployment configuration change was required for these files.
- The current importer persists course/module/lesson/exercise rows. Lesson knowledge checks and projects are loaded from repository-side JSON by existing backend routes, with learner-facing routes withholding answer keys/reference solutions.
- **The existing runtime does not provide a final-exam blueprint delivery/submission route.** The final-exam blueprint and 40 protected questions are included as draft authoring assets, but they are not a live exam experience until a generic exam API/UI integration is implemented and tested. Do not represent this final exam as available to learners yet.
- No course rows were written to a database, no exam was submitted, and no certificate was issued during this work. XP remains backend-owned; the JSON contains no per-activity XP overrides.

## Checks performed

- CodeLeaf `validate_course_content.py --course-slug flask`: passed (21 modules, 237 lessons, 14 exercises, 10 projects, 711 lesson knowledge-check questions, 37 SVG assets, all referenced paths/IDs/graders/SVG XML and XP-key checks).
- CodeLeaf `import_course_files.py --course-slug flask`: passed validation-only dry run; no database changes.
- Additional static checks: passed (237 lesson/title/sequence mapping against parsed syllabus; required lesson scaffolding; Python snippet AST parsing; 711 answer keys correspond to options; 37 SVG sizes and XML; no author-supplied XP keys).
- Not run: live PostgreSQL import, browser/API end-to-end testing, production deployment, execution of the Flask lesson snippets. Python examples require local/server-runner execution and were syntax-checked only.

## Before publication

Have a Flask reviewer verify the examples, source details, assessment fairness, accessibility, security and third-party extension compatibility. Add and test final-exam API/UI integration separately before exposing the final assessment. Only change draft statuses after review.
