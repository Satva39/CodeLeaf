import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const bookmarks = readFileSync(path.join(root, "src/pages/BookmarksPage.jsx"), "utf8");
const profile = readFileSync(path.join(root, "src/pages/ProfilePage.jsx"), "utf8");
const styles = readFileSync(path.join(root, "src/styles/phase3c-personal-learning.css"), "utf8");
const checks = [
  ["bookmarks retain server/guest state", /useBookmarkState/.test(bookmarks) && /bookmarkState\.mode === "remote"/.test(bookmarks) && /bookmarkState\.mode === "guest"/.test(bookmarks)],
  ["search and course filter exist", /Search saved lessons/.test(bookmarks) && /courseFilter/.test(bookmarks) && /All courses/.test(bookmarks)],
  ["bookmark actions keep encoded lesson routes", /encodeURIComponent\(entry\.course_slug\)/.test(bookmarks) && /encodeURIComponent\(entry\.lesson_slug\)/.test(bookmarks)],
  ["remote preferences are read from server", /\/api\/me\/learning-preferences/.test(profile) && /apiGetJson/.test(profile)],
  ["preferences save without client-issued XP", /method: "PATCH"/.test(profile) && /review_frequency_days/.test(profile) && /daily_review_limit/.test(profile) && !/xp_points\s*:/.test(profile)],
  ["analytics consent is explicit", /analytics_enabled/.test(profile) && /Share optional product analytics/.test(profile)],
  ["styles are scoped and responsive", /\.phase3c-bookmark-card/.test(styles) && /@media \(max-width: 560px\)/.test(styles) && /prefers-reduced-motion/.test(styles)],
];
for (const [name, passed] of checks) {
  if (!passed) throw new Error(`FAILED: ${name}`);
  console.log(`PASS ${name}`);
}
console.log(`Passed ${checks.length} Phase 3C contract checks.`);
