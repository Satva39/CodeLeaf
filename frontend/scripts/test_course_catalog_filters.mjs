import assert from "node:assert/strict";
import { filterCourseCatalog, mapAuthoritativeCourseCatalog } from "../src/lib/courseCatalogFilters.js";

const courses = [
  { slug: "html", title: "HTML", desc: "Structure the web", category: "Web", level: "Beginner", lessons: 20, status: "Published" },
  { slug: "react", title: "React", desc: "Build interfaces", category: "Web", level: "Intermediate", lessons: 75, status: "Published" },
  { slug: "python", title: "Python", desc: "Programming", category: "Programming", level: "Beginner", lessons: 0, status: "Roadmap" },
];

assert.deepEqual(filterCourseCatalog(courses, { category: "Web" }).map((c) => c.slug), ["html", "react"]);
assert.deepEqual(filterCourseCatalog(courses, { level: "Intermediate" }).map((c) => c.slug), ["react"]);
assert.deepEqual(filterCourseCatalog(courses, { status: "Roadmap" }).map((c) => c.slug), ["python"]);
assert.deepEqual(filterCourseCatalog(courses, { query: "not-a-course" }), []);
assert.deepEqual(filterCourseCatalog(courses, { sort: "lessons-desc" }).map((c) => c.slug), ["react", "html", "python"]);
assert.deepEqual(filterCourseCatalog(courses, { status: "All availability", query: "structure", category: "All" }).map((c) => c.slug), ["html"]);
console.log("PASS catalog search/category/level/status/empty-result/sort checks");

const authoritative = mapAuthoritativeCourseCatalog([
  { slug: "html", title: "HTML Published", description: "API description", lesson_count: 3, module_count: 2, reference_count: 4, project_count: 1, practice_count: 5, estimated_minutes: 70, status: "published", category: "Web" },
  { slug: "planned-from-api", title: "Planned", lesson_count: 0, status: "roadmap" },
], [
  { slug: "html", title: "Stale local title", icon: "HTML", color: "#abcdef" },
  { slug: "frontend-only", title: "Must not appear" },
]);
assert.deepEqual(authoritative.map((course) => course.slug), ["html", "planned-from-api"]);
assert.equal(authoritative[0].title, "HTML Published");
assert.equal(authoritative[0].icon, "HTML");
assert.equal(authoritative[0].status, "Published");
assert.equal(authoritative[0].references, 4);
assert.equal(authoritative[1].status, "Roadmap");
assert.equal(authoritative[1].lessons, 0);
console.log("PASS backend catalog controls membership/status while local metadata only decorates matching courses");
