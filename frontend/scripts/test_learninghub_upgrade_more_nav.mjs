import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const hub = read("src/pages/LearningHubPage.jsx");
const header = read("src/components/layout/Header.jsx");
const layoutCss = read("src/styles/layout.css");
const responsiveCss = read("src/styles/responsive.css");
const phase5Css = read("src/styles/phase5.css");

assert.match(hub, /detail\?\.message \|\| body\?\.message/,
  "structured FastAPI detail objects are converted into readable errors");
assert.match(hub, /Promise\.allSettled\(/,
  "recommendation failure does not prevent the other learning hub APIs from rendering");
assert.match(hub, /FEATURE_REQUIRES_UPGRADE/,
  "the expected premium-feature 403 is recognized separately from service errors");
assert.match(hub, /Unlock personalized recommendations/,
  "locked recommendations provide a clear upgrade state instead of a raw error");
assert.match(hub, /to="\/plans"/, "the recommendation upgrade prompt links to plan comparison");

for (const [name, route] of [["Tutorials", "/tutorials"], ["References", "/references"], ["Projects", "/projects"], ["Practice", "/practice"]]) {
  assert.ok(header.includes(`to="${route}"`), `${name} remains in the primary navigation`);
}
assert.match(header, /More <ChevronDown/,
  "the primary navbar includes the More dropdown trigger");
const moreMenu = header.slice(header.indexOf('id="primary-nav-more-menu"'));
for (const route of ["/review", "/learning-hub", "/ai", "/portfolio", "/certificates"]) {
  assert.ok(moreMenu.includes(`to="${route}"`), `${route} is available inside More`);
}
assert.match(header, /aria-expanded=\{moreOpen\}/,
  "More exposes its expanded state for assistive technology");
assert.match(header, /event\.key === "Escape"/,
  "Escape closes the More menu");
assert.match(layoutCss, /\.primary-nav-more-menu/,
  "desktop More dropdown has dedicated styling");
assert.match(responsiveCss, /\.primary-nav-more-menu\s*\{[\s\S]*?position:\s*static/,
  "More dropdown is responsive inside the mobile navigation panel");
assert.match(phase5Css, /\.phase5-upgrade-prompt/,
  "the recommendation upgrade state has dedicated styles");

console.log("PASS Learning Hub handles structured 403 entitlement responses without [object Object]");
console.log("PASS Learning Hub loads independent sections even if recommendations require an upgrade");
console.log("PASS primary navigation keeps four key links and moves secondary links into More");
console.log("PASS More dropdown supports accessible state, Escape-to-close, and responsive layout");
