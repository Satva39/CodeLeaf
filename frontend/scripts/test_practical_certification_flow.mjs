import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const certificates = readFileSync(new URL("../src/pages/CertificatesPage.jsx", import.meta.url), "utf8");
const exam = readFileSync(new URL("../src/pages/ExamPage.jsx", import.meta.url), "utf8");
const practical = readFileSync(new URL("../src/pages/PracticalExamPage.jsx", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
const backend = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8");
const models = readFileSync(new URL("../../backend/app/models.py", import.meta.url), "utf8");

assert.match(backend, /required_question_count["']?\s*:\s*80|"required_question_count": 80/, "backend reports the 80-question exam minimum");
assert.match(backend, /_choose_exam_questions\(pool, blueprint, count=80\)/, "MCQ attempt selects 80 items server-side");
assert.match(backend, /rng\.shuffle\(options\)/, "options are randomized for each attempt on the backend");
assert.match(backend, /practical_exam_required/, "MCQ passing does not bypass practical certification");
assert.match(backend, /project_review_required["']?\s*:\s*False/, "project review is not an eligibility gate");
assert.match(backend, /@app\.post\("\/api\/courses\/\{course_slug\}\/practical-exam\/start"/, "practical starts through a protected backend route");
assert.match(backend, /@app\.post\("\/api\/me\/practical-exams\/\{attempt_id\}\/submit"/, "practical grading is server-side and attempt-scoped");
assert.match(backend, /_require_course_prerequisites\(db, user, course\)/, "eligibility is enforced on protected actions");
assert.match(models, /class PracticalExamAttempt\(Base\)/, "practical submissions have persistent attempt records");
assert.match(app, /path="\/practical\/:examSlug"/, "practical assessment page is routed");
assert.match(practical, /Submit practical exam/, "practical page has an explicit submission action");
assert.match(certificates, /Complete all lessons/, "Certificates offers the course learning route when lessons remain");
assert.match(certificates, /Complete all exercises/, "Certificates offers the course Practice route when exercises remain");
assert.match(certificates, /Take practical exam/, "passed MCQ learners are directed to the practical stage");
assert.doesNotMatch(certificates, /Meet any project review requirements/, "Certificates no longer displays a project-review prerequisite");
console.log("Practical/certification flow source-contract checks passed.");
