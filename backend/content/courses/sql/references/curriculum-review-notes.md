# SQL curriculum review notes

**Status:** Draft; generated on 2026-10-11. This package has not been subject-matter approved and is not marked published.

## Source coverage

- Inspected the full 60-page `SQL.pdf`; text was extracted for the entire document and every page was rendered for visual review. The main numbered curriculum is topics 1–261 across 24 modules.
- Preserved the 261 numbered topics and all nested subtopics in `syllabus-map.json` and one lesson file per topic.
- Preserved the 32 Section C practical exercises as separately referenced exercise files.
- Preserved the nine Section D projects and the `Production-Ready Commerce Database` capstone as ten project briefs.
- Preserved Section E's core/professional/database-specific/data engineering/analytics/administration/specialist categories and its four optional specialization tracks in `course.json` and `syllabus-map.json`.
- Preserved the six-stage suggested learning path and review checklist; they are described in the roadmap/quality sections of `syllabus-map.json` and the course metadata.

## Corrections and scope decisions

- The PDF lists **261 numbered curriculum topics**; its 32 practical exercises are a separate section and are not counted as lessons. This follows the PDF's final recommendation.
- The PDF says approximately 80–150 hours. Course metadata retains that range rather than inventing a more precise promise.
- The course defaults to PostgreSQL as the practice engine and labels cross-database/engine-specific behavior. PostgreSQL 15+ is the lab baseline because the MERGE topic is included; PostgreSQL 18 current documentation is used for reference links checked on the date above.
- Optional PostGIS/spatial queries explicitly require the extension. SQL Server/T-SQL, Oracle/PL/SQL, MySQL, SQLite, full-text search, JSON, temporal concepts, and distributed SQL are framed as engine- or implementation-specific where appropriate.
- Minor punctuation in `145. NOT NULL , CHECK , and Default Constraints` was normalized to `NOT NULL, CHECK, and Default Constraints` for a readable title; topic meaning is unchanged.
- No syllabus topic was excluded. The course does not silently treat the PDF's illustrative screenshot assets as required course assets; all included teaching diagrams are new SVGs.

## Quality and integration status

- All lessons, exercises, projects, question files, and diagrams are marked `draft` pending human review.
- Examples are PostgreSQL-oriented and marked `static-validation`. The current CodeLeaf frontend's Run example control previews recorded sample output; it does not execute arbitrary SQL. No SQL execution runner, isolation container, timeout policy, or database sandbox was added.
- Knowledge-check answers and reference solutions are kept in repository-only JSON files; public lesson content references, but does not embed, question answers or solution files. Public asset route allows only image/video extensions, not JSON or SQL.
- The existing generic API/catalog and importer already support this course structure. No frontend, backend route, database model, migration, Render, Vercel, or dependency changes were required in this patch.
- Project grading is human review. Exercise `contains_all` graders are only string smoke checks, not SQL parsers; they must be replaced or supplemented by engine-backed tests before publication.
- Code samples and answer keys still require expert technical review; generated file validity is not equivalent to validated SQL execution.
