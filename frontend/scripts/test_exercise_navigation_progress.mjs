import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../src/pages/ExerciseDetailPage.jsx", import.meta.url), "utf8");
const practice = readFileSync(new URL("../src/pages/ChallengesPage.jsx", import.meta.url), "utf8");
const backend = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8");

assert.match(page, /Next exercise/, "exercise detail offers forward navigation");
assert.match(page, /Previous exercise/, "exercise detail offers backward navigation");
assert.match(page, /exerciseRoute\(courseSlug, navigation\.next\)/, "next navigation remains in the current course");
assert.match(page, /exerciseRoute\(courseSlug, navigation\.previous\)/, "previous navigation remains in the current course");
assert.match(page, /\/api\/me\/courses\/\$\{encodeURIComponent\(courseSlug\)\}\/exercise-progress/, "exercise detail restores progress from the authenticated server API");
assert.match(page, /Boolean\(data\.completed\)/, "only the server grading response updates the displayed completion state");
assert.match(practice, /Completed/, "Practice list displays a completed indicator");
assert.match(backend, /@app\.get\("\/api\/me\/courses\/\{course_slug\}\/exercise-progress"\)/, "backend exposes learner-scoped exercise completion");
assert.match(backend, /ExerciseProgress\.completed/, "progress readback is based on persistent database state");
console.log("Exercise navigation/progress source-contract checks passed.");
