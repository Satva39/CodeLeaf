# Angular course status

**Status: DRAFT — complete structured course package, not yet publication-approved.**

## Contents created

- Source coverage: all 26 modules, all 349 main syllabus topics and 1378 extracted subtopics from the attached PDF.
- Lessons: 349, each a separate JSON file with outcomes, content blocks, an SVG visual, example, expected result, run/reset notes, task, hints, mistakes, recap, references and version notes.
- Knowledge checks: 349 separate files with 3 questions each (1047 questions). Answer keys remain in repository-side files and are returned only by the existing backend grading flow when the course is enabled.
- Exercises: 48 linked tasks, each with an independent exercise JSON and protected solution outline.
- Projects: 13 briefs (12 listed projects plus the commerce capstone), each separate, with starter-file metadata, milestones, test plan, 100-point rubric and repository-only reference outline.
- Assessment: one 75-minute draft blueprint and 45 draft final-assessment questions.
- Visuals: 375 SVG files: 26 module overviews plus one unique lesson concept map per lesson. Complete inventory: `assets/ASSET-CHECKLIST.md`.

## Integration

The current CodeLeaf directory importer and API already support per-course JSON manifests, lessons, exercises, protected knowledge-check files, projects, source references and SVG course assets. This patch adds only the `angular` content directory and documentation; no application source, database schema, dependency manifest or deployment configuration was changed.

## Required review before publication

1. Run the validator and importer dry run shown in `PATCH-INSTRUCTIONS.txt`.
2. Import draft records into a local test database, run API contract and knowledge-check tests, and inspect returned payloads for protected answer leakage.
3. Create a disposable Angular v22 workspace that matches the current official Node.js/TypeScript/RxJS compatibility table. Review and run version-sensitive examples, especially Signal Forms, resources, zoneless APIs, SSR and animation migrations.
4. Run the actual configured Angular tests/build for learner examples; this patch does not claim these Angular snippets were individually compiled.
5. Run an accessibility review and human technical review before changing authored status to `published`. Certificate issuance and production deployment were not tested or added.
