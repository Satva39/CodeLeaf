import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const playground = readFileSync(new URL("../src/pages/PlaygroundPage.jsx", import.meta.url), "utf8");
const tryIt = readFileSync(new URL("../src/pages/TryItPage.jsx", import.meta.url), "utf8");
const frontendFiles = [
  "../src/pages/PlaygroundPage.jsx",
  "../src/pages/TryItPage.jsx",
  "../src/lib/apiClient.js",
].map((path) => readFileSync(new URL(path, import.meta.url), "utf8"));
const frontendSource = frontendFiles.join("\n");

assert.match(playground, /RUNNER_MAX_FILES\s*=\s*10/);
assert.match(playground, /RUNNER_MAX_FILE_BYTES\s*=\s*65_536/);
assert.match(playground, /RUNNER_MAX_TOTAL_BYTES\s*=\s*131_072/);
assert.match(playground, /requestBody\.files\s*=\s*projectFiles\.map/);
assert.match(playground, /requestBody\.setup_sql\s*=\s*setupSql/);
assert.match(playground, /Database setup SQL/);
assert.match(tryIt, /setup_sql:\s*databaseSetupSql/);
assert.match(tryIt, /Database setup SQL/);
assert.match(tryIt, /idempotency_key/);
assert.doesNotMatch(frontendSource, /RUNNER_SERVICE_TOKEN|X-Runner-Key|CODELEAF_RUNNER_SERVICE_TOKEN/);

console.log("PASS Phase 6 frontend: multi-file payloads, Runner limits, SQL setup, idempotency, and no browser-held service token");
