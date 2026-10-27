import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../src/pages/CertificatesPage.jsx", import.meta.url), "utf8");
const backend = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8");

assert.match(page, /\/api\/exams\/catalog/, "certificates page fetches live exam availability");
assert.match(page, /exam\?\.available === true/, "exam readiness controls the available state");
assert.match(page, /Start exam/, "published exam cards expose a start action");
assert.match(page, /\/exam\/\$\{encodeURIComponent\(course\.slug\)\}/, "start action opens the matching course exam");
assert.doesNotMatch(page, /The exam becomes available when a reviewed course blueprint and question bank are published\./, "course cards do not hardcode the roadmap message");
assert.doesNotMatch(page, /exam \? \"Roadmap\"/, "missing learner progress never falls back to the misleading Roadmap CTA");
assert.match(page, /Sign in to check eligibility/, "signed-out learners get an explicit sign-in action instead of Roadmap");
assert.match(page, /Progress unavailable/, "missing per-learner progress is shown explicitly");
assert.match(page, /Retry progress check/, "learners can retry a failed progress request");
assert.match(page, /lessons_complete !== true/, "lesson action is shown until the backend confirms lesson completion");
assert.match(page, /exercises_complete !== true/, "exercise action is shown until the backend confirms exercise completion");
assert.match(page, /Exam unavailable/, "unpublished practical content has a truthful unavailable state");
assert.match(backend, /@app\.get\("\/api\/exams\/catalog"\)/, "backend exposes an exam-availability catalog");
assert.match(backend, /_has_published_exam_question_set/, "catalog verifies published question-bank data");

console.log("Certificate exam availability contract checks passed.");
