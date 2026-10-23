# ASP Course Status

- Course slug: `asp`
- Current status: **draft**; not published.
- Source PDF: `ASP(1).pdf` (35 pages), visually inspected page-by-page via contact sheets and parsed text.
- Modules: 15
- Lessons: 116
- Exercises: 24
- Projects: 7 (including the capstone)
- Assessments: 1 exam blueprint plus six protected question pools
- Lesson knowledge-check questions: 348
- Included visuals: 132 SVG files (one course roadmap, 15 module overviews, 116 lesson diagrams).

## Verification completed during generation

- All lesson topics 1–116 parsed from Section B and assigned to their matching module ranges.
- Every lesson has a separate JSON file, 2–4 outcomes, a diagram block, an inspectable code/config/trace block, source links, draft status, and a three-question protected knowledge-check file.
- All 24 Section C exercise briefs and all seven Section D projects have dedicated files.
- Every exercise has a separate repository-only solution outline; every project has a separate repository-only reference outline.
- Every visual referenced by lesson/module metadata is included as an SVG file and listed in `assets/asset-manifest.json`.
- No per-lesson or per-exercise XP override is authored.

## Not run / pending review

- Classic ASP/VBScript was not executed: the generation container is not the target Windows/IIS environment, and CodeLeaf's browser playground does not execute Classic ASP.
- ADO and COM examples were not run against a real database/provider/registered component.
- The PostgreSQL/database import is not applied by this patch generation. Run the importer in dry-run mode first.
- No Vercel/Render deployment or production publication was performed.
- Review all content, examples, provider assumptions, security lessons, and assessment answers with a Classic ASP/IIS specialist before changing status to `published`.
