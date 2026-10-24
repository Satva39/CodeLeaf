import assert from "node:assert/strict";
import { formatLearningStat, selectLearningTarget } from "../src/lib/learningPath.js";

const courses = [
  { slug: "html", title: "HTML — From Beginner to Professional", status: "Published", lessons: 141 },
  { slug: "python", title: "Python", status: "Published", lessons: 324 },
  { slug: "draft-course", title: "Draft Course", status: "Roadmap", lessons: 80 },
  { slug: "empty", title: "Empty Course", status: "Published", lessons: 0 },
];

const recentItems = [
  { course_slug: "html", lesson_slug: "intro", title: "Introduction to HTML", completed: false, last_opened_at: "2026-10-20T10:00:00Z" },
  { course_slug: "python", lesson_slug: "functions", title: "Python Functions", completed: true, last_opened_at: "2026-10-22T10:00:00Z" },
  { course_slug: "draft-course", lesson_slug: "hidden", title: "Draft lesson", completed: false, last_opened_at: "2026-10-24T10:00:00Z" },
];

let result = selectLearningTarget({ courses, recentItems, lastCourseSlug: "html" });
assert.equal(result.kind, "lesson");
assert.equal(result.course.slug, "python", "most recently opened available course should win");
assert.equal(result.lessonTitle, "Python Functions");
assert.equal(result.href, "/learn/python/functions");
assert.equal(result.completed, true);
assert.equal(result.ctaLabel, "Review last lesson");

result = selectLearningTarget({ courses, recentItems: [{ course_slug: "python", lesson_slug: "bad slug/?", last_opened_at: "2026-10-24T12:00:00Z" }] });
assert.equal(result.href, "/learn/python/bad%20slug%2F%3F", "lesson route segments must be encoded");
assert.equal(result.ctaLabel, "Resume last lesson");

result = selectLearningTarget({ courses, recentItems: [{ course_slug: "draft-course", lesson_slug: "hidden", last_opened_at: "2026-10-24T12:00:00Z" }], lastCourseSlug: "python" });
assert.equal(result.kind, "course", "roadmap lesson activity must not create a public resume target");
assert.equal(result.course.slug, "python");
assert.equal(result.href, "/learn/python");

result = selectLearningTarget({ courses, recentItems: [], lastCourseSlug: "unknown" });
assert.equal(result.kind, "start");
assert.equal(result.course.slug, "html");
assert.equal(result.ctaLabel, "Start learning", "first course must not be represented as prior progress");

result = selectLearningTarget({ courses: [{ slug: "only-draft", title: "Draft", status: "Roadmap", lessons: 12 }] });
assert.equal(result.kind, "catalog");
assert.equal(result.href, "/tutorials");
assert.equal(result.ctaLabel, "Explore courses");

result = selectLearningTarget({ courses, recentItems: [], lastCourseSlug: "python" });
assert.equal(result.kind, "course");
assert.equal(result.course.slug, "python");
assert.equal(result.ctaLabel, "Continue course");

assert.equal(formatLearningStat(1200, "remote"), "1,200");
assert.equal(formatLearningStat(0, "loading"), "Loading…");
assert.equal(formatLearningStat(0, "unavailable"), "Unavailable");

console.log("PASS: 9 learning-path and honest progress state checks");
