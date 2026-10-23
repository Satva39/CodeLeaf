# Excel course patch — validation report

**Status:** Content validation passed; course remains draft. **Checked:** 2026-10-12.

## Generated content

| Item | Count | Result |
|---|---:|---|
| Curriculum modules | 27 | All module files present |
| Numbered PDF syllabus topics / lesson files | 262 | Topics 1–262 preserved in order |
| Exercises | 286 | 262 lesson-linked drills plus the PDF's 24 practical exercises |
| Projects | 12 | Includes the integrated capstone; learner starter briefs and protected review plans included |
| Protected lesson question sets | 262 | Three questions per lesson (786 total) |
| Final assessment | 1 blueprint, 18 questions | Question-file count matches the blueprint's 18 questions |
| Protected knowledge-check and assessment questions | 804 | Answer keys/explanations kept in repository-side files |
| SVG teaching visuals | 28 | One learning roadmap plus one visual for each module; 1280 × 720 (16:9) |
| Synthetic CSV datasets | 33 | Every row in each file has the same number of columns |
| Parsed JSON files | 1,153 | All valid JSON |

## Checks run

- **PASS — course validator:** `python scripts/validate_course_content.py --course-slug excel`. It reported 27 modules, 262 lessons, 286 exercises, 12 projects, 804 protected questions, 28 visual assets, 1,153 JSON files, and status `draft`; all referenced files, IDs, relationships, grader configurations, paths, and SVG XML passed.
- **PASS — importer dry run:** `python scripts/import_course_files.py --course-slug excel`. It completed extended validation and explicitly reported that no database changes were made.
- **PASS — API contract tests:** `python scripts/test_course_api_contract.py`. Draft privacy, learner-safe exercise payloads, protected answer paths, asset serving, project privacy, authentication, server-owned 20/30 XP rules, reward idempotency, and streak-gap behavior passed.
- **PASS — knowledge-check tests:** `python scripts/test_knowledge_check_api.py`. Answer keys/explanations were withheld before submit; server-side grading and post-submit feedback, invalid answers/IDs, and draft visibility checks passed.
- **PASS — isolated database import/idempotency:** Using a temporary SQLite database with the current SQLAlchemy models, `--apply` imported 1 course, 27 modules, 262 lessons and 286 exercises. A second import kept those counts unchanged. The temporary database was removed; no configured or production database was used.
- **PASS — repository integrity scan:** all 1,153 JSON files parsed; all 28 manifest SVGs existed and parsed as XML; all 33 CSV datasets had consistent row widths; learner-facing `public_tests` contained no expected answers; no course-authored XP override keys were found.
- **PASS — visual preview:** roadmap and module overview SVGs rasterized to 1280 × 720 PNG previews and were visually inspected. The previews are diagnostics only and are not included in the patch ZIP.
- **PASS — patch scope:** only the new `backend/content/courses/excel/` subtree, the changed `frontend/src/pages/ProjectsPage.jsx`, and these two root-level patch notes are included in the ZIP.

## Not run / limitations

- **NOT RUN — frontend production build:** `npm ci` did not complete in the execution environment and the Vite binary was unavailable, so `npm run build` was not claimed as passing. Run both commands below on a connected local development machine.
- **NOT RUN — Excel engine tests:** formulas, charts, PivotTables, Power Query M, Data Model/DAX, VBA, Office Scripts, and add-ins were not executed inside a desktop/browser Excel installation. Examples and workbooks require target-version checks and, where indicated, human review.
- **NOT RUN — production database or deployment:** no production database was connected and no Render or Vercel deployment/build was performed.
- **NOT RUN — completed workbook artifact review:** the ZIP supplies briefs and synthetic CSV data, not finished `.xlsx` deliverables. CodeLeaf's existing exercise grader checks answer text/choices and does not execute Excel or inspect workbook uploads.

No test that was actually run failed. Items above marked not run are not presented as passes.

## Local commands

Run from PowerShell at the repository root (`E:\Code_Leaf` in the user's prior local path):

```powershell
cd E:\Code_Leaf\backend
python scripts/validate_course_content.py --course-slug excel
python scripts/import_course_files.py --course-slug excel
python scripts/test_course_api_contract.py
python scripts/test_knowledge_check_api.py

# After reviewing the content and configuring DATABASE_URL for a migrated development/test DB:
python scripts/import_course_files.py --course-slug excel --apply

cd E:\Code_Leaf\frontend
npm ci
npm run build
```

Do not run `--apply` against production merely to test the ZIP. All course content is draft. The frontend patch only extends the existing project-page API fetch list to include `excel`; the existing catalog already has an Excel fallback entry. No migration, environment-variable addition, Render config, Vercel config, Docker change, dependency-manifest edit, or credential is included.
