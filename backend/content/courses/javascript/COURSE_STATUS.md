# JavaScript course status

**Status: DRAFT — generated content requires technical/editorial review before publication.**

- Source PDF inspected: JavaScript.pdf (56 pages).
- Source syllabus topics preserved: 302 (numbered 1–302).
- Modules: 28 (27 source modules + 1 supplemental control-flow module).
- Lessons: 312 (302 source topics + 10 supplemental lessons).
- Practical exercises: 36 separate files, with protected repository-only reference solution files.
- Projects: 13 separate briefs, plus protected reference planning files.
- Knowledge-check files: 312 sets × 3 draft questions = 936 questions.
- Visual assets: 340 SVGs (one module overview per module and one visual per lesson).
- Exam blueprint: one; actual exam delivery, grading sessions, and certificate issuance are not implemented by this content patch.
- XP: no course-authored XP fields or overrides; platform's existing server-side policy remains authoritative.
- Execution: lesson snippets are inspectable/static-validation examples with local run instructions; no isolated arbitrary-code runner was found/added.
- Deployment/backend/frontend configuration: unchanged.

## Required review before publication

1. Review all lesson expansions and verify every code sample in its intended runtime.
2. Replace or strengthen token-only grading with behavioral tests and/or human review.
3. Verify protected question/solution content is never returned by public API routes.
4. Review accessibility, compatibility, Node.js release choice and the use of emerging APIs.
5. Only publish after review and a successful validated import in a configured PostgreSQL environment.
