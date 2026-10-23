# jQuery course build status

- **Course status:** draft / needs human technical and editorial review
- **Baseline:** jQuery 4.0.0 (official Download page and release article checked 2026-10-12)
- **Source PDF:** 45 pages reviewed in rendered contact sheets and extracted syllabus text
- **Module count:** 22
- **Lesson count:** 193 (source topics 1–193 preserved)
- **Exercise count:** 193 (one linked practice per lesson)
- **Protected lesson checks:** 193 question sets × 3 questions = 579 questions
- **Projects:** 13 (12 progressive projects plus the capstone)
- **Final assessment:** 1 exam blueprint (not a claim that final-exam persistence/certificate issuance is live)
- **Visual assets:** 22 original SVG module diagrams, each 1280 × 720 (16:9)

## Still required before publication

1. Have a jQuery-experienced reviewer check every API example against jQuery 4.0.0 and the corresponding official documentation.
2. Run examples in a local browser page with network behavior mocked or controlled; test empty, failure, keyboard, and reduced-motion states where relevant.
3. Validate that the deployed knowledge-check endpoint returns no answer keys or explanations before submission.
4. Review exercise grading tests and solutions for each topic; smoke-string grading is not proof of semantic correctness.
5. Run the import dry-run against the exact CodeLeaf checkout and a disposable PostgreSQL database before importing to production.
6. Keep all items draft during review; publish only after all course/module/lesson/item statuses are reviewed and intentionally updated.

No live database import, production deployment, browser E2E run, or certificate issuance was performed while generating this patch.
