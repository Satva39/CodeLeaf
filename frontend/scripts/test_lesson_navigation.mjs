import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const page = readFileSync(resolve(process.cwd(), "src/pages/LessonPage.jsx"), "utf8");
const start = page.indexOf("function CourseSidebar(");
const end = page.indexOf("function contentFromPublishedLesson(");
assert.ok(start >= 0 && end > start, "CourseSidebar should exist in LessonPage");
const sidebar = page.slice(start, end);
assert.match(sidebar, /const activeGroupTitle\s*=/, "active lesson should determine the default expanded module");
assert.match(sidebar, /const \[expandedGroup, setExpandedGroup\] = useState\(activeGroupTitle\)/, "only one module should be tracked as expanded");
assert.match(sidebar, /setExpandedGroup\(\(previous\) => previous === g\.title \? \"\" : g\.title\)/, "clicking a module should close the previous one");
assert.match(sidebar, /aria-expanded=\{expandedGroup === g\.title\}/, "module toggle should expose its expansion state accessibly");
assert.match(sidebar, /setExpandedGroup\(activeGroupTitle\)/, "navigation to a different lesson should open its parent module");
assert.doesNotMatch(sidebar, /Object\.fromEntries\(groups\.map\(\(g\) => \[g\.title, true\]\)\)/, "all modules must not be expanded by default");
assert.match(page, /<LessonLiveExample[\s\S]*?lessonTitle=\{current\?\.title/, "lesson page should integrate the relevant interactive example");
console.log("Lesson navigation checks passed (single-open accordion, active-module tracking, accessibility, and live-example integration).");
