import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../src/pages/PlaygroundPage.jsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../src/styles/learning-workspaces.css", import.meta.url), "utf8");
const workspace = readFileSync(new URL("../src/lib/languageWorkspace.js", import.meta.url), "utf8");

assert.match(page, /browserActiveFile \? <Monitor size=\{15\}/);
assert.match(page, /CODELEAF TERMINAL/);
assert.match(page, /browserActiveFile \? "Preview" : "Terminal"/);
assert.match(page, /stdout/);
assert.match(page, /stderr \/ result/);
assert.match(page, /currently accepts Python and JavaScript only/);
assert.match(styles, /\.workspace-terminal-idle/);
assert.match(workspace, /execution: "browser-html"/);
assert.match(workspace, /export function isBrowserWorkspace/);

console.log("Playground browser-preview and terminal-output contract checks passed.");
