# FastAPI course status

- Course status: **draft** (all modules, lessons, exercises, projects, questions and solutions are draft).
- Source: `FastAPI.pdf`, 39 pages, visually reviewed after rendering.
- Parsed: 22 modules; 144 numbered lessons; 783 subtopic lines; 28 Section C exercises; 11 project briefs (10 projects + 1 capstone); 1 final assessment blueprint with 36 questions; 3 learner-facing knowledge checks for each lesson.
- Visuals: 166 original SVGs (22 module overviews + 144 lesson diagrams), 1200 × 675, 16:9.
- Content authoring files are separated by course/module/lesson/exercise/project. The existing CodeLeaf importer/validator is the integration boundary; no app code, schema, dependencies, frontend routes, or deployment configuration changed.
- Examples are instructional artifacts. CodeLeaf does not execute Python/SQL/shell examples in the lesson view; exercises rely on static smoke checks and human review until a separate isolated runner/stronger grader exists.
- Existing API contract and protected-knowledge-check test scripts passed using temporary SQLite fixtures. A PostgreSQL/Neon import (`--apply`), external integration tests, frontend build and deployment were not run. See the root patch validation report.
- Before publishing: run all snippets against a supported version matrix, review auth/webhook/file-upload examples, verify exam/answer-key API protections, improve static graders into structured tests where supported, then publish through the reviewed workflow.
