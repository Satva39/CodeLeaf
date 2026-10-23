# CSS Course Status

- Source PDF: `CSS.pdf` (57 pages); all seven sections and embedded page visuals were reviewed.
- Coverage: 25 modules, 256 numbered lessons, and 1,344 numbered subtopics are preserved in individual lesson files and `syllabus-map.json`.
- Practice: 24 named exercises and 10 project briefs, including the commerce design-system/storefront capstone.
- Knowledge checks: 256 separate protected question files with 3 questions each (768 questions total). They remain separate from the learner API and are **not a live exam engine** in the current application.
- Protected solutions: 24 separate exercise solution JSON files and 10 project reference bundles containing illustrative HTML/CSS. Exercise JSON contains no inline answer key; all solutions remain repository-only and draft.
- Visuals: 25 module overview diagrams and 20 lesson concept diagrams are actual SVG files indexed in `assets/asset-manifest.json`. All 45 are included; there are no pending image-generation placeholders.
- Source review: `references/curriculum-review-notes.md` records the one syntax correction (CSS comment delimiter), advanced-feature qualification, legacy-topic treatment, and implementation boundaries. No PDF syllabus topic was intentionally excluded.
- Publication state: **draft**. Generated lesson prose, sample code, answer keys, compatibility claims, and grading criteria still require subject-matter review and browser QA. Do not publish solely because structural validation passes.
- Integration: The existing directory-based importer/database support course, module, lesson, exercise, and project-brief records. The question bank is stored as files; live exam runtime, certificate issuance, and project reference-solution delivery are not implemented by this patch.
- Gamification: Course files contain no XP override. The existing backend remains responsible for 20 base XP and the plan-specific 1.5× multiplier; database/concurrency behavior was not tested in this environment.
- Security: No `.env`, production credential, virtual environment, dependency directory, or database dump is included in the patch.
