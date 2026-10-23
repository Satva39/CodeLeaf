# Angular curriculum review notes

**Source syllabus:** Angular — Complete Learning Curriculum, 59-page PDF supplied for this run. Parsed Section B contains 26 module headings, 349 numbered main topics and 1378 numbered subtopics. Every main topic and its extracted subtopics are represented in `references/complete-syllabus.json` and linked lesson files.

**Technical source check:** Official Angular version, release, template, signals, forms, routing, HTTP, testing, SSR, hydration, security, accessibility, CLI and update documentation was checked on 2026-10-14. The indexed links and version assumptions are in `reference-index.json`. Keep this review date and version assumptions updated before publishing.

## Corrections and compatibility notes

- **Version baseline verified:** the PDF's statement that Angular v22 is active and v21 is LTS matches the official Angular release schedule checked on 2026-10-14. Angular's official compatibility table, rather than a universal Node/TypeScript recommendation, should be used for the specific framework minor selected at install time.
- **Signal Forms:** included in the syllabus but labeled as a modern, version-gated path (Angular v22+ in the current reference set). Template-driven and reactive forms remain core approaches for existing apps.
- **Zoneless change detection:** taught with compatibility notes because defaults differ by Angular major; official guidance identifies zoneless as the default from v21 onward.
- **Animations:** `animate.enter` and `animate.leave` are the modern focus. Legacy `@angular/animations` APIs remain useful for maintaining and migrating existing applications; verify current deprecations rather than presenting legacy APIs as the default for new projects.
- **“Error boundaries”:** interpreted as feature-boundary error handling and resilient fallback UI, not as a claim that Angular provides a direct React-style built-in error-boundary component.
- **Resources and reactive HTTP resources:** retained with version/stability warnings. Confirm the exact API surface against documentation for the pinned Angular version before publication.
- **Legacy syntax and NgModule architecture:** retained for maintenance and migration; modern standalone APIs and built-in control flow are the primary learning path.

## Exclusions

No numbered main topic from Section B was excluded. Topics 1–349 and their extracted subtopics are retained. The 48 practical exercises, 13 project briefs (12 projects plus the capstone), roadmap and six specialization paths follow Sections C–F. The exam is a draft blueprint; the patch does not claim a live exam attempt system or certificate issuance.

## Publishing gates

Review source snippets with a pinned Angular CLI/Node/TypeScript version, run the matching test target, verify accessibility in a browser and screen reader, examine security-sensitive flows with the backend, and reconcile all version-dependent APIs. All authored content is intentionally `draft` until that review is complete.
