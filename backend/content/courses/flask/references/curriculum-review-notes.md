# Flask course curriculum review notes

Review date: 2026-10-19
Source: attached `Flask.pdf` (45 pages), visually reviewed across all pages and text-extracted for the full syllabus.

## Count correction
The PDF cover says **22 modules**, while its detailed curriculum and Section G correction note specify **21 modules and 237 numbered lessons**. This package follows the detailed list: 21 modules, lesson IDs 001–237. The 14 practical exercises and 9 named projects are preserved, and the separately named Modular Learning Management Platform capstone is treated as a tenth project.

## Technical scope clarifications
- Flask 3.1.x is the course baseline. The official Flask changelog lists Flask 3.1.3 as released on 2026-02-18; version-sensitive content must be checked again at publication time.
- Flask is a WSGI web framework. Its development server/debugger is for local development, not production hosting.
- SQLAlchemy/Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, caching systems, task queues, object storage, tracing and WebSocket support are treated as optional ecosystem integrations, not as Flask built-ins. Their compatibility, security posture and operational dependencies require separate review.
- Async views do not turn Flask's WSGI server into an ASGI server or make every workload faster. Durable work belongs in a queue/worker architecture where required.
- Legacy API names listed in the PDF (for example `attachment_filename`, `cache_timeout`, and `add_etags`) belong in a migration/compatibility discussion; modern examples should use current supported signatures and be checked against the chosen runtime.
- Practical projects and exercises are repository artifacts and review rubrics. CodeLeaf's browser preview does not execute Python/Flask; examples are labeled for server runner, static validation or human review. A separate isolated runner would be required for safe learner-code execution.
- Course files remain draft. No database migration, frontend route, deployment configuration, or dependency manifest change is necessary because the existing idempotent importer and database-backed catalog/lesson routes already support directory-based course content.

## Source coverage
- Section A: overview, audience, prerequisites, outcomes and workload.
- Section B: all 21 modules and 237 numbered lessons with listed subtopics.
- Section C: all 14 practical exercises.
- Section D: nine progressive projects plus the separate capstone.
- Section E: optional/specialized topics and legacy migration notes.
- Section F: five-phase learning path and milestones.
- Section G: coverage matrix, count correction and official source list.

## Publication checklist
1. Subject-matter review each lesson's explanation and snippets.
2. Run the course tree validator and importer dry run.
3. Verify all example code against the selected Python/Flask patch versions; sample fragments have not been claimed as executed.
4. Review protected question and project/exercise solution handling before publication.
5. Publish only after reviewed status is set and the course importer is run with the explicit publish workflow.
