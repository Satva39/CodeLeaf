import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const page = fs.readFileSync(path.join(root, "src/pages/PlaygroundPage.jsx"), "utf8");
const tryIt = fs.readFileSync(path.join(root, "src/pages/TryItPage.jsx"), "utf8");

assert.match(page, /\/api\/runner\/status/);
assert.match(page, /runnerConfigured/);
assert.match(page, /runnerConfigChecked/);
assert.match(page, /runnerAvailabilityPending/);
assert.match(page, /disabled=\{running \|\| runnerAvailabilityPending\}/);
assert.match(page, /runnerAvailabilityPending \? "Checking…"/);
assert.match(page, /if \(!runnerConfigured\)/);
assert.match(page, /source remains editable and has not been executed/);
assert.match(page, /No server-side execution provider is configured yet/);

assert.match(tryIt, /\/api\/runner\/status/);
assert.match(tryIt, /runnerCapabilitiesChecked/);
assert.match(tryIt, /runnerAvailabilityPending/);
assert.match(tryIt, /disabled=\{running \|\| !code\.trim\(\) \|\| runnerAvailabilityPending\}/);
assert.match(tryIt, /runnerAvailabilityPending \? "Checking…"/);

console.log("PASS Try It and Playground prevent premature server execution while runner availability is loading");
