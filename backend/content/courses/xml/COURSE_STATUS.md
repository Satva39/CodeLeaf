# XML course status

- Course slug: `xml`
- PDF inspected: `XML.pdf` (38/38 pages rendered and visually reviewed in contact sheets; searchable text parsed)
- Modules: 21
- Lessons: 176 (all numbered lesson topics 1–176 retained)
- Exercises: 18 (all Section C exercises)
- Projects: 9 (eight listed projects plus capstone)
- Assessment blueprints: 1 (with four separate draft question pools)
- Lesson knowledge checks: 176 sets, 3 questions each
- Visual assets: 198 original SVGs (21 module overviews + 176 lesson diagrams + 1 roadmap)
- Publication status: all draft

## Remaining before publication

1. Have an XML specialist review lesson-specific examples and assessment answers against the chosen XML/XSD/XPath/XSLT/XQuery processors.
2. Expand processor-specific checks using the exact XSD/XSLT/XQuery implementations CodeLeaf intends to support. Local checks used lxml to validate one DTD, three XSD instance/schema pairs, and two XSLT transformations; this does not prove compatibility with every processor or all XSD 1.1 / XPath 3.1 / XSLT 3.0 features.
3. Run the full backend test suite and local Vite build in the target development environment. Selected API-contract, knowledge-check, and XML starter-route tests passed, but not every repository test was run. A Vite build attempt in the authoring Linux sandbox could not complete because the supplied `node_modules` lacks `@rollup/rollup-linux-x64-gnu` (the packaged dependencies appear to be for another platform); retry after `npm ci` on the target machine.
4. Configure a compatible XML toolchain if live execution is required; this patch intentionally does not add arbitrary XML execution to the main API/production web process.
5. Publish only reviewed modules/lessons/projects/question sets through the existing import workflow.
