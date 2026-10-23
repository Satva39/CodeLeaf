# FastAPI curriculum review notes

Reviewed on 2026-10-19. Source: the supplied `FastAPI.pdf` (39 pages).

## Source coverage

- Section A: audience, prerequisites, outcomes, ecosystem and the PDF estimate of 8–14 weeks at 6–10 hours/week.
- Section B: all 22 modules, lessons numbered 1–144, and their decimal-numbered subtopics were parsed from the PDF text. Module titles and lesson titles are retained in order.
- Section C: all 28 practical exercises mapped to related lesson IDs.
- Section D: 10 progressive projects and the “Production-Ready E-Commerce Backend” capstone; all 11 briefs are included separately.
- Section E: all ten specialist tracks are represented as optional paths rather than core prerequisites.
- Section F: the six-stage roadmap and PDF prerequisite relationships are recorded in `syllabus-map.json`.
- Section G: cross-checks are represented by the source sequence and validation checks.

## Technical/version notes

1. The PDF recommends the current official setup flow using `uv` and `fastapi[standard]`, while also documenting `pip`. Examples use Pydantic v2 conventions and assume Python 3.10+; verify installed versions before publication rather than treating this as a dependency lock.
2. Current FastAPI guidance uses a lifespan context manager for managed startup/shutdown resources; older `on_event` patterns are considered deprecated in current documentation.
3. `fastapi dev` is for development with reloading. Production commands, workers, binding and environment variables must match the deployment host.
4. `async` helps when waiting on asynchronous I/O; CPU-bound operations generally need appropriate offloading, and durable work may require a separate worker/queue.
5. OAuth2/Bearer snippets show request-security wiring only, not a complete authentication system. Production systems must verify token signature, issuer/audience, expiry and authorization claims; passwords require appropriate password hashing, and user/role policy needs tests.
6. Static exercise graders look only for required text; they do not execute Python, database SQL, WebSockets, HTTP calls, or security checks. Those exercises remain draft and require targeted tests/human review.
7. Question answer keys and project/exercise reference outlines remain under the backend content tree with repository-only/draft markers. Verify deployed assessment access control before publishing; no frontend/static exposure is intended.
8. Every module/lesson/project/exercise remains `draft`. Filesystem validation is not a substitute for reviewing each snippet, running real integrations, passing security review or verifying a live deployment.

## PDF discrepancy/exclusion record

- No numbered module, numbered lesson title, Section C exercise, Section D project, or Section E specialist track was intentionally excluded.
- Vendor wordmarks/ornamental visual annotations in the PDF were not copied; the course uses original diagrams and the PDF's own written syllabus as the structural source.
- The attached PDF does not supply pinned FastAPI/Pydantic versions, an actual runner specification, credentials, or verified application test outputs. Those are intentionally not invented.
