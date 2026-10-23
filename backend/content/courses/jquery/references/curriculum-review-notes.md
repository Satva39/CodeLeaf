# jQuery curriculum review notes

**Source:** `jQuery(2).pdf` (45 pages), visually reviewed as rendered page contact sheets and text-extracted for topic inventory on 2026-10-12. **Course status:** draft, not published.

## Coverage preserved

- Section A overview, prerequisites, intended audience, outcomes, version baseline, and Core-versus-ecosystem scope.
- Section B: all **22 modules** and topics **1–193**, kept in the source numbering and ordered topic titles. The module 1 heading is visible in the page image but was omitted from extracted text; its title and grouping (topics 1–8) were preserved from page 2's rendered image.
- Section C: beginner, intermediate, and advanced exercise themes. The course additionally links a practical exercise to every main lesson so each core concept has an individual practice opportunity.
- Section D: all 12 progressive projects and the capstone (13 total), each with milestones, a 100-point rubric, starter files, and a protected reference plan.
- Section E specialist topics are tagged through optional, legacy, and professional lesson/module tracks rather than forced into core beginner exercises.
- Section F stage progression is represented by module order, prerequisites, lesson IDs, and previous/next edges.
- Section G coverage checks are represented by the module/lesson inventory, three protected knowledge-check questions per lesson, course reference index, and final exam blueprint.

## Current version baseline and source verification

The official jQuery Download page listed **jQuery 4.0.0** as the latest version when checked on 2026-10-12. The official release article is dated 2026-01-17 and the official 4.0 upgrade guide is the primary reference for breaking changes. All course items remain draft pending a human technical review and actual local test.

## Corrections, clarifications, and scope handling

1. **Removed APIs are migration material, not current recommendations.** The jQuery 4.0 release removed helpers including `jQuery.trim`, `jQuery.isArray`, `jQuery.parseJSON`, `jQuery.type`, `jQuery.now`, `jQuery.isNumeric`, `jQuery.isFunction`, `jQuery.isWindow`, `jQuery.camelCase`, and additional legacy/internal methods. Current examples use native equivalents such as `String.prototype.trim()`, `Array.isArray()`, `JSON.parse()`, and `Date.now()` where relevant. Confirm a method against the upgrade guide before labeling it supported.
2. **Legacy event APIs are clearly marked.** `.bind()`, `.delegate()`, and `.live()` are migration examples only; current course examples use `.on()` and `.off()`.
3. **Build selection is explicit.** The official Download page says the slim build excludes AJAX and effects. Learners needing `$.ajax()` or built-in effects should choose the full build or intentionally provide alternatives.
4. **DOM readiness follows current convention.** Examples use `$(handler)`/`$(function () { ... })`. Older readiness forms are discussed for maintenance without presenting them as the preferred new-code pattern.
5. **AJAX security boundaries are clarified.** jQuery cannot implement server authorization or fix server CORS configuration. Sensitive endpoints still need server-side authentication, authorization, validation, appropriate CSRF defenses, TLS, and safe response handling.
6. **Client-side form validation is not a security boundary.** It improves feedback but all security-relevant fields must be validated on the server.
7. **Safe content rendering is emphasized.** `.text()` or DOM `textContent` is preferred for untrusted strings; `.html()` is shown only with trusted, constant markup. No attack payloads are needed to teach the defensive concept.
8. **Optional ecosystem tools remain optional.** jQuery UI and Widget Factory material requires a separately loaded compatible dependency; jQuery Mobile is kept as historical/legacy maintenance context. QUnit is a separate testing project, not jQuery Core.
9. **Course platform boundaries remain honest.** The API can import the course and serve per-lesson content/knowledge checks, but the final exam blueprint is a content specification only. Do not claim final exam session persistence, a deployed arbitrary-code runner, or certificate issuance until those are independently implemented and tested.
10. **All generated items stay draft.** Neither the package generation nor filesystem validation is a substitute for expert review, browser execution, accessibility checks, or deployment verification.

## Official references

- [Download jQuery](https://jquery.com/download/)
- [jQuery 4.0.0 release notes](https://blog.jquery.com/2026/01/17/jquery-4-0-0/)
- [jQuery Core 4.0 Upgrade Guide](https://jquery.com/upgrade-guide/4.0/)
- [jQuery API Documentation](https://api.jquery.com/)
- [jQuery Learning Center](https://learn.jquery.com/)
- [QUnit](https://qunitjs.com/)
- [jQuery UI / Widget Factory learning material](https://learn.jquery.com/jquery-ui/)

References checked on 2026-10-12. Check release notes again before publishing or recommending a different version.
