# Ruby course status

- Course slug: `ruby`
- PDF: `Ruby.pdf` (55 pages)
- Source numbered lessons covered: 304 / 304
- Modules: 28 / 28
- Practical exercises from Section C: 28 / 28
- Projects from Section D: 12 / 12
- Knowledge-check sets: 304, 3 questions each = 912 draft questions
- Final assessment blueprint: 1 draft blueprint with 30 draft questions
- Visual assets: 333 original SVGs (1 course roadmap, 28 module overviews, 304 lesson diagrams)
- Publication status: **DRAFT / REVIEW REQUIRED**

## Done in this patch

- Each syllabus lesson is an independent JSON file with a stable ID, module relationship, previous/next links, prerequisite references, outcomes, explanation blocks, code example/result, troubleshooting, try-it-yourself prompt, reset instructions, sources, and a linked knowledge-check set.
- Every module includes a dedicated overview SVG. Each lesson has its own concept diagram. Exercise and project solution outlines are kept in repository-only files.
- Reference list, learning roadmap, module/lesson index, specialist tracks, source review notes, and individual asset checklist are included.
- No XP overrides were added. No backend schema, API, importer, gamification, deployment, or dependency files were modified.

## Required before publication

- Human technical review of all code examples, especially version-sensitive topics, I/O, database, web-framework, concurrency, security, JIT, and native-extension lessons.
- Validation performed here: all **304 Ruby snippets passed `ruby -c`** using the available Ruby 3.3.8 runtime; **173 snippets from Modules 1–16 were also executed** without runtime exceptions (one intentionally unsafe monkey-patch sample was skipped). The examples were not functionally executed across all modules, the course baseline is Ruby 4.0.7, and version/gem-specific behavior still needs review on the target runtime.
- Review static required-token grading or replace it with a Ruby-aware isolated runner/human review before enabling coding exercises.
- Review all quiz answers, exam questions, project requirements, and protected solution outlines.
- Test importing into a non-production PostgreSQL database and inspect the catalog/lesson routes in draft-preview mode.

## Known platform boundary

The existing CodeLeaf app supports course content via manifests/import and its current playground only previews HTML/CSS/JavaScript. Ruby execution is not available in this patch. Do not run arbitrary learner Ruby code inside the FastAPI service.
