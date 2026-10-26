# CodeLeaf exam, exercise progress and certification upgrade report

**Snapshot:** uploaded `Code_Leaf(8).zip` (Git HEAD recorded inside that snapshot: `78872208fa8a2d03737ef3287cf395a5522ba3ac`, branch `master`).  
**Date:** 26 October 2026  
**Deployment:** none. No commit or push was made.

## Executive result

This update integrates the existing exercise progress, MCQ attempt and certificate paths instead of rebuilding the application. The UI changes are local and use the current page/button patterns. Backend checks are authoritative for prerequisites, MCQ scoring, practical assessment attempts and certificate issuance.

**This is not yet a release-ready certification catalogue.** The supplied content snapshot has 62 published courses; 34 have at least 80 structurally valid, distinct MCQ prompts under the audit rules, and 28 do not. **0 of 62 courses have a published practical-exam definition supported by the new deterministic text grader, so 0 courses are fully exam-ready.** The system intentionally leaves those exams unavailable. It does not duplicate questions to reach 80, simulate practical success, or issue certificates after only the MCQ stage.

The MCQ structural audit is not a semantic/manual review: it detects exact normalized prompt duplicates and structural defects, but cannot guarantee that differently worded questions test different concepts or that every answer has been independently reviewed by a subject-matter expert.

## Implementation summary

### Exercise navigation and completion

- The exercise detail page loads the published course exercise order and provides Previous/Next navigation without crossing course boundaries. At the end it returns to the course Practice listing.
- Successful server grading is the only event that updates the visible completion state. Completion is restored via the authenticated, course-scoped exercise-progress endpoint rather than treated as authoritative local-storage state.
- The Practice list shows the server-returned completion state. Progress remains user- and course-scoped; the current server grading and XP behavior is reused.

### Certification prerequisites and server checks

- Added server-side course prerequisite calculation over published required lessons and published exercises for the authenticated learner.
- MCQ start, protected attempt access/submission, practical-exam access/start/submission and certificate issuance recheck relevant prerequisites server-side.
- Removed the separate project-review gate from generic certificate eligibility. The Projects feature remains intact.
- Certificate cards can show course-specific lesson/practice links, Start exam only where backend eligibility and content readiness permit, or a truthful unavailable/pending status.

### MCQ exam

- Final exam selection is configured for 80 distinct normalized question prompts and only exposes question/option text to the client.
- Each attempt stores the shuffled option mapping server-side; the server grades against that persisted mapping rather than trusting client correctness flags.
- Missing/invalid references or an insufficient unique bank keep the exam unavailable rather than falling back to 20 questions.

### Practical assessment and certificates

- Added persisted practical-attempt records and migration `0005_practical_exam_attempts`.
- Added protected APIs and a themed React page for explicitly published practical task definitions using supported deterministic text-grading modes (`exact_text`, `contains_all`, `json_equal`). The endpoint never runs arbitrary submitted code inside the FastAPI process.
- Certificate issuance now requires prerequisite completion, a passed MCQ attempt and a passed practical attempt for the same user/course. Repeated issuance is idempotent, and a failed or merely completed MCQ attempt cannot issue a certificate.
- **No course currently contains `exams/practical-exam.json` in the uploaded snapshot.** Code execution assessments across each language/framework need carefully authored tasks and a supported isolated runner integration before they can be published. This update does not pretend generic text graders or the existing general runner prove all course-specific practical exams are ready.

## Source audit

- Published tracks audited: **62**.
- Structurally MCQ-ready (80+ distinct valid prompts): **34**.
- MCQ banks blocked: **28**.
- Published supported practical definitions: **0**.
- Fully exam-ready tracks: **0**.

### MCQ banks currently blocked

Distinct valid prompt counts are shown in brackets. These are not padding recommendations; author or repair real curriculum-aligned questions before publishing:

`angular` (45), `asp` (36), `dart` (60), `django` (40), `dsa` (40), `excel` (18), `fastapi` (36), `flask` (22), `generative-ai` (60), `git` (20), `go` (40), `json-yaml` (47), `kotlin` (39), `lua` (40), `nextjs` (60), `nodejs` (60), `powershell` (30), `react` (60), `ruby` (10), `sass` (39), `scikit-learn` (30), `solidity` (40), `sqlite` (40), `swift` (60), `typescript` (28), `vue` (60), `web-application-security` (20), `xml` (32)

