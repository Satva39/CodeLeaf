# AngularJS Course Status

- Status: **draft — requires subject-matter and product review**.
- Source PDF: `AngularJS(1).pdf`, 37 pages reviewed (rendered contact sheet and text extraction).
- Source curriculum represented: 24 modules, 136 numbered lessons, 957 subtopic headings, 30 practical exercises, 10 projects and one exam blueprint.
- Visuals: 160 original SVGs (one per module plus one per lesson), with alt text/captions in `assets/asset-manifest.json`.
- Integration: existing importer, database contract, API routes, catalog fallback and preview mechanism are reused; the current frontend already has an `angularjs` catalog entry. No application code or schema migration is required for this content-only patch.
- XP: no course-authored XP overrides; importer/backend platform rules remain authoritative.
- Execution: example blocks are marked `static-validation`. No arbitrary code is run in the FastAPI process and no AngularJS browser runner is claimed.
- Security: lesson checks and project solutions remain repository-side content; the existing APIs are expected to return learner-safe fields only.
- Not performed: database import/apply, live API/database tests, production deployment, browser runtime execution, real deployment/runner validation.
