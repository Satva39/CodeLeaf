# jQuery Patch Validation Report

Date: 2026-10-12
Course status: **draft**
Scope: new `backend/content/courses/jquery/` content and `PATCH-INSTRUCTIONS.txt` only; no existing application source or deployment configuration was changed.

## Course package checks

- **PASS** — source PDF inspected: 45 pages; module sequence and continuous topic numbering preserved for 22 modules and topics 1–193. Module 1's title was captured from the rendered page image because its heading was not present in extracted text.
- **PASS** — existing CodeLeaf filesystem/course validator: 22 modules, 193 lessons, 193 exercises, 13 projects, 579 knowledge-check questions in 193 sets, 22 visual assets, and 825 JSON files.
- **PASS** — all linked paths, unique IDs/references checked by the existing validator; SVG XML parsed successfully; prohibited per-activity XP overrides are absent.
- **PASS** — importer dry run: `python scripts/import_course_files.py --course-slug jquery`; validated 22 modules, 193 lessons, 193 exercises, 13 projects, 579 protected knowledge-check questions, and 22 visuals. It made no database changes.
- **PASS** — backend course API contract test: draft-content privacy, authenticated progress, safe lesson/exercise responses, asset serving, reward rules (20 base XP / server-side 1.5x Max entitlement), duplicate-reward idempotency, incorrect exercise answers, and streak-gap behavior. All reported assertions passed against temporary SQLite test data.
- **PASS** — protected knowledge-check API test: answer keys/explanations hidden before submit, server-side grading, invalid-answer/question rejection, and draft privacy. All reported assertions passed against temporary SQLite test data.
- **PASS** — package inventory: 888 course files (825 JSON, 22 SVG, 13 HTML starter files, 13 JavaScript starter files, 13 CSS starter files, and 2 Markdown files).

## Blocked or not run

- **BLOCKED** — frontend `npm run build` could not start in the isolated inspection workspace because the workspace intentionally omitted `node_modules`; the command reported `vite: not found`. No frontend files were changed. Run `npm ci` then `npm run build` in the local `frontend/` directory.
- **NOT RUN** — database write import with `--apply`; use a disposable development PostgreSQL database after configuring `backend/.env` and applying the existing schema/migrations.
- **NOT RUN** — live PostgreSQL/Neon integration, production deployment, browser end-to-end execution of lesson samples, live external API requests, full accessibility audit, and final exam/certificate issuance. The existing project notes describe some of these LMS flows as incomplete/demo; this patch does not claim to implement them.

## Local commands (Windows PowerShell)

From the Code_Leaf repository root:

```powershell
Set-Location .\backend
python scripts\validate_course_content.py --course-slug jquery
python scripts\import_course_files.py --course-slug jquery
python scripts\test_course_api_contract.py
python scripts\test_knowledge_check_api.py

Set-Location ..\frontend
npm ci
npm run build
```

For a write test only against a disposable development PostgreSQL database:

```powershell
Set-Location ..\backend
python scripts\import_course_files.py --course-slug jquery --apply
```

Do not run `--apply` against production until the course has been reviewed and the import has been tested against a disposable database. All course content remains draft; the final exam blueprint is a blueprint, not a claim that persisted exam sessions or certificates are live.
