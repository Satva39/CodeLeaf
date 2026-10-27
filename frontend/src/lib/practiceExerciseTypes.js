const MCQ_TYPES = new Set(["choice", "multiple_choice", "mcq"]);
const CODE_CHALLENGE_TYPES = new Set([
  "coding",
  "code",
  "code_challenge",
  "implementation",
  "practical",
  "workbook_practice",
]);

export function normalizePracticeExerciseType(value) {
  return String(value || "").trim().toLowerCase().replace(/[-\s]+/g, "_");
}

export function practiceExerciseKind(value) {
  const type = normalizePracticeExerciseType(value);
  if (MCQ_TYPES.has(type)) return "mcq";
  if (CODE_CHALLENGE_TYPES.has(type)) return "code_challenge";
  return null;
}

export function isSupportedPracticeExercise(value) {
  return practiceExerciseKind(value) !== null;
}

export function practiceExerciseLabel(value) {
  return practiceExerciseKind(value) === "mcq" ? "MCQ" : "Code Challenge";
}
