import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd());
const page = readFileSync(resolve(root, "src/pages/CourseDirectoryPage.jsx"), "utf8");
const styles = readFileSync(resolve(root, "src/styles/ui-polish.css"), "utf8");

function check(condition, message) {
  if (!condition) throw new Error(`FAIL ${message}`);
  console.log(`PASS ${message}`);
}

check(/className="button button-secondary button-small collection-clear-filters"/.test(page), "Clear filters uses the shared secondary-button design instead of browser-default styling");
check(/aria-label="Clear all project filters"/.test(page), "Clear filters button has an accessible label");
check(/\.collection-directory-toolbar \.collection-clear-filters:hover/.test(styles), "Clear filters has a theme-matched hover state");
check(/\.collection-directory-toolbar \.collection-clear-filters:focus-visible/.test(styles), "Clear filters has a visible keyboard-focus state");
check(/\.collection-directory-toolbar > \.collection-clear-filters \{ order: 4; \}/.test(styles), "Clear filters stays in the intended order on narrow screens");
console.log("All project directory Clear filters tests passed.");
