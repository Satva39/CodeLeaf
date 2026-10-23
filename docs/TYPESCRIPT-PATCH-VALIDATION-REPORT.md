# TypeScript Course Patch Validation Report

Generated: 2026-10-14  
Target course: `typescript` — TypeScript 7.0 as the curriculum's primary version assumption  
Status: **Draft; not published**

## Content inventory

| Item | Count | Result |
|---|---:|---|
| Modules | 26 | PASS |
| Lessons | 239 | PASS; IDs and global sequence 1–239 are unique and continuous |
| Exercises | 30 | PASS; linked to the intended lessons, with separate protected solutions |
| Project briefs | 10 | PASS; 9 named PDF projects plus the separately described capstone |
| Lesson knowledge-check sets | 239 | PASS; 3 questions per lesson |
| All protected assessment questions | 766 | PASS; 717 lesson checks plus 49 final-assessment questions |
| SVG visuals | 266 | PASS; 1 roadmap, 26 module overviews and 239 lesson concept maps |
| JSON files | 592 | PASS; course validator checks schema/path/relationship rules supported by the repository |

## Validation and test results

- **PASS — course validator:** `python scripts/validate_course_content.py --course-slug typescript` returned: “All referenced course files, IDs, relationships, graders, asset paths, and SVG XML passed validation.”
- **PASS — importer dry run:** `python scripts/import_course_files.py --course-slug typescript` validated 26 modules, 239 lessons, 30 exercises, 10 projects, 766 assessment questions and 266 assets. It explicitly reported “No database changes made.”
- **PASS — inventory sanity checks:** every lesson sequence is unique and continuous; all knowledge-check keys appear in the options; the four choices are distinct; all 266 asset-manifest paths exist; lessons and assessment files remain draft.
- **PARTIAL — TypeScript snippets:** local `tsc` is TypeScript 5.8.3, not the course target of 7.0. An isolated compiler probe checked 204 TypeScript code blocks; 197 produced no diagnostics. Seven testing snippets refer to `vitest`, which is not installed in the isolated validation environment, so resolution stopped at that missing package. The corresponding lessons provide a Vitest installation/run instruction. This check does not establish TypeScript 7.0 compatibility for every example.
- **NOT RUN — environment-dependent checks:** 35 code blocks written as non-TypeScript examples (such as shell commands, JSON configuration, JavaScript or TSX) were excluded from the isolated TypeScript-only probe. React/TSX compilation, real Vitest execution, Node type-package checks, and browser/runtime execution were not run.
- **NOT RUN — application integration:** database import with `--apply`, API/auth/answer-key tests against a development database, XP idempotency tests, migration execution, frontend production build, deployment and an isolated TypeScript code runner were not run.

The initial validator detected incorrect relative paths for exercise files; those were corrected before final validation. The final validator and importer dry run both passed. No database changes or deployments were made.

## Exact local commands

From Windows PowerShell, after extracting this patch into the **CodeLeaf repository root**:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts\validate_course_content.py --course-slug typescript
python scripts\import_course_files.py --course-slug typescript
```

The last command is a **dry run** and makes no database changes. Only after a human technical review and after confirming the database is a disposable development database, configure `backend/.env` for that database and run:

```powershell
python scripts\import_course_files.py --course-slug typescript --apply
```

Do not use `--publish` until all course lessons, answer-key protection, API access controls, XP/idempotency behavior and actual compiler/runtime examples have been reviewed and tested. See `PATCH-INSTRUCTIONS.txt` for the longer local preview/API checklist.

## Architecture and deployment

The patch adds course content and two repository-root documentation files only. It does not modify Python/React source code, schemas, migrations, dependency manifests, Docker, Render or Vercel configuration. Existing importer, lesson API, SVG asset endpoint and knowledge-check endpoint are reused. No new environment variables or production secrets are required; draft preview should be enabled only in local development if it is needed.

## Limitations

The syllabus and assets are generated as a comprehensive course draft. Technical editorial review is still required before publication. The included exercise grader uses the existing `contains_all` static token checker, not a TypeScript compiler or secure arbitrary-code runner. All lessons, exercises, projects, question sets and assessment blueprint remain `draft`.
