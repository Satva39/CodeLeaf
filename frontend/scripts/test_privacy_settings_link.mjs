import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (name) => fs.readFileSync(path.join(root, name), "utf8");
const profile = read("src/pages/ProfilePage.jsx");
const hub = read("src/pages/LearningHubPage.jsx");
const phase5Css = read("src/styles/phase5.css");

assert.doesNotMatch(profile, /privacy controls|PRIVACY & VISIBILITY|account-setting-unavailable|Not available yet/i);
assert.match(profile, /LEARNING PREFERENCES/);
assert.match(profile, /\/api\/me\/learning-preferences/);
assert.match(profile, /account-logout-button/);
assert.match(hub, /\/api\/me\/learning-preferences/);
assert.match(hub, /Allow privacy-minimized product analytics/);
assert.match(hub, /Review and privacy settings/);
assert.match(phase5Css, /phase5-privacy-note/);
console.log("PASS the unfinished privacy placeholder is removed from the profile page");
console.log("PASS account settings provide a logout action in place of the placeholder");
console.log("PASS real backend-backed learning/privacy preferences remain available in the Learning Hub");
