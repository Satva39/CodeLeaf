# PHP course status

- Course slug: `php`.
- Source PDF: all 48 pages reviewed; 28 modules and all 290 numbered curriculum topics mapped in source order.
- Content inventory: 28 modules, 290 individual lessons, 30 exercises, 30 protected exercise solutions, 11 project briefs, 11 protected project reference outlines, 290 separate knowledge-check files (870 single-choice questions), and one final-exam blueprint.
- Visual inventory: 43 included original SVG diagrams (28 module overviews and 15 focused diagrams), all 1200 × 500 (12:5, 2.4:1), with captions and alt text.
- Publication state: all generated course content, questions, exercise solutions, and projects are `draft`; no content is published by this patch.
- Validation: course schema/path/relationship validator passed; importer dry run passed; 360 PHP snippets passed `php -l` under local PHP 8.4.24; all 290 trusted lesson examples executed under PHP 8.4.24 and matched their expected output; all 290 lesson quiz output questions align with their lesson output; knowledge-check API tests passed; existing course API contract regression tests passed; changed frontend JSX parsed successfully.
- Version caveat: the target curriculum assumes PHP 8.5.x, while the local PHP runtime used for validation was 8.4.24. Recheck against the current PHP 8.5 patch release and review language/version-specific lessons before publication.
- Not run: a production Vite build (frontend dependencies were unavailable offline and registry installation did not finish), a PostgreSQL write/import, a Vercel/Render deployment, or PHP 8.5 runtime testing.
- Before publication: technically review lessons, examples, references, quiz answers and distractors, exercises and rubrics, project briefs, framework/tool versions, accessibility, and security. Independently verify assessment and certificate issuance paths.
