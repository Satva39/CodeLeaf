# AWS Course Status

- **Status:** Draft / pending AWS-specific technical review.
- **Source inspected:** `AWS.pdf`, 57 pages.
- **Syllabus coverage:** 24 modules; all explicitly numbered lesson topics 1–285; 22 exercise briefs; 10 projects including the capstone; specialist paths, learning stages, quality checks and maintenance guidance.
- **Assessments:** 285 per-lesson knowledge-check sets with three questions each (855 total); one final exam blueprint. Answer keys are server-side repository files and the existing API contract exposes only questions/options to the learner.
- **Visuals:** 32 original SVG diagrams (24 module overview diagrams plus 8 concept diagrams), all referenced in the asset manifest.
- **Important source discrepancy:** The PDF claims 287 lesson identifiers in its overview/final note, but its complete numbered syllabus contains only IDs 1–285. This patch preserves the 285 defined topics without inventing 286–287.
- **Corrections:** AWS Data Pipeline is treated as legacy (new customer access closed July 25, 2024) and alternatives are noted. The Amazon Quick/Quick Sight terminology is clarified against current official docs. Budget alerts are never described as spending caps.
- **Not tested:** No live AWS service invocation, deployment, account billing, production API, real database import, credential flow, secure cloud runner, or certificate issuance was tested here. All content needs independent technical review before publication.
- **Next review:** Check all examples/commands against current docs and the target account/Region, review IAM/policy examples, perform selected read-only command tests using an approved sandbox, review exercise grading/answers, then selectively approve content before publishing.
