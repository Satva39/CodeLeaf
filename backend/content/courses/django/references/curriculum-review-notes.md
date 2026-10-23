# Django curriculum source review and technical notes

## Source coverage

- Source file: `Django(1).pdf` (61 pages), all pages inspected using parsed text and rendered page overviews, including the course overview/version statement, all module lists, exercise/project briefs, specialized topics, learning path, and coverage checklist.
- Parsed syllabus: Sections A–G. Section B provides **24 modules and 275 continuously numbered lessons**. Section C lists **15 practical exercises**. Section D lists **nine projects plus the multi-vendor e-commerce capstone**. Section E classifies ecosystem extensions separately from core coverage.
- The generated files preserve each lesson title, its full subtopic list, its lesson number, and module order from the PDF. The 275 lessons, 15 exercises, ten projects and 40-question draft final-bank are separate files; all are marked draft.
- Decorative repeated `Django +1` marks and explanatory side notes in the PDF are not treated as additional lessons. The explanatory note after lesson 80 is captured below.

## Version scope checked

The source PDF states Django 6.1.2 was released October 6, 2026, and Django 6.1 supports Python 3.12, 3.13, and 3.14. The official Django 6.1.2 release notes and 6.1 release notes were checked on October 13, 2026. Use a supported patch release, read current security releases before installing/upgrading, and recheck supported Python/database/dependency versions before publication. Django 6.1.2 is a source-PDF snapshot, not an evergreen guarantee that it will always be the best install choice.

## Corrections, clarifications, and optional scope

1. **Django 6.1 model field fetch modes (lesson 80):** retained as a version-specific advanced topic. The lesson links the 6.1 fetch-mode docs and warns readers to confirm the installed patch version and measure behavior. It does not suggest that fetch modes replace `select_related()` or `prefetch_related()` universally.
2. **Django REST framework:** treated as an optional third-party API specialization, not part of Django core. API examples distinguish a small core `JsonResponse` view from DRF serializers/ViewSets.
3. **Celery/background workers and Channels/WebSockets:** identified as optional external ecosystem components. Installing Django alone does not create a broker, worker, websocket layer, or scheduled task runner.
4. **Async boundaries:** the course emphasizes that async views and async-capable APIs do not make all libraries non-blocking or transactions fully async-safe. Keep transaction-sensitive ORM work in a supported synchronous function where required by the docs.
5. **Model validation:** calling `Model.save()` does not automatically call `full_clean()` in every code path. Use form/serializer/service validation and database constraints appropriate to the business rule.
6. **Security controls:** CSRF, CORS, authentication, and authorization are different concerns. CORS is not a built-in generic Django setting that should be assumed configured. Templates autoescape by default in standard Django template usage, but `safe` output and user-generated content require careful policy.
7. **Uploads:** extension checks alone do not prove uploaded data is safe. Apply size/type/content controls, isolated storage, authorization, and appropriate delivery restrictions.
8. **Deployment:** `runserver` is development-only. Static assets, user media, secrets, HTTPS, logging, backups, production application servers, and health/recovery procedures need deployment-specific configuration.
9. **Transactions/webhooks/external effects:** database atomicity does not roll back email, payment-provider actions, or other remote side effects. Verify provider authenticity, enforce idempotency and uniqueness, and design retries deliberately.
10. **Exams/certificates:** the exam is a draft blueprint and protected repository-side question set. The current project UI was reviewed as demo-oriented; this patch does not claim live exam grading/certificate issuance integration.

## Content status and execution limitations

All course, module, lesson, exercise, project, question, solution, and exam content remains `draft`. The repository importer can dry-run file validation and can write draft records with `--apply`, but database writes require a configured `DATABASE_URL` and migrated schema. The CodeLeaf browser preview does not execute Django/Python server code. Python examples are marked as server-runner fragments or static-validation examples with prerequisites; no isolated learner-code execution infrastructure was added, and no code, external integration, production deployment, payment flow, or certificate workflow is claimed tested.

## Sources

See `references/reference-index.json`. The principal technical references are the official Django 6.1 docs, Django 6.1 release notes, Django 6.1.2 release notes, async support, models/queries/fetch modes, migrations/transactions, forms/authentication/security/testing, and deployment checklist. Specialized packages link to their own documentation and are identified as third-party.
