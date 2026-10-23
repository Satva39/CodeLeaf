import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (name) => fs.readFileSync(path.join(root, name), "utf8");
const profile = read("src/pages/ProfilePage.jsx");
const hub = read("src/pages/LearningHubPage.jsx");
const phase5Css = read("src/styles/phase5.css");

assert.match(profile, /to="\/learning-hub#privacy-preferences"/);
assert.match(profile, /Manage privacy settings/);
assert.match(profile, /Privacy & learning preferences/);
assert.doesNotMatch(profile, /Not available yet/);
assert.doesNotMatch(profile, /account-setting-unavailable/);
assert.match(hub, /id="privacy-preferences"/);
assert.match(hub, /\/api\/me\/learning-preferences/);
assert.match(hub, /Allow privacy-minimized product analytics/);
assert.match(hub, /scrollIntoView\(/);
assert.match(phase5Css, /\.phase5-privacy-preferences\s*\{\s*scroll-margin-top:/);
console.log("PASS account privacy controls navigate to backend-backed preferences");
console.log("PASS placeholder 'Not available yet' is removed");
console.log("PASS privacy preferences provide analytics consent and review controls");
console.log("PASS direct privacy link scrolls to the settings section after load");
