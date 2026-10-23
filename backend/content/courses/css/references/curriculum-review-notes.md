# CSS curriculum review notes

Checked on **2026-10-11** against the attached 57-page `CSS.pdf` and current official documentation linked in `reference-index.json`.

## Coverage and preservation

- All 25 modules, 256 numbered lesson titles, and 1,344 numbered subtopics were retained in `syllabus-map.json` and the per-lesson files.
- All 24 named practice exercises and 10 project briefs were included, including the commerce design-system/storefront capstone.
- **No syllabus topic from the PDF was intentionally excluded.** Historical and legacy subjects remain available for understanding existing code, but lessons flag when they should not be treated as the default for new layouts.

## Corrections and editorial decisions

1. **CSS comments:** The PDF separates “single-line” and “multiline” comments as subtopics. CSS uses the same `/* ... */` comment syntax for both; it does not have a JavaScript-style `//` single-line CSS comment. The course teaches the actual CSS syntax and shows that a block comment can span one or multiple lines.
2. **Modern color notation:** The syllabus keeps named, hexadecimal, RGB/RGBA and HSL/HSLA notation, then extends to modern color spaces. Lessons may mention older function spellings for compatibility, while using current syntax when appropriate and consulting the CSS color reference.
3. **Support-sensitive features:** `@scope`, anchor positioning, scroll-driven/scroll-triggered animations, and newer container-query forms are treated as advanced or optional. Their lesson notes and official-reference links instruct learners to check support for their target browsers and retain a usable fallback. The course does not imply that every emerging feature is universally available.
4. **Legacy layout patterns:** Floats, multi-column behavior, and older layout approaches are retained because they appear in the syllabus and matter when maintaining existing sites. Flexbox, Grid, and normal responsive flow are taught as primary modern layout tools where appropriate.
5. **Assessment boundary:** The PDF’s assessment topics are represented as a blueprint and separate protected question files. The current CodeLeaf importer does not create a live exam runner from those files, so this is documented as pending integration rather than presented as a working exam feature.
6. **Protected answers:** Exercise reference answers and project reference HTML/CSS are separate repository-only solution files. They are not placed in the learner-facing exercise JSON or served as project API fields.

## Source-of-truth and review status

The PDF is authoritative for syllabus coverage. Technical explanations and original examples are instructional expansions, supported by the official MDN and W3C references in `reference-index.json`. The generated course remains **draft** until a CSS subject-matter reviewer checks the lesson text, code examples, references, browser support, exercise grading criteria, keyboard interaction, reduced-motion behavior, and narrow/wide viewport rendering.

## Official references used

- MDN CSS reference: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference
- MDN CSS comments: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Syntax/Comments
- W3C CSS Cascade Level 5: https://www.w3.org/TR/css-cascade-5/
- MDN CSS container queries: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries
- MDN CSS nesting: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Nesting/Using
- MDN scroll-driven animations: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations
- MDN scroll-triggered animations: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Animation_triggers/Using_scroll-triggered_animations
- W3C WAI WCAG 2.2 understanding documents: https://www.w3.org/WAI/WCAG22/Understanding/
w