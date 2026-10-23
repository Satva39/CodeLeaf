# Linux Course Status

- Course slug: `linux`
- Status: **draft**
- Syllabus basis: supplied `Linux.pdf`, 58 pages
- Parsed curriculum: 27 modules, 257 lessons (numbered 1–257)
- Practice exercises: 291 (257 per-lesson tasks plus all 34 named Section C exercises)
- Practical projects: 13 (12 projects plus one capstone)
- Knowledge-check sets: 257 with 3 questions each (771 total questions)
- Visual assets: 54 original SVG files (27 module roadmaps and 27 lesson-level concept diagrams)

## Review status

All generated content is draft, including lesson content, exercises, protected solutions, knowledge checks, projects, and exam blueprint. The references provide official documentation entry points; the examples have not been run on every distribution. Review all answer keys/distractors, command compatibility and safety, and each project rubric before publishing.

## Verified in generation

- Exact Section B lesson numbering 1–257 was parsed with no gaps or duplicates.
- Files are written as separate JSON documents with stable IDs and explicit file references.
- XP override fields are not authored.
- Lesson examples are marked for manual terminal use; no arbitrary shell execution code was added to the web backend.

See `references/curriculum-review-notes.md` and root `PATCH-INSTRUCTIONS.txt` for source coverage, corrections, safe usage, and exact commands.

## Local validation performed on 2026-10-20

- **PASS — course-content validator:** 27 modules, 257 lessons, 291 exercises, 13 projects, 257 knowledge-check sets, 771 question records, 1 exam blueprint, 54 visuals, 1,154 JSON files; status remains `draft`.
- **PASS — importer dry run:** course file/tree validation completed and printed `DRY RUN ONLY`; no database changes were made.
- **PASS — link/security consistency check:** lesson/exercise/solution links resolve; all 257 question sets have unique options with exactly one matching answer key per question; all manifest assets exist; no `xp_reward` overrides were found; authored files remain draft.
- **PASS — Bash syntax-only check:** all 257 lesson Bash snippets passed `bash -n`. This parses syntax only; it does not execute the commands or prove distribution-specific runtime behavior.
- **PASS — SVG validation and visual spot-check:** all 54 SVG XML/assets passed the existing validator; rendered previews of module 1, the Linux architecture diagram, and Linux namespaces were inspected.
- **NOT RUN — database import, learner API integration, frontend build, migrations, and production deployment:** no configured database connection or full deployment test was executed for this patch.
