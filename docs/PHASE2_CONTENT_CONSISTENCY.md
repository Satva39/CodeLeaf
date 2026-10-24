# Phase 2 — Course and content consistency

## Included in this increment

- Course overview remains a tutorial-specific experience: the “Who this is for”, “Prerequisites”, “Learning outcomes”, and “Course outline” sections only render when the Tutorials course landing page opts into `showLearningSections`.
- Reference, project, and practice pages use the compact shared course header and do not request a tutorial outline just to display their collection header.
- The tutorial overview has a clearly visible Start Learning action, separate course-fit cards, and an accessible, single-open module preview.
- Reference entries share one detail layout across courses. The renderer preserves authored explanations/examples, derives a clearly generic practical workflow only when the source entry lacks one, tokenizes the supplied topics, and matches related lesson suggestions against the selected course outline.
- Reference source links are rendered only for `http:`/`https:` URLs. Related lesson links use the actual outline slugs.
- Reference detail card width uses the available content width. No existing CSS entry-point file is replaced; component-local stylesheet imports preserve previously existing global imports.
- A new test checks course route registration, tutorial-only sections, catalog publication mapping, reference matching, and safe external URLs.

## Deliberately not changed

- No Neon/production database rows are changed.
- No course manifest publication statuses are modified.
- No `.env`, secret, credential, Vercel or Render environment settings are changed.
- This increment does not claim that generic reference guidance is an individually researched technical explanation. Existing authored entry content is preserved; generated fallback text is contextual guidance built only from the entry metadata and should be reviewed over time.

## Acceptance checks

From `frontend/`:

```powershell
node scripts/test_phase2_content_consistency.mjs
node scripts/test_reference_details.mjs
node scripts/test_course_catalog_filters.mjs
node scripts/test_course_overview_cta.mjs
npm run build
```

Also smoke-test a tutorial course page, one HTML reference detail, one non-HTML reference detail, one Projects page, and one Practice page at desktop and mobile sizes. References/projects/practice should not display the tutorial-specific detail cards or outline.
