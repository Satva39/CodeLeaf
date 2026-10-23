# Redis course generation status

- Status: `draft`
- Source: attached `Redis.pdf` (47 pages), visually reviewed page-by-page using rendered contact sheets, and extracted text for exact syllabus headings.
- Curriculum: 24 modules, 202 sequential lessons, each with 3 separate knowledge-check prompts.
- Practice: 30 PDF-derived exercises with protected reference notes; 10 project briefs (9 projects plus capstone) with local-only starter files.
- Visuals: 226 original SVGs (24 module overviews + 202 lesson diagrams), each referenced by lesson/module content and manifest.
- Integration: uses existing CodeLeaf directory-based course importer and course-content validator. No React, API, schema, migration, Render, Vercel, or dependency manifest changes were required because the existing content pipeline supports this course format and the `redis` catalog slug already exists.
- Exercise checks: `contains_all` is a static token smoke check, not Redis command execution. Learner code is not executed in the FastAPI process.
- Not performed: no database write/import with `--apply`, no live Redis instance testing, no frontend build, and no production deployment. Review draft content and test in a local development environment before publication.
