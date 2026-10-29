import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  isSupportedPracticeExercise,
  practiceExerciseKind,
  practiceExerciseLabel,
} from "../src/lib/practiceExerciseTypes.js";

assert.equal(practiceExerciseKind("choice"), "mcq");
assert.equal(practiceExerciseKind("multiple_choice"), "mcq");
assert.equal(practiceExerciseKind("mcq"), "mcq");
assert.equal(practiceExerciseLabel("choice"), "MCQ");
assert.equal(practiceExerciseKind("coding"), "code_challenge");
assert.equal(practiceExerciseKind("code_challenge"), "code_challenge");
assert.equal(practiceExerciseLabel("implementation"), "Code Challenge");
assert.equal(isSupportedPracticeExercise("short_answer"), false);
assert.equal(isSupportedPracticeExercise("essay"), false);

const practice = readFileSync(new URL("../src/pages/ChallengesPage.jsx", import.meta.url), "utf8");
const detail = readFileSync(new URL("../src/pages/ExerciseDetailPage.jsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../src/styles/collections.css", import.meta.url), "utf8");
const backend = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8");

assert.match(practice, /items\.filter\(\(item\) => item\.is_locked \|\| isSupportedPracticeExercise\(item\.type\)\)/);
assert.match(practice, /item\.is_locked/);
assert.match(practice, /\/plans/);
assert.match(practice, /practice-completed-badge/);
assert.match(detail, /\.filter\(\(item\) => isSupportedPracticeExercise\(item\.type\)\)/);
assert.match(detail, /resolveLanguage\(courseSlug, ""\)/, "workspace follows the current course's language");
assert.match(styles, /\.practice-task-meta span\.practice-completed-badge/);
assert.match(backend, /Only multiple-choice questions and code challenges are available in Practice\./);
assert.match(backend, /is_supported_practice_exercise\(/, "eligibility uses the same Practice task policy");

console.log("Practice types and completion-badge checks passed.");
