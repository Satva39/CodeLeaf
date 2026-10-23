# AWS Course Patch — Validation Report

**Target:** `aws`  
**Source:** `AWS.pdf` (57 pages) and the supplied Code_Leaf project ZIP  
**Generation date:** 2026-10-11  
**Course publication state:** Draft; AWS-specific editorial/technical review remains required.

## Package counts

| Item | Count | Result |
|---|---:|---|
| Modules | 24 | Passed |
| Main lesson topics | 285 | Passed; source IDs 1–285 preserved |
| Source PDF subtopics | 1,148 | Passed; each compared to the parsed PDF topic listing |
| Practical exercises | 22 | Passed |
| Protected exercise solution files | 22 | Passed by CodeLeaf validation |
| Project briefs | 10 | Passed |
| Project solution outlines | 10 | Passed by CodeLeaf validation |
| Per-lesson knowledge-check sets | 285 | Passed |
| Knowledge-check questions | 855 | Passed; every answer key matches one option |
| Exam blueprints | 1 | Passed |
| Original SVG visuals | 32 | Passed; well-formed XML with accessible title/description and 1200 × 675 viewBox |
| JSON files | 662 | Passed |

## Tests actually run

1. `python scripts/validate_course_content.py --course-slug aws` — **PASS**. CodeLeaf reported all referenced files, IDs, relationships, graders, asset paths, SVG XML, XP-key checks and count relationships passed.
2. `python scripts/import_course_files.py --course-slug aws` — **PASS (dry run only)**. CodeLeaf validated 24 modules, 285 lessons, 22 exercises, 10 projects, 855 questions and 32 visual assets. It confirmed that no database changes were made.
3. PDF-to-course coverage audit — **PASS**. Compared all 285 source lesson titles and all 1,148 listed subtopics against the generated lesson files; no mismatches were found.
4. JSON/assessment/asset audit — **PASS**. All 662 JSON files parsed; all 855 keys were present among their answer options; no author-supplied XP override keys were found; all 32 SVG files were parsed and checked for accessible title/description and expected dimensions.

## Not run / limits

- `--apply` database import: **NOT RUN**; no development or production database was written to.
- Frontend build: **NOT RUN**; no frontend source was changed. `npm run build` is included as an optional local regression check.
- Live AWS API/CLI invocations, AWS account configuration, billing, deployment, load testing, external runner, and certificate issuance: **NOT RUN**.
- A 285-topic structure and direct official references are present, but **the course is not publish-ready**. Every service-specific command/configuration and answer explanation needs human technical review in the target AWS/Region/account context before selected statuses are changed from `draft` to `published`.

## Source note

The PDF's overview and final validation note say 287 lesson IDs, but its explicit numbered syllabus lists exactly 285 consecutive lessons (1–285). The patch keeps those 285 listed topics and does not fabricate lessons 286 or 287. AWS Data Pipeline is treated as a legacy migration topic because new customer access closed in 2024; Amazon Quick terminology and budget-alert limitations are documented in the course review notes.
