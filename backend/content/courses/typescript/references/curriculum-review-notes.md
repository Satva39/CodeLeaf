# TypeScript curriculum review notes

Review date: 2026-10-14

## Source coverage

The supplied 40-page PDF was rendered for visual inspection and its text was extracted for structured comparison. The numbered curriculum in Section B covers topics **1–239 across 26 modules**. Section C lists **30 exercises**. Section D lists **9 named projects** plus a separately described **Production-Ready TypeScript Platform** capstone. Sections E–G describe specializations, six learning stages, dependency guidance, and quality/publishing checks. All of those sections are represented in the course files.

The Module 3 heading on PDF page 4 is visible in the rendered page but is not present in the extractable text layer. It was read from the page image as **JavaScript Foundations for TypeScript**; its nine lessons (15–23) are preserved.

## Version accuracy and clarifications

- The PDF says TypeScript 7.0 is available as of October 2026. This was checked against the official TypeScript team's [TypeScript 7.0 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) dated July 8, 2026. The course therefore treats TypeScript 7.0 as its primary version scope, not as an unverified future proposal.
- The official [TypeScript 6.0 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/) describes 6.0 as a bridge release. The course teaches migration through deprecation diagnostics and tests rather than assuming an in-place upgrade is effortless.
- The official 7.0 announcement identifies its native Go implementation and notes that the TypeScript 7.0 package does not ship a compiler API at 7.0; tools needing the compiler API should follow the official compatibility guidance. This nuance is included in release/migration material.
- The advertised compiler speed-up is an overall project-reported result, not a guarantee for every project or hardware configuration. Learners are asked to measure before/after performance instead of claiming a fixed multiplier.
- TypeScript's type declarations are primarily compile-time checks and do not validate arbitrary JSON or other external data at runtime. The course repeats this distinction at API, file, storage, security and deployment boundaries.
- The syllabus mentions `node16`, `nodenext`, and `node20` module modes. The course tells learners to use only modes supported by the installed compiler and to match configuration to the actual Node.js/bundler version; it does not assert that each named mode is supported by every TypeScript version.
- Decorators are version-sensitive. Modern standard decorators and legacy experimental decorators are presented as different models; learners must verify the target compiler/runtime/tooling combination.

## Content-generation boundaries

- All lessons, exercises, projects, questions and visuals are draft. They must not be published without a human technical review.
- TypeScript lesson code in this course is static text. The current CodeLeaf playground executes only sandboxed HTML/CSS/JavaScript previews, not TypeScript, Node.js, React/TSX, shell, or arbitrary user code. The lesson metadata labels examples as `static-validation`; local compiler/test instructions are provided where appropriate.
- Exercise graders use the existing server-side `contains_all` token grader. It confirms the presence of required source fragments, not TypeScript syntax, type correctness, runtime output, or security. The exercises explicitly state that this is not a compiler or code runner; final review remains human-led until an isolated TypeScript grader exists.
- XP is not authored in course files. Existing platform rules own 20 base XP per successfully completed lesson or correctly graded exercise and the plan multiplier, with server-side idempotency. The importer is used in draft mode until review.
- Answer keys and exercise/project solution files are stored as protected repository content. Existing API routes omit lesson answer keys in question payloads and do not expose JSON through the course-assets endpoint. Keep the course un-published until access-control tests are run against a configured local DB/API.

## Recommended pre-publication review

1. Run the filesystem validator and importer dry-run.
2. Set up a clean local TypeScript project at the chosen TypeScript 7.0-compatible tooling versions and compile examples by environment. Review and correct any snippet that requires a runtime or dependency.
3. Run the database import in a development database with draft content, then verify outline, lesson and knowledge-check APIs and confirm answer keys are not returned.
4. Verify duplicate lesson/exercise XP idempotency using the existing tests and a development user; course content must not override the platform's rules.
5. Conduct accessibility review of rendered SVGs and responsive lesson pages, a full technical editorial pass, and a security review before setting any status to published.