The detailed machine-readable audit is `docs/exam-readiness-report.json`. It includes per-course title/status, file-reference counts, valid question and prompt counts, missing/malformed references, missing answer keys, malformed question counts, duplicate IDs/text counts, MCQ readiness, practical readiness and overall readiness. It is generated from course content and does not query or modify the production database.

Two malformed content examples were repaired without changing their correct-answer keys:

- Java `java-q-009-01`: replaced a duplicated distractor with a distinct, course-relevant distractor.
- Kotlin `kotlin-final-trace-005`: replaced an empty option with a valid distractor. Kotlin remains blocked because its distinct prompt count is below 80.

## Files changed or added

- `backend/app/main.py` — question-bank validation and selection, 80-question readiness, persisted option shuffle, prerequisite gates, progress/readiness APIs, practical attempt APIs and certificate eligibility/issuance gates.
- `backend/app/models.py` — `PracticalExamAttempt` persistence model.
- `backend/alembic/versions/0005_practical_exam_attempts.py` — repeatable/backward-compatible practical-attempt migration.
- `backend/scripts/test_phase2_exam_api.py` — integration coverage of exam prerequisites, shuffled mapping, practical flow, cert issuance and learner isolation.
- `backend/scripts/test_exam_question_bank_compatibility.py` — checks minimum question-bank readiness rather than assuming every published bank is ready.
- `backend/scripts/test_migration_repeatability.py` — migration head/table checks.
- `backend/scripts/audit_exam_readiness.py` — static course-by-course readiness audit.
- `backend/content/courses/java/exams/question-files/lesson-009-questions.json` — fixes duplicated distractor.
- `backend/content/courses/kotlin/exams/final-assessment-questions.json` — fixes blank option.
- `frontend/src/pages/ExerciseDetailPage.jsx` — course-scoped exercise navigation and server completion display.
- `frontend/src/pages/ChallengesPage.jsx` — real completion markers in Practice.
- `frontend/src/pages/CertificatesPage.jsx` — lesson/exercise links, server readiness state, MCQ/practical state, and removal of project-review prerequisite messaging.
- `frontend/src/pages/ExamPage.jsx` — 80-question and mandatory-practical messaging, structured API errors and practical links.
- `frontend/src/pages/PracticalExamPage.jsx` — practical attempt task/submission interface.
- `frontend/src/App.jsx` — practical-exam route.
- `frontend/src/styles/pages.css`, `frontend/src/styles/responsive.css` — scoped responsive actions row styling.
- `frontend/package.json` — focused test scripts.
- `frontend/scripts/test_exercise_navigation_progress.mjs`, `frontend/scripts/test_practical_certification_flow.mjs` — source-contract regression checks.
- `docs/exam-readiness-report.json` — generated per-course audit.

## Validation results

### Passed

- `python -m compileall -q app scripts` — passed.
- `python scripts/check_alembic_heads.py` — passed; one head at `0005_practical_exam_attempts`.
- `python scripts/check_repository_hygiene.py` — passed on the working source tree.
- `python scripts/test_phase2_exam_api.py` — passed, including user/course-scoped exercise progress, lesson/exercise prerequisite checks, attempt re-checks, hidden answer keys, randomized options graded against the persisted mapping, duplicate-submission behavior, MCQ pass unlocking practical (not certificate), failed practical not issuing a certificate, project review not being a gate, certificate listing/verification and XP idempotency.
- `python scripts/test_exam_question_bank_compatibility.py` — passed for all 62 published tracks; undersized/invalid banks are unavailable.
- `python scripts/test_migration_repeatability.py` — passed using a temporary SQLite database; migration ran repeatably. No production Neon writes were made.
- `python scripts/test_course_api_contract.py` — passed.
- `python scripts/test_exercise_solution_endpoint.py` — all 3 test cases printed `ok`, but the process did not exit within the combined validation timeout; treat its assertions as passed while clean process teardown remains unverified.
- `python scripts/test_phase2_content_routes.py` — passed.
- `python scripts/test_auth_lifecycle.py` — passed.
- `python scripts/test_phase5_contract.py` — passed (8 checks).
- `python scripts/test_runner_config_status.py` — passed (2 checks).
- Frontend source-contract Node suite: **22 of 26 scripts passed**, including both new focused tests. Four failed because expected source/config patterns are absent from this uploaded baseline in unrelated files (details below).

