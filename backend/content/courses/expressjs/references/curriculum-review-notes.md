# Express.js curriculum review notes

## Source inspected

- `ExpressJS.pdf`: 45 pages. Extracted the full text, rendered all 45 pages to images and reviewed three contact sheets. Pages 36–41 containing the Section D project-roadmap illustrations were rendered at higher resolution; those images were used only to understand the supplied examples and were not copied into CodeLeaf assets.
- The complete Section B structure is preserved as 20 modules and 184 continuously numbered lessons. The 30 Section C exercise briefs and all 11 Section D progressive projects plus the capstone are kept as independent files. Section E optional topics and Section F learning stages/prerequisites are captured under `references/advanced-specializations.json` and `references/learning-roadmap.json`.

## Version and correctness decisions (checked 2026-10-19)

1. **Runtime recommendation updated:** the PDF states that Express 5's migration guide requires Node.js 18 or higher. That is a minimum compatibility statement, not a recommendation to deploy an end-of-life runtime. This course recommends a currently supported Node.js LTS line (Node.js 24 LTS as shown in the official release schedule on 2026-10-19); re-check the release table before publishing.
2. **Express 5 path syntax:** route wildcards are named. Use `/*splat` for non-root paths and `{*splat}`-style brace syntax (`/{*splat}` in source code) when the route should also match `/`; older Express 4 wildcard patterns should be treated as migration work. The lesson example uses `/{*splat}` to represent a root-inclusive route and should still be run in a local lab before publication.
3. **Promise error forwarding:** Express 5 forwards rejected promises returned by route handlers/middleware. The course does not teach this as a guarantee for detached/unreturned promises or callbacks outside the handler's promise chain.
4. **Framework versus ecosystem:** database drivers/ORMs, schema validators, password-hashing libraries, sessions, JWT libraries, Helmet, CORS middleware, Multer, rate limiters, testing clients, OpenAPI tools and background queues are third-party technologies. Content labels them as packages/integrations rather than built-in Express features.
5. **CORS is not access control:** allowlists and preflight/credential behavior are covered separately from authentication and per-resource authorization.
6. **Static grader limitation:** the existing CodeLeaf exercise grader supports choice, exact text and required-string checks. The 30 Express practice exercises use required-string smoke checks plus explicit human/local runtime review; these graders do not execute Node.js, and their `status` is draft.
7. **Node execution:** the current lesson reader can show code and a reference output but does not run arbitrary Node.js code. Express examples are marked `execution_mode: server-runner` and `run_mode: static-validation`; learners must copy/run them locally unless a separate isolated runner is implemented later. No arbitrary code execution service was added.
8. **Publication and assessment:** all authored course/module/lesson/exercise/project/knowledge-check files are `draft`. The exam JSON is a blueprint, not a claim that a separate randomized exam-attempt system or certificate issuance flow exists. Publish only after review, local runs, security review and answer-key checks.

## PDF coverage inventory

- Section A: audience, prerequisites, outcomes, version baseline and estimated 10–16 week learning window captured in `course.json`.
- Section B: all 20 modules, all 184 numbered topic titles, and extracted subtopics appear in individual module and lesson JSON files.
- Section C: all 30 hands-on exercise briefs map to lesson IDs; reference answers are stored outside learner-facing lesson/exercise instructions.
- Section D: Developer Information Website, Task Manager API, External Data Explorer, Inventory Management Backend, Authentication Service, Document Management API, Online Bookstore API, Monitoring and Observability Service, Order and Payment Backend, Multi-Service API Backend, Multi-Tenant Administration API, and the Production-Ready Commerce Platform API capstone each have separate project files.
- Section E: seven advanced/specialization areas plus legacy boundaries captured as an optional-path index.
- Section F: six learning stages and the prerequisite map captured as structured roadmap data.
- Section G: coverage and publication readiness summarized here and in `EXPRESSJS-VALIDATION-REPORT.md` at the patch root.

## Not claimed as complete

This content package provides the complete draft syllabus structure, original SVG visuals, examples, assessments, exercise blueprints and project briefs. It does not prove every sample ran against a live Express 5 install, does not include a production Node.js sandbox, does not connect to live payment/identity providers, and does not deploy the course. Local runtime smoke tests and a human technical review are required before publication.
