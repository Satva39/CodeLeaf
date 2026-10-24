import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  compatibleFilename,
  createBrowserDocument,
  getLanguageForFilename,
  isBrowserWorkspace,
  resolveLanguage,
  safeWorkspaceFilename,
  starterFiles,
} from "../src/lib/languageWorkspace.js";
import { COURSE_CATALOG } from "../src/data.js";

const here = dirname(fileURLToPath(import.meta.url));
const read = (relativePath) => readFileSync(resolve(here, relativePath), "utf8");

// A C lesson must seed a C file, not the generic JavaScript filename or a web project.
const cLanguage = resolveLanguage("c", "C");
assert.equal(cLanguage.key, "c");
assert.equal(cLanguage.filename, "main.c");
const cFiles = starterFiles({ courseSlug: "c", codeLanguage: "c", source: '#include <stdio.h>\nint main(void) { return 0; }' });
assert.deepEqual(cFiles.map((file) => file.name), ["main.c"]);
assert.match(cFiles[0].content, /#include <stdio\.h>/);
assert.equal(getLanguageForFilename("main.cpp").key, "cpp");
assert.equal(getLanguageForFilename("main.py").key, "python");
assert.equal(getLanguageForFilename("Main.java").key, "java");
assert.equal(compatibleFilename("example.js", cLanguage), "main.c");
assert.equal(compatibleFilename("chapter.c", cLanguage), "chapter.c");
assert.equal(compatibleFilename("../../unsafe.js", resolveLanguage("javascript")), "script.js");
for (const course of COURSE_CATALOG) {
  assert.notEqual(resolveLanguage(course.slug).key, "plain", `course ${course.slug} should use a language-specific workspace mapping`);
}

const cssFiles = starterFiles({ courseSlug: "css", codeLanguage: "css", source: "h1 { color: tomato; }" });
assert.equal(cssFiles[0].name, "styles.css");
assert.ok(cssFiles.some((file) => file.name === "index.html"));
assert.ok(cssFiles.some((file) => file.name === "script.js"));
assert.equal(isBrowserWorkspace(cssFiles), true);
const doc = createBrowserDocument(cssFiles, "codeleaf-playground-output");
assert.match(doc, /Content-Security-Policy/);
assert.match(doc, /connect-src 'none'/);
assert.match(doc, /codeleaf-playground-output/);
assert.match(doc, /color: tomato/);
assert.equal(safeWorkspaceFilename("my program.c"), true);
assert.equal(safeWorkspaceFilename("../main.c"), false);
assert.equal(safeWorkspaceFilename(""), false);

const app = read("../src/App.jsx");
assert.match(app, /path="\/try\/:courseSlug\/:lessonSlug\?"/);
assert.match(app, /path="\/practice\/:courseSlug\/:lessonSlug\/:exerciseSlug"/);
const lesson = read("../src/pages/LessonPage.jsx");
assert.match(lesson, /openSeededWorkspace\("try"/);
assert.match(lesson, /openSeededWorkspace\("playground"/);
assert.match(lesson, /compatibleFilename\(content\.codeFileName, workspaceLanguage\)/);
assert.doesNotMatch(lesson, /\? "example\.js"/);
assert.doesNotMatch(lesson, /\{exercises\.length > 0 &&/);
assert.match(lesson, /lesson-practice-library/);
assert.match(lesson, /referenceSources\.length > 0/);
assert.doesNotMatch(lesson, /KnowledgeCheck|knowledge-check-section/);
const collectionsCss = read("../src/styles/collections.css");
assert.match(collectionsCss, /\.course-exercise-library \.exercise-topic-group/);
assert.match(collectionsCss, /\.course-exercise-library \.exercise-library-row/);
assert.match(collectionsCss, /@media \(max-width: 650px\)/);
assert.match(lesson, /setExpandedGroup\(\(previous\) => previous === g\.title \? "" : g\.title\)/);

const workspace = read("../src/pages/PlaygroundPage.jsx");
for (const control of ["New file", "Rename", "Delete", "Export all files", "WORKSPACE_STORAGE_KEY", "safeWorkspaceFilename", "createBrowserDocument"]) {
  assert.ok(workspace.includes(control), `workspace should include ${control}`);
}
const tryIt = read("../src/pages/TryItPage.jsx");
assert.match(tryIt, /openSeededWorkspace\("playground"/);
const exercise = read("../src/pages/ExerciseDetailPage.jsx");
assert.match(exercise, /Show solution/);
assert.match(exercise, /Need a hint\?/);
assert.match(exercise, /Open in Try-it editor/);
assert.match(exercise, /compatibleFilename\(exercise\?\.starter\?\.file_name \|\| exercise\?\.starter\?\.filename, language\)/);
assert.match(exercise, /api\/courses\/\$\{encodeURIComponent\(courseSlug\)\}\/lessons\/\$\{encodeURIComponent\(lessonSlug\)\}\/exercises/);
assert.match(exercise, /exercises\/\$\{encodeURIComponent\(exerciseSlug\)\}\/solution/);

console.log("Learning workspace checks passed: language extensions, source seeding, sandbox preview, file management, lesson routing, one-open sidebar, references, and standalone exercises.");
