# R Language course status

- **Slug:** `r`
- **Status:** Draft; not ready for publication
- **Source PDF:** `R(1).pdf`, 62 pages
- **Source syllabus coverage:** 23 modules, 247 numbered lessons, 40 exercises, 10 projects including the capstone
- **Knowledge checks:** one file per lesson; 3 questions per lesson (741 total)
- **Visuals:** 31 original SVG files (one overview per module plus additional concept diagrams)
- **Execution mode:** `static-validation`; no R runner was added
- **Database/deployment changes:** none; existing importer and API contracts are preserved

## Still required before publication

1. Have an R subject-matter reviewer verify every lesson, example, expected output, statistical statement and specialist topic.
2. Run executable examples with a supported current R version and record package/version requirements. Some integration and deployment snippets are design sketches by intent.
3. Replace or constrain `contains_all` token matching for code exercises before publishing; it does not execute R or prove correctness.
4. Conduct local importer, API-preview, frontend-build and authenticated progress/XP tests against a non-production database. No database write, production deployment, XP award or certificate issuance was performed for this patch.
5. Review the UI display of code blocks, diagram asset paths and lesson sidebars after import.
