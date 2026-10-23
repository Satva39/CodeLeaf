# React course status — draft

- Source: attached `React.pdf` (67 pages). All pages were inspected as rendered contact sheets and parsed text.
- Extracted numbered syllabus: **29 modules / 333 lessons** (lesson numbers 1–333 contiguous).
- Added practical activities: **30 exercise files** and **10 project briefs** with separate protected reference outlines.
- Knowledge checks: **333 per-lesson sets × 3 questions = 999 questions**; final assessment bank: **60 questions**.
- Visuals: **362 original SVGs** (29 module overview diagrams + 333 lesson diagrams). No remote image URLs or third-party screenshots are referenced as included assets.
- Course, modules, lessons, exercises, questions, projects, solutions, reference index, and assets are marked `draft` until reviewed.
- Course API assumption: React 19.3 per official release notes dated 2026-09-09. The supplied CodeLeaf frontend itself remains on React/React DOM 18.3.1; version-specific examples are not executable in the current platform runtime and require a version-matched local learning project. No dependency upgrade was made.

## Editorial/verification notes

1. The source PDF’s Section B title and subtopic labels are preserved verbatim as `title` and `subtopics`; lesson copy and original diagrams expand them.
2. `Create React App` remains a legacy maintenance topic, not the recommended new-project path.
3. React Server Components and Server Functions are taught only with explicit supported-framework/runtime boundaries.
4. PDF screenshots/branding and UI residue such as `React +1` are not copied into the assets.
5. Exercise submissions use the repository’s supported `contains_all` grader and are therefore only basic static pattern checks. The exercise content explicitly requires human verification; no secure arbitrary-code runner is provided by this patch.
6. No XP override fields were added. Course import and XP awards continue to use the current CodeLeaf importer/backend rules.

## Current state

Generated files are drafts. Inspect them, validate them, run the importer in dry-run mode, manually review lessons/assessment keys, then publish using the instructions in `PATCH-INSTRUCTIONS.txt`.
