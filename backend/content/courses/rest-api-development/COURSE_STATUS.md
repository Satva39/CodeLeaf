# REST API Development — Course Status

- **Course slug:** `rest-api-development`
- **Content status:** DRAFT — review and explicit publication required.
- **Syllabus:** 24 modules, 240 main lessons and 975 decimal subtopics mapped from the attached 49-page PDF.
- **Practice:** 30 formal applied exercises with separate solution files.
- **Projects:** 11 separate briefs (10 progression projects plus the multi-vendor commerce capstone), each with a protected reference solution and a 100-point rubric.
- **Knowledge checks:** 240 protected question-set files with 3 questions each (720 questions). Files include answer keys and explanations; the existing lesson/knowledge-check API is designed to keep these out of ordinary learner payloads.
- **Assessment:** one 120-minute/50-question exam blueprint; its question pool is authored but **not integrated into CodeLeaf’s actual learner exam/attempt flow**. The current `ExamPage.jsx` expressly presents a demo assessment. Do not claim timed delivery, persisted exam attempts, or certificate issuance based on this package.
- **Visuals:** 264 original SVG assets (24 module maps + 240 lesson concept maps).
- **Optional specializations:** recorded in `references/specializations.json`. They are reference-only because the current importer has no first-class specialization-track model/UI.
- **Source changes:** no React, FastAPI, database model, migration, dependency manifest, Vercel, Render, Docker or environment file is changed by this patch. The course uses the existing directory-based importer and course-content endpoints.

## Validation evidence

Validated locally before packaging:

- `python scripts/validate_course_content.py --course-slug rest-api-development` — passed.
- `python scripts/import_course_files.py --course-slug rest-api-development` — passed dry run; no database changes made.
- JSON links, stable IDs, module/lesson/exercise references, protected question/solution paths, asset paths, SVG XML, grader definitions, and project rubric totals — checked by the course validator.
- Representative SVG assets — rendered and manually reviewed.

Not run / not claimed:

- No database import (`--apply`), production publication, live backend/database integration, frontend build, automated browser test or deployment was performed for this course patch.
- Because no app source changed, there is no frontend build regression check specific to changed app code. A smoke test after importing is still recommended.

## Safe next step

Review `COURSE_COVERAGE_REPORT.md` and a sample from every module before writing content to a database. Keep the course in draft while reviewing. After explicit approval, use the commands in `PATCH-INSTRUCTIONS.txt`; publishing requires reviewed content statuses and `--apply --publish`.
