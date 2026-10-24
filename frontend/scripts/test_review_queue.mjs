import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildReviewLessonHref, formatReviewDueDate } from "../src/lib/reviewSchedule.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const lesson = buildReviewLessonHref({ id: "review-123", course_slug: "html", item_type: "lesson", item_slug: "intro-to-html", lesson_slug: "intro-to-html" });
assert.equal(lesson.startsWith("/learn/html/intro-to-html?"), true);
assert.equal(new URLSearchParams(lesson.split("?")[1]).get("reviewId"), "review-123");
assert.equal(new URLSearchParams(lesson.split("?")[1]).get("reviewType"), "lesson");

const exercise = buildReviewLessonHref({ id: "review-456", course_slug: "c-plus-plus", item_type: "exercise", item_slug: "loop-practice", lesson_slug: "for-loops" });
assert.equal(exercise.startsWith("/learn/c-plus-plus/for-loops?"), true);
assert.equal(new URLSearchParams(exercise.split("?")[1]).get("reviewItemSlug"), "loop-practice");
assert.equal(buildReviewLessonHref({ course_slug: "html", item_type: "exercise", item_slug: "task" }), "/practice/html");
assert.equal(formatReviewDueDate("not-a-date", new Date("2026-01-01T00:00:00Z")), "Schedule date unavailable");
assert.equal(formatReviewDueDate("2026-01-01T00:00:00Z", new Date("2026-01-02T00:00:00Z")), "Due now");
assert.equal(formatReviewDueDate("2026-01-03T00:00:00Z", new Date("2026-01-01T00:00:00Z")), "Due in 2 days");

const app = fs.readFileSync(path.join(root, "src/App.jsx"), "utf8");
assert.match(app, /import ReviewPage from "\.\/pages\/ReviewPage\.jsx"/);
assert.match(app, /<Route path="\/review" element={<ReviewPage \/>} \/>/);
const reviewPage = fs.readFileSync(path.join(root, "src/pages/ReviewPage.jsx"), "utf8");
assert.match(reviewPage, /\/api\/me\/reviews/);
assert.match(reviewPage, /\/api\/me\/learning-preferences/);
assert.match(reviewPage, /\/snooze/);
const prompt = fs.readFileSync(path.join(root, "src/components/ReviewPrompt.jsx"), "utf8");
assert.match(prompt, /\/rate/);
assert.match(prompt, /does not award XP or mark content complete/i);
console.log("Review queue contract tests passed (lesson/exercise targets, dates, route, server queue, preferences, snooze, self-rating).");
