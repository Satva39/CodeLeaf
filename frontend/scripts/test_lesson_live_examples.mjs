import assert from "node:assert/strict";
import { buildSandboxDocument, getLessonLiveExampleMode } from "../src/lib/lessonLiveExampleModel.js";

const fixtures = [
  [{ courseSlug: "html", lessonTitle: "Introduction to HTML", codeLanguage: "html" }, "browser-html"],
  [{ courseSlug: "css", lessonTitle: "CSS 2D Transforms", codeLanguage: "css" }, "browser-css"],
  [{ courseSlug: "javascript", lessonTitle: "DOM Manipulation", codeLanguage: "javascript" }, "browser-javascript"],
  [{ courseSlug: "python", lessonTitle: "For Loops", codeLanguage: "python" }, "loops"],
  [{ courseSlug: "typescript", lessonTitle: "Type Inference", codeLanguage: "typescript" }, "types"],
  [{ courseSlug: "python", lessonTitle: "Variables and Constants", codeLanguage: "python" }, "variables"],
  [{ courseSlug: "java", lessonTitle: "Conditional Statements", codeLanguage: "java" }, "conditions"],
  [{ courseSlug: "cpp", lessonTitle: "Arrays and Vectors", codeLanguage: "cpp" }, "collections"],
  [{ courseSlug: "nextjs", lessonTitle: "Introduction to Next.js", codeLanguage: "javascript" }, "ui"],
  [{ courseSlug: "sql", lessonTitle: "Filtering Rows with WHERE", codeLanguage: "sql" }, "database"],
  [{ courseSlug: "rest-api-development", lessonTitle: "HTTP Request and Response", codeLanguage: "http" }, "api"],
  [{ courseSlug: "git", lessonTitle: "Branches and Merging", codeLanguage: "bash" }, "git"],
  [{ courseSlug: "docker", lessonTitle: "Container Lifecycle", codeLanguage: "dockerfile" }, "containers"],
  [{ courseSlug: "redis", lessonTitle: "Cache Eviction Policies", codeLanguage: "redis-cli" }, "cache"],
  [{ courseSlug: "web-application-security", lessonTitle: "Authentication and Authorization", codeLanguage: "python" }, "security"],
  [{ courseSlug: "scikit-learn", lessonTitle: "Classification Thresholds", codeLanguage: "python" }, "data"],
  [{ courseSlug: "excel", lessonTitle: "Spreadsheet Formulas", codeLanguage: "excel-formula" }, "spreadsheet"],
  [{ courseSlug: "json-yaml", lessonTitle: "JSON Configuration", codeLanguage: "json" }, "config"],
  [{ courseSlug: "linux", lessonTitle: "File Permissions", codeLanguage: "bash" }, "filesystem"],
  [{ courseSlug: "python", lessonTitle: "Classes and Object-Oriented Programming", codeLanguage: "python" }, "oop"],
  [{ courseSlug: "python", lessonTitle: "Exception Handling", codeLanguage: "python" }, "error-flow"],
  [{ courseSlug: "go", lessonTitle: "TCP and UDP Programming", codeLanguage: "go" }, "network"],
  [{ courseSlug: "javascript", lessonTitle: "State Transitions", codeLanguage: "javascript" }, "browser-javascript"],
  [{ courseSlug: "course-with-a-unique-topic", lessonTitle: "An uncommon topic", codeLanguage: "custom" }, "concept"],
];
for (const [lesson, expected] of fixtures) {
  assert.equal(getLessonLiveExampleMode(lesson), expected, `mode for ${lesson.courseSlug} / ${lesson.lessonTitle}`);
}

const html = buildSandboxDocument("browser-html", "<main><h1>Hello CodeLeaf</h1></main>");
assert.match(html, /Hello CodeLeaf/);
assert.match(html, /Content-Security-Policy/);
assert.match(html, /connect-src 'none'/);
assert.match(html, /<body>/);

const css = buildSandboxDocument("browser-css", ".demo-card { color: rebeccapurple; }", "CSS 2D Transforms");
assert.match(css, /transform-target/);
assert.match(css, /color: rebeccapurple/);
assert.match(css, /2D transform playground/);

const js = buildSandboxDocument("browser-javascript", "console.log('live output');");
assert.match(js, /live output/);
assert.match(js, /console\.log/);
assert.match(js, /connect-src 'none'/);

// The resolver always returns a supported mode, including lessons that need
// a clearly labeled illustrative fallback rather than unsafe native execution.
for (const lesson of [
  { courseSlug: "python", lessonTitle: "Introduction to Python", codeLanguage: "python" },
  { courseSlug: "java", lessonTitle: "Streams", codeLanguage: "java" },
  { courseSlug: "unknown", lessonTitle: "Unclassified topic", codeLanguage: "unknown" },
]) assert.ok(getLessonLiveExampleMode(lesson), "every lesson must resolve to a live-example mode");

console.log(`Lesson live-example checks passed (${fixtures.length} topic routes plus sandbox CSP/output checks).`);
