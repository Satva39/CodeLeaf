# Curriculum review notes — Vue.js

## Source coverage

The attached `Vue.pdf` has 34 pages. All pages were text-extracted, and a visual contact sheet of the full document was inspected to check its page composition, syllabus tables, project thumbnails, learning path, advanced topic matrix, and final coverage checklist. Section B contributes 20 modules and 152 main lesson headings. Sections C–G contribute 23 practical exercises, eight progressive projects plus one capstone, specializations, a five-stage roadmap, and the coverage checklist.

## Source corrections and handling

- The last syllabus topic repeats “152.5 Following framework changes responsibly”; the duplicate is represented once.
- Vue 3 is the main track. Official Vue docs are the baseline, and API/tooling details must be rechecked against the target runtime at publication. `defineModel()` requires Vue 3.4+, deferred Teleport behavior requires an appropriate newer Vue runtime, and Suspense/version-sensitive topics are identified for review.
- Vue 2 is treated as legacy; the official Vue EOL notice says it reached end of life on December 31, 2023. Vue CLI is retained as legacy/maintenance knowledge, while create-vue/Vite is the default setup path for new work.
- TypeScript remains a recommended specialization because the PDF includes it, but it is reference-only: this patch adds no `.ts`/`.tsx` files or TypeScript dependencies.
- The Vue logo, third-party labels, and project screenshots in the PDF were not copied into the course. All included teaching visuals are original generated SVG diagrams.

## Editorial and technical distinctions

- **From the PDF:** 20-module / 152-lesson course structure, exact lesson titles/subtopics, 23 named exercises, project progression, optional/specialist matrix, learning roadmap, and coverage checklist.
- **Verified against official docs:** Vue template/reactivity/component/composable guidance; Vue Router route guards/lazy loading; Pinia; Vitest/Vue Test Utils; security, performance, SSR; Nuxt/Vite tooling; Vue 2 EOL. Official source URLs and date checked are in `reference-index.json` and each lesson’s `sources`. Checked date: 2026-10-17.
- **Editorial recommendation:** all generated content stays `draft`; every lesson includes outcomes, topic explanations, an inspectable code/config example, expected result, local run/reset guidance, hints, mistakes, recap, accessibility/version notes, and a protected three-question knowledge check. The 40 exercises include all 23 exercises named in the PDF plus 17 reinforcement exercises to give every module a practice opportunity.

## Platform integration

- The supplied project already contains a `vue` catalog slug, a generic course API, a content-directory importer, protected lesson question-set handling, project listing, and asset serving.
- This patch only adds `backend/content/courses/vue/` and root-level instructions/report files. It makes no frontend, backend source, DB schema, dependency, deployment, or environment changes.
- The existing exercise endpoint supports only choice, exact-text, and case-sensitive contains-all text grading. The Vue exercises explicitly disclose that marker checks do not execute code or prove correctness; keep the course draft until stronger graded tests or a human-review workflow exists.
- `--apply` imports course/module/lesson/exercise records as draft. Question banks, projects, and visuals remain repository-backed. Publishing must follow manual review and updating the file-level statuses; the CLI `--publish` flag alone does not promote JSON question/project statuses.

## Validation caveat

Static file validation checks JSON syntax, required lesson fields, unique referenced IDs, lesson/module relationships, exercise grading configuration, protected solution references, question-set relationships, project rubric totals, asset paths, and SVG XML. It does not prove that every code excerpt works in every target Vue/Nuxt runtime, does not run browser/SSR/E2E tests, and does not validate a production database deployment.
