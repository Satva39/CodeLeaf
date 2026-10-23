# C# Course Status

- **Course slug:** `csharp`
- **Status:** Draft — not safe to publish without technical and educational review.
- **Source:** `C#(1).pdf` (50 pages), all sections A–G reviewed.
- **Coverage:** 25 modules, 195 lessons, 30 formal exercises, 9 project artifacts (8 staged projects + 1 capstone), 195 knowledge-check files with 3 questions each (585 questions).
- **Visual assets:** 43 original SVG diagrams (25 module maps + 18 lesson-level diagrams).
- **Execution mode:** `static-validation`. CodeLeaf currently has no C# runtime; examples need local .NET verification.
- **Database changes:** None. Existing directory importer and SQLAlchemy tables support the course structure.
- **Frontend changes:** None required for catalog registration; `frontend/src/data.js` already has the `csharp` catalog entry.

## Remaining before publication

1. Compile/review all code examples with the .NET 10 SDK; special attention is required for package, test-framework, JSON, async, expression-tree, unsafe, and version-specific examples.
2. Review lesson explanations, answer keys, exercise tokens, protected solution outlines, project rubrics, and the final assessment.
3. Replace/expand project solution outlines into fully compiled reference implementations where appropriate.
4. Re-run the validation and importer dry-run after any edits.
5. Change authored `status` fields to `published` only after review; then import with `--apply --publish`.

The included project starters are brief scaffolds and the solution documents are outlines, not complete production apps. This status deliberately does not claim an actual C# build, database import, deployment, or live exam execution.
