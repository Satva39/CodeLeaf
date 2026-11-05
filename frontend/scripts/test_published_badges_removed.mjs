import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checks = [
  ["src/components/common.jsx", /course\.status\s*!==\s*"Published"\s*&&\s*<span[\s\S]*?course-status-pill/],
  ["src/pages/CourseDirectoryPage.jsx", /course\.status\s*!==\s*"Published"\s*&&\s*<span[\s\S]*?course-status-pill/],
  ["src/components/course/CourseOverview.jsx", /statusLabel\s*!==\s*"Published"\s*&&\s*<span[\s\S]*?course-status-pill/],
];
for (const [file, pattern] of checks) {
  const source = fs.readFileSync(path.join(root, file), "utf8");
  assert.match(source, pattern, `${file} should suppress Published status chips`);
}
const sourceFiles = [];
function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(target);
    else if (/\.(jsx|tsx)$/.test(entry.name)) sourceFiles.push(target);
  }
}
walk(path.join(root, "src"));
const remainingStatusPillSites = sourceFiles.flatMap((file) => {
  const source = fs.readFileSync(file, "utf8");
  return source.includes("course-status-pill") && !checks.some(([relative]) => path.resolve(root, relative) === file)
    ? [path.relative(root, file)]
    : [];
});
assert.deepEqual(remainingStatusPillSites, [], "No other course Published status badge sites should remain");
console.log("PASS Published development badges are hidden across Tutorials, Projects, References, Practice and course overview cards");
