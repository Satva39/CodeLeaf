# Next.js curriculum review notes

- Source: `NextJS(1).pdf` (54 pages), sections A–G reviewed on 2026-10-18.
- Syllabus mapping: all 24 modules and all 268 numbered Section B topics are represented as separate lesson files; every lesson preserves its listed subtopics.
- Practice: all 26 Section C exercises are represented as separate exercise files and linked from their target lessons. Each has a protected repository-only solution outline and static marker checker.
- Projects: all 10 named projects plus the production-style multi-vendor marketplace capstone in Section D are represented by separate project briefs, actual starter page/readme files, and protected reference architecture outlines.
- Assessment: a 60-item draft final exam blueprint is present; lesson-level question sets each contain three protected questions.
- Specialist coverage: Section E topics and five optional learning tracks are preserved in `references/advanced-specializations.json`; Section F learning stages are included in course metadata.
- Visuals: one overview SVG per module and one SVG concept map per lesson are included and described in `assets/asset-manifest.json`.
- Primary path: JavaScript/JSX only. No TypeScript source files have been added.
- Status: draft. Do not publish without instructor review of the explanations, code snippets, exam distractors, accessibility, and version-specific details.

## Version review

The official Next.js docs checked on 2026-10-18 document the Next.js 16 convention `proxy.js` (renamed from middleware) and the Cache Components model enabled by `cacheComponents`. Caching defaults and experimental features are explicitly version-sensitive. The official installation docs state Node.js 20.9 as the minimum.

## Execution and security limitations

CodeLeaf's content validator can verify the file tree, stable IDs, relationships, XML-valid SVGs, and supported grading config. It does not execute arbitrary learner JavaScript or prove runtime correctness. Coding exercises use a static marker check only and require separate local tests/human review. Database/auth provider integrations, real external services, production deployment, and multi-user isolation have not been run by this course generator.
