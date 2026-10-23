# PHP curriculum review notes

Reviewed on 2026-10-11. Source: `PHP.pdf` (48 pages). The PDF was text-extracted and all pages were rendered into a visual contact sheet to inspect the layout and check for missed diagrams/tables.

## Coverage accounting

- Source course overview and learning outcomes: captured in `course.json`.
- Complete numbered curriculum: all 290 numbered lesson topics across 28 modules are represented, in the source order, by one lesson file each. See `syllabus-map.json` for the one-to-one mapping and the preserved subtopic lists.
- Section C: all 30 practical exercises are represented as separate exercise JSON files, each with learner prompt, starter, acceptance criteria, test cases, a protected solution file, and explicit human-review status.
- Section D: all 10 projects and the Clipcart-style multi-vendor e-commerce backend capstone are represented as separate project files with milestone checklists, a 100-point rubric, test/review criteria, and protected reference outlines.
- Section E: all optional specialization headings and their listed topics are represented in `references/learning-roadmap.json`; these pathways are optional rather than prerequisites for the core course.
- Section F: all nine learning phases and the dependency guidance are represented in the roadmap.
- Section G: its technical quality requirements are included in the publication checklist below.

## Version and technical review

The PDF specifies PHP 8.5.x as the curriculum baseline. The official PHP release listing available during this review identifies PHP 8.5.10 as the latest verified 8.5 patch release; re-check the PHP supported-versions and releases pages before publishing because patch releases change. The local validation runtime available during content generation is PHP 8.4.x, so the examples were intentionally kept syntax-compatible with PHP 8.4 and are linted locally; this does not substitute for a full PHP 8.5 runtime review. Examples requiring a framework, database driver, extension, or external provider are labeled for static inspection/local setup and are not claimed as integration-tested.

## Corrections, cautions, and exclusions

- No numbered topic from 1–290 was intentionally excluded. Topic titles, order, and listed subtopic terms are preserved from the supplied PDF.
- The PDF's stated PHP 8.5.x version scope is retained, with the latest patch verified at review time recorded explicitly instead of implying the version will remain current.
- Composer, Laravel, Symfony, PHPUnit, static-analysis tools, and optional advanced specializations are documented with official references, but their compatible versions must be rechecked at publication.
- Section E subjects (for example fibers, event-driven runtimes, CMS platforms, cloud infrastructure, and advanced database engineering) are kept in separate optional pathways rather than expanding the core numbered modules.
- Security examples teach parameterized SQL, password hashing, contextual output escaping, CSRF protection, safe upload handling, authorization, and secret management. They are educational patterns, not a substitute for application-specific security review.
- Exercise `grading_config` uses a shallow source-token check only because the existing CodeLeaf exercise grader supports `choice`, `exact_text`, and `contains_all`. All code exercises remain draft and require human review or a secure isolated runner; token checks do not prove that PHP code behaves correctly.
- All knowledge-check question sets are marked `protected_content_repository_only`. GET responses omit answer keys and explanations; POST responses disclose feedback only for submitted questions. The final exam blueprint is draft, and certificate issuance must continue to depend on backend-verified passing results.

## Publication checklist (from Section G)

- [ ] Run every example under the selected maintained PHP 8.5 patch release.
- [ ] Label version-specific syntax and verify migration/compatibility behavior.
- [ ] Confirm all database examples use parameterized input and appropriate transactions.
- [ ] Confirm password APIs, session settings, contextual escaping, upload limits, and file storage boundaries.
- [ ] Confirm production error responses do not expose stack traces or secrets.
- [ ] Verify Composer lockfile/autoload guidance and current PSR status.
- [ ] Review every exercise's acceptance criteria and grading strategy.
- [ ] Complete all project security/test reviews and check the capstone's transaction/idempotency behavior.
- [ ] Review framework version support and distinguish optional specialization from core PHP requirements.
- [ ] Keep legacy APIs clearly marked and explain migration alternatives.
- [ ] Confirm the real knowledge-check/final assessment workflow before publishing learner-visible assessment content.

## Integration notes

The existing importer and backend schema already support directory-based course content, modules, lesson JSON, exercise JSON, projects, course assets, and protected solution files. This patch reuses that model. No database migration, hosting provider change, dependency change, or environment-variable addition is required. PHP code is displayed in static-validation mode; arbitrary learner execution remains a separate isolated-runner concern.
