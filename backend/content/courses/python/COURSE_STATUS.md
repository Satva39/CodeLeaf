# Python course generation status

**Status: DRAFT — do not publish without review.**

- Source PDF inspected: `Python.pdf` (23 pages). The ordered core syllabus preserves 27 modules and lessons 1–324.
- Content written as separate files: course metadata, 27 module files, 324 lesson files, 28 exercises with separate protected reference-code solutions, 324 three-question knowledge-check sets, an exam blueprint, 15 project briefs with separate reference guides, specialist tracks, references, and lesson/module SVGs.
- Visuals: all local SVG paths exist and are listed in `assets/asset-manifest.json`; diagram XML is validated by CodeLeaf's local content validator.
- Runtime truth: examples are marked `static-validation`. The current site shows stored expected output and does not execute Python. Run snippets locally.
- Exam truth: question files and answer keys are repository-only draft content; the existing importer does not implement a live exam service for them.
- XP: no author-defined XP override is present. Existing CodeLeaf backend rules remain authoritative.
- Database: no schema change or Alembic migration is needed for the directory importer.
- Deployment: no Render, Vercel, Docker, dependency manifest, or environment-file changes are included.
- Required before publication: Python subject-matter review of all explanations/snippets; verify Python 3.15 syntax and APIs in the relevant runtime; review project solution completeness; validate answer-key security and exam service; test responsive/accessibility behavior; decide on a secure isolated Python runner if in-page execution is desired.
