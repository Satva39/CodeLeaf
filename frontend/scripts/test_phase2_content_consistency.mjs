import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { filterCourseCatalog, mapAuthoritativeCourseCatalog } from "../src/lib/courseCatalogFilters.js";
import { buildReferenceDetails, flattenCourseOutline, safeExternalHref } from "../src/lib/referenceDetails.js";

const here = dirname(fileURLToPath(import.meta.url));
const read = (path) => readFileSync(resolve(here, path), "utf8");
const overview = read("../src/components/course/CourseOverview.jsx");
const landing = read("../src/pages/CourseLandingPage.jsx");
const referencePage = read("../src/pages/ReferencePage.jsx");
const projectsPage = read("../src/pages/ProjectsPage.jsx");
const practicePage = read("../src/pages/ChallengesPage.jsx");
const appRoutes = read("../src/App.jsx");
const overviewCss = read("../src/styles/course-overview-redesign.css");
const referenceCss = read("../src/styles/reference-enrichment.css");

function check(condition, label) {
  assert.ok(condition, label);
  console.log(`PASS ${label}`);
}

// Only the tutorials landing page opts into tutorial-specific course-fit details.
check(/showLearningSections\s*=\s*false/.test(overview), "shared course overview defaults to collection-safe compact mode");
check(/if\s*\(!showLearningSections\s*\|\|\s*!course\?\.slug\s*\|\|\s*!available\)/.test(overview), "outline API request only runs for published tutorial overview sections");
check(/showLearningSections/.test(landing) && /actionLabel="Start Learning"/.test(landing), "tutorial course overview includes course details and a prominent Start Learning CTA");
check(/showLearningSections=\{false\}/.test(referencePage), "reference page explicitly disables tutorial-only sections");
check(!/showLearningSections=\{true\}/.test(projectsPage), "project page never opts into tutorial-only sections");
check(!/showLearningSections=\{true\}/.test(practicePage), "practice page never opts into tutorial-only sections");
check(/path="\/courses\/:courseSlug"/.test(appRoutes) && /path="\/reference\/:courseSlug\/:referenceSlug\?"/.test(appRoutes), "course overview and reference routes are registered");
check(/@media\s*\(max-width:\s*620px\)/.test(overviewCss) && /prefers-reduced-motion/.test(overviewCss), "course overview styles support mobile and reduced motion");
check(/reference-entry-detail\.reference-entry-enriched/.test(referenceCss) && /max-width:\s*none/.test(referenceCss) && /width:\s*100%/.test(referenceCss), "reference detail panel fills available content width");
check(/buildReferenceDetails/.test(referencePage) && /flattenCourseOutline/.test(referencePage), "reference detail page enriches entries with course-outline context");

// Course catalog membership and availability remain API-authoritative.
const remoteCatalog = mapAuthoritativeCourseCatalog([
  { slug: "html", title: "HTML", lesson_count: 141, module_count: 26, reference_count: 8, project_count: 10, practice_count: 30, status: "published" },
  { slug: "draft-track", title: "Draft track", lesson_count: 12, module_count: 4, status: "draft" },
  { slug: "empty-published", title: "Empty", lesson_count: 0, module_count: 8, status: "published" },
], [
  { slug: "html", title: "Stale HTML", icon: "HTML", color: "#fff" },
  { slug: "not-on-api", title: "Must not be included" },
]);
assert.deepEqual(remoteCatalog.map((item) => item.slug), ["html", "draft-track", "empty-published"]);
assert.equal(remoteCatalog[0].title, "HTML");
assert.equal(remoteCatalog[0].lessons, 141);
assert.equal(remoteCatalog[0].status, "Published");
assert.equal(remoteCatalog[1].status, "Roadmap");
assert.equal(remoteCatalog[1].lessons, 0);
assert.equal(remoteCatalog[2].status, "Roadmap");
assert.equal(remoteCatalog[2].lessons, 0);
assert.deepEqual(filterCourseCatalog(remoteCatalog, { status: "Published" }).map((item) => item.slug), ["html"]);
console.log("PASS catalog membership, publication status, empty content, and availability filters remain consistent");

// Reference enrichment keeps author-written copy, only links to real outline slugs,
// and rejects non-web URL schemes before rendering an external link.
const outline = flattenCourseOutline([{
  title: "Version and compatibility",
  lessons: [
    { slug: "version-support", title: "Version Support", sequence: 1, keywords: ["compatibility", "runtime"] },
    { slug: "dependency-updates", title: "Dependency Updates", sequence: 2, keywords: ["upgrade", "release"] },
  ],
}]);
const generated = buildReferenceDetails({
  title: "Version compatibility", url: "https://docs.example.dev/versions", publisher: "Example Docs",
  source_type: "official_documentation", supports: "versions; compatibility", explanation: "versions; compatibility",
}, { title: "Example Framework Course" }, outline);
assert.match(generated.explanation, /Version compatibility/);
assert.ok(generated.relatedLessons.some((lesson) => lesson.slug === "version-support" || lesson.slug === "dependency-updates"));
assert.equal(safeExternalHref("https://docs.example.dev/path"), "https://docs.example.dev/path");
assert.equal(safeExternalHref("javascript:alert(1)"), "");
assert.equal(safeExternalHref("data:text/html,bad"), "");
assert.equal(safeExternalHref("not a URL"), "");
const authored = buildReferenceDetails({ title: "Specific reference", supports: "specific topic", explanation: "A specific, author-written explanation with enough context to preserve.", example: "Use this option in a focused test." }, { title: "Example Course" }, outline);
assert.equal(authored.explanation, "A specific, author-written explanation with enough context to preserve.");
assert.equal(authored.example, "Use this option in a focused test.");
console.log("PASS reference content enrichment, valid lesson matching, authored copy preservation, and external-link safety");

console.log("All Phase 2 content consistency checks passed.");
