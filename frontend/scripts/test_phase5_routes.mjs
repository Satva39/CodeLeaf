import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(resolve(here, "../src/App.jsx"), "utf8");
const header = readFileSync(resolve(here, "../src/components/layout/Header.jsx"), "utf8");
const pageChecks = [
  ["LearningHubPage", "/learning-hub"],
  ["PortfolioPage", "/portfolio"],
  ["ContentStudioPage", "/content-studio"],
  ["ReviewPage", "/review"],
];
for (const [component, route] of pageChecks) {
  assert.match(app, new RegExp(`import ${component} from \\"\\./pages/${component}\\.jsx\\";`), `${component} import exists`);
  assert.ok(app.includes(`path=\"${route}\"`) || app.includes(`path=\"${route}/:username\"`), `${route} route exists`);
  console.log(`PASS ${component} is registered`);
}
assert.ok(header.includes('to="/learning-hub"'), "Learning hub is reachable from the main navigation");
assert.ok(header.includes('to="/portfolio"'), "Portfolio is reachable from the main navigation");
assert.ok(header.includes('to="/review"'), "Review queue is reachable from the main navigation");
console.log("PASS Phase 3 review and Phase 5 learner routes are integrated");
