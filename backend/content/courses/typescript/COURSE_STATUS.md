# TypeScript Course Status

- **Slug:** `typescript`
- **Status:** Draft — intentionally not published
- **Syllabus coverage:** 26 modules, 239 lessons (source topics 1–239), 30 exercises, 9 named projects plus 1 separate capstone (10 project briefs total), 239 lesson knowledge-check sets with 3 questions each, and 1 final exam blueprint.
- **Question inventory:** 717 lesson knowledge-check questions plus 49 final-assessment questions.
- **Visuals:** 266 included original SVGs (1 roadmap, 26 module overviews, 239 lesson concept maps).
- **Source PDF:** `TypeScript(1).pdf`, 40 pages, Sections A–G reviewed; see `references/curriculum-review-notes.md`.
- **Reference verification:** Official TypeScript 6.0 and 7.0 announcements, Handbook and TSConfig docs were checked on 2026-10-14.

## Why this remains draft

The full directory structure and existing importer contract are satisfied, but the generated teaching snippets and the static token graders still need a technical editorial pass and compiler/runtime-specific verification. No TypeScript runner was added to CodeLeaf, and no code snippet is claimed to have executed here. The existing browser playground only previews HTML/CSS/JavaScript. Do not pass `--publish` until human technical review and API/authorization tests are complete.

## Technical clarifications

- The visually present Module 3 title on PDF page 4 is not readable from the PDF text layer; it was included after visual inspection.
- TypeScript 7.0 is treated as available based on the official July 8, 2026 release announcement. See the curriculum review notes for compatibility caveats, TypeScript 6.0 migration advice, and compiler API considerations.
- The 30 exercise graders use the existing `contains_all` mode. This is a static substring check, not a compiler or sandbox. Human review and local compiler tests are necessary.
- Lesson knowledge-check answer keys and solution files remain repository-side protected content; the course stays draft by default.
- No `xp_reward`, `xp_points`, `xp_override`, or similar authored reward field is included. Platform-wide reward rules remain in backend code.

## Verification results recorded for this patch

- **PASS:** `python scripts/validate_course_content.py --course-slug typescript` — validated 26 modules, 239 lessons, 30 exercises, 10 projects, 239 knowledge-check sets, 766 total protected assessment questions, 266 visual assets and 592 JSON files; all referenced files, relationships, grading configs and SVG XML passed.
- **PASS:** `python scripts/import_course_files.py --course-slug typescript` — importer dry run validated the course and made no database changes.
- **PARTIAL:** An isolated syntax/type check with the locally installed TypeScript 5.8.3 compiler examined 204 TypeScript code blocks. 197 had no compiler diagnostics. Seven test examples could not resolve the `vitest` package because that package is not installed in the isolated check environment; their lesson instructions now state how to install it. This is not a TypeScript 7.0 compiler run.
- **NOT RUN:** TypeScript 7.0 compiler validation; installing and running the Vitest examples; database `--apply` import; knowledge-check/API authorization tests against a live database; XP idempotency regression suite; frontend production build; deployment or any external/isolated code runner.

No production deployment, database write, live API test or TypeScript 7.0 execution is claimed. All course records remain draft.
