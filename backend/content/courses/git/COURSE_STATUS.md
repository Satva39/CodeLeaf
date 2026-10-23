# Git Course Status

- Course slug: `git`
- Publication status: **draft** (do not publish without technical/editorial review)
- Source: supplied `Git.pdf` (38 pages); the PDF’s numbered syllabus was extracted and mapped into the generated course, retaining its ordered modules and lesson topics.
- Verified syllabus: 20 modules and 216 numbered lessons (continuous IDs 1–216); the PDF's 28 source exercise briefs and six source projects plus capstone are expanded into mapped practice.
- Deliverables: 20 module files, 216 individual lesson files, 51 linked practical exercises with separate protected solution files, 216 lesson-specific knowledge-check sets (648 questions), 7 projects with protected solution outlines, one final exam blueprint with 20 questions, 19 documentation references, 32 SVG visuals (roadmap + 20 module overviews + 11 concept diagrams).
- All lessons, modules, projects, exercises and assessments remain draft. The browser does not execute Git commands; command-changing projects use learner evidence/human review rather than implying execution occurred on the server.

## Validation evidence (run on 2026-10-15)

- **PASS** — `python scripts/validate_course_content.py --course-slug git`: 573 JSON files; 20 modules; 216 lessons; 51 exercises; 7 projects; 216 knowledge-check sets; 668 protected assessment questions counted across lesson checks and final assessment; 1 exam blueprint; 32 SVG assets. All referenced files, IDs, relationships, graders, asset paths and SVG XML passed.
- **PASS** — `python scripts/import_course_files.py --course-slug git` dry run: recognized the complete draft course; no database writes.
- **PASS** — temporary SQLite integration: `--apply` run twice yielded one course, 20 modules, 216 lessons and 51 exercises, with draft publication state preserved.
- **PASS** — `python scripts/test_knowledge_check_api.py`: 8 assertions, including withholding answer keys on GET and server-side grading.
- **PASS** — `python scripts/test_course_api_contract.py`: 20 assertions covering draft privacy, asset serving, protected fields, project/exercise visibility, 20 XP base lesson completion, 1.5x Max-plan boost, incorrect exercise submissions, duplicate reward prevention, XP transaction totals and streak calculation. The patch includes a test-only fixture isolation fix: the script now uses a temporary content root with synthetic HTML metadata/asset/project data, avoiding collisions with the real HTML course files. Production routes/models are unchanged.
- **PASS** — Python bytecode compilation for the relevant backend modules/scripts.
- **PASS** — local API smoke test with draft preview explicitly enabled: Git outline HTTP 200 (20 modules/216 lessons), lesson detail HTTP 200 without hidden knowledge-check references/answer keys, knowledge-check prompt HTTP 200 (3 questions, no answer key), roadmap SVG HTTP 200 (`image/svg+xml`), exercise endpoint HTTP 200.
- **NOT RUN** — full frontend production build, deployed Render/Vercel checks, and live remote/credential interactions. These are outside this content-only patch and need the project dependencies/environment.

## Source coverage and review still required

1. The course preserves the PDF's ordered 20-module, 216-lesson topic coverage, including advanced history recovery, refs/object storage, hooks and configuration, submodules/worktrees, sparse and partial clone, Git LFS, signing, migration, maintenance and automation. The expanded exercise/project design adds practice rather than dropping source topics.
2. A Git-experienced reviewer must spot-check commands and examples, especially reset/revert/rebase, force-with-lease, credentials/signatures, sparse-index, worktrees and maintenance. Verify commands against the learner's installed `git --version` before publication.
3. Review the 648 generated knowledge-check questions and 20 final-exam questions for ambiguity, assessment quality, and coverage. UI details for GitHub/GitLab/IDE integrations should be refreshed before publication.
4. The PDF is a syllabus/roadmap, not a source for all implementation details; explanations and commands are original course authoring cross-referenced to the official Git documentation listed in `references/reference-index.json`. Any correction/interpretation is noted in the review notes.
5. This patch changes no database schema, migration, dependency, environment example, Render/Vercel/Docker configuration or static catalog. Use the existing content importer; only enable draft preview in a local development environment.