### Failed or not verified

- Four pre-existing frontend source-contract checks fail against the source snapshot:
  - `test_deployment_config.mjs` expects Vercel rewrite `/api/proxy/:path*`, while the supplied config rewrites `/api/:path*` directly to the Render backend.
  - `test_exercise_page_contract.mjs` expects `allowed_roots` in `backend/app/main.py`; that marker was also absent in the original supplied snapshot and this runner setting was not rewritten by the exam changes.
  - `test_language_workspace.mjs` expects `usableReferenceSources(content.sources)` in `frontend/src/pages/LessonPage.jsx`; this lesson page was not changed for this task.
  - `test_lesson_loading_timeout.mjs` expects `timeoutMs: 12_000` in `frontend/src/pages/LessonPage.jsx`; this lesson page was not changed for this task.
- `npm run build` could not run because the ZIP has no installed `frontend/node_modules` and therefore no `vite` binary. Dependency installation timed out in this environment. The partial install was removed from the deliverable. **Frontend bundle compilation is not verified.**
- `git diff --check` reports CRLF line endings as trailing whitespace in the pre-existing uploaded `.github/workflows/checks.yml` snapshot (not modified for this upgrade). No normalization was applied to avoid changing an unrelated file.
- No browser screenshots or manual viewport-by-viewport visual comparison was possible; no screenshot regression is claimed. CSS/source checks were used only.
- MCQ structural readiness is not the same as a manual subject-matter/semantic-duplicate review.
- All practical exams remain unavailable until course-specific task definitions are authored/published and supported grading/runtime integrations are tested.

## Visual regression status

No large layout redesign was made. Existing components and styles were reused; the new action row has scoped styles and responsive wrapping. However, there was no running Vite application or installed browser-test setup, so no before/after screenshots were captured at 320, 375, 430, 768, 1024, 1366 and 1440 px. Treat visual regression as **not run**, not passed.

## Apply and test on Windows

The archive is a source-tree overlay rooted at the repository root; it does not include `.git`, real `.env` files, virtual environments, `node_modules`, or generated build output. Back up your current folder first and review the diff before replacing any files:

```powershell
Set-Location E:\Code_Leaf

git status --short
git branch --show-current
git rev-parse HEAD
git diff --check
git diff --stat

# Extract the ZIP into a separate review folder first; then copy the reviewed changes
# into E:\Code_Leaf. Do not overwrite your real .env files.
```

Backend validation (with your existing virtual environment activated, from `E:\Code_Leafackend`):

```powershell
python -m compileall -q app scripts
python scripts/check_alembic_heads.py
python scripts/check_repository_hygiene.py
python scripts/audit_exam_readiness.py
python scripts/test_phase2_exam_api.py
python scripts/test_exam_question_bank_compatibility.py
python scripts/test_migration_repeatability.py
python scripts/test_course_api_contract.py
python scripts/test_exercise_solution_endpoint.py
python scripts/test_phase2_content_routes.py
python scripts/test_auth_lifecycle.py
python scripts/test_phase5_contract.py
python scripts/test_runner_config_status.py
```

Frontend validation (from `E:\Code_Leafrontend`, after installing dependencies):

```powershell
npm ci
npm run test:exercise-navigation-progress
npm run test:practical-certification-flow
npm run build
```

Before any release, manually review the `docs/exam-readiness-report.json` results and author/publish the missing course-specific question banks and practical tasks. Confirm practical execution uses a real isolated runner for code-based tracks. Then perform browser screenshots at the seven required viewport widths. This ZIP is not a deployment and does not alter the production service.
