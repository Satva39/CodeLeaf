# Swift course generation status

- Course slug: `swift`
- Source: supplied `Swift.pdf` (51 pages), with visual review of all rendered pages/contact sheets.
- Reference baseline: Swift 6.4 (official release date checked: 2026-09-15).
- Publication state: **draft / not approved for publication**.

## Generated inventory

- Modules: 22
- Lessons: 261
- Per-lesson knowledge-check sets: 261
- Questions in per-lesson knowledge checks: 783
- Final exam question bank: 60 questions
- Lesson-linked practice exercises: 261
- Additional PDF-mapped practice challenges: 46
- Total exercises: 307
- Projects including capstone: 12
- SVG visuals: 32
- Main curriculum lesson range: 1–261

## Validation results from the patch build

- CodeLeaf strict content-tree validation and importer dry run passed; no database changes were made.
- All 261 lesson code snippets parsed using host Swift 6.2.1. 243/261 type-checked on Linux; the 18 SwiftUI snippets require an Apple SDK and were not type-checked here.
- All 12 project starter files and all 12 protected core-logic reference snippets ran successfully on Swift 6.2.1 Linux.
- All 32 SVG assets rendered and were visually inspected; the changed plain JavaScript files passed `node --check` and the changed Python file passed syntax parsing.
- The Vite production build was not run because dependency installation (`npm ci`) did not complete in the build runner.

## Important test boundary

This patch does **not** add a Swift compiler or a secure Swift sandbox to CodeLeaf. Lesson examples use `static-validation` display mode. Re-test with Swift 6.4, verify SwiftUI in a compatible Apple SDK, run `npm ci`/`npm run build`, and review the domain-specific lessons, exercise grading and protected answers before publication.
