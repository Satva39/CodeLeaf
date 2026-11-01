import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  createBrowserDocument,
  createReactPreviewDocument,
  detectOutputMode,
  getLanguageForFilename,
  isBrowserWorkspace,
} from "../src/lib/languageWorkspace.js";

const page = readFileSync(new URL("../src/pages/PlaygroundPage.jsx", import.meta.url), "utf8");
const tryIt = readFileSync(new URL("../src/pages/TryItPage.jsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../src/styles/learning-workspaces.css", import.meta.url), "utf8");
const workspaceSource = readFileSync(new URL("../src/lib/languageWorkspace.js", import.meta.url), "utf8");
const runner = ["python", "javascript"];

const files = [
  { name: "index.html", content: '<!doctype html><html><head><link rel="stylesheet" href="style.css"><script src="main.js"></script></head><body><h1>CodeLeaf</h1></body></html>' },
  { name: "style.css", content: "h1 { color: green; }" },
  { name: "main.js", content: "console.log('linked JavaScript');" },
  { name: "main.py", content: "print('connected Python')" },
  { name: "main.c", content: '#include <stdio.h>\nint main(void){return 0;}' },
  { name: "main.cpp", content: "int main(){return 0;}" },
  { name: "query.sql", content: "select 1;" },
  { name: "server.js", language: "expressjs", content: "console.log('server')" },
];

assert.equal(detectOutputMode({ currentFile: files[0], files, runnerCapabilities: runner }).mode, "browser-preview", "HTML should render in browser preview");
assert.equal(detectOutputMode({ currentFile: files[1], files, runnerCapabilities: runner }).mode, "browser-preview", "CSS should render against its HTML project");
assert.equal(detectOutputMode({ currentFile: files[2], files, runnerCapabilities: runner }).mode, "browser-preview", "JavaScript referenced by HTML should preview");
assert.equal(detectOutputMode({ currentFile: files[3], files, runnerCapabilities: runner }).mode, "terminal", "Python must use the terminal unless explicitly connected");
assert.equal(detectOutputMode({ currentFile: files[4], files, runnerCapabilities: runner }).mode, "terminal", "C must use terminal output");
assert.equal(detectOutputMode({ currentFile: files[5], files, runnerCapabilities: runner }).mode, "terminal", "C++ must use terminal output");
assert.equal(detectOutputMode({ currentFile: files[6], files, runnerCapabilities: runner }).mode, "terminal", "SQL must use terminal/query output, not a browser");
assert.equal(detectOutputMode({ currentFile: files[3], files: [files[3], files[0]], runnerCapabilities: runner }).mode, "terminal", "the mere presence of HTML must not connect Python");
assert.equal(detectOutputMode({ currentFile: files[2], files: [files[2]], runnerCapabilities: runner }).mode, "terminal", "unlinked JavaScript should use the JavaScript runner");
assert.equal(getLanguageForFilename(files[7].name, files[7].language).key, "expressjs", "explicit server framework metadata should survive a .js filename");
assert.equal(detectOutputMode({ currentFile: files[7], files, runnerCapabilities: ["expressjs"] }).mode, "terminal", "Express server files must use terminal output, not a browser preview");

const connection = { enabled: true, mode: "stdout-bridge", entryFile: "index.html", languageFile: "main.py", language: "python" };
const connected = detectOutputMode({ currentFile: files[3], files, runnerCapabilities: runner, webConnection: connection });
assert.equal(connected.mode, "connected-preview", "an explicit connection should enable an integrated preview");
assert.equal(connected.entryFile, "index.html");
assert.equal(detectOutputMode({ currentFile: files[3], files, runnerCapabilities: ["javascript"], webConnection: connection }).mode, "terminal", "a connection must not bypass runner capabilities");
assert.equal(detectOutputMode({ currentFile: files[3], files, runnerCapabilities: runner, webConnection: null }).mode, "terminal", "removing the connection restores terminal mode");

const htmlDocument = createBrowserDocument(files, "codeleaf-test", {
  entryFile: "index.html",
  connectedOutput: { language: "python", stdout: "connected Python", stderr: "", exit_code: 0 },
});
assert.match(htmlDocument, /Content-Security-Policy/);
assert.match(htmlDocument, /connect-src 'none'/);
assert.match(htmlDocument, /h1 \{ color: green; \}/, "linked CSS should be inlined into the HTML preview");
assert.match(htmlDocument, /linked JavaScript/, "the referenced local JavaScript should be inlined");
assert.doesNotMatch(htmlDocument, /href="style.css"/, "the preview should not depend on an unavailable workspace file server");
assert.match(htmlDocument, /CODELEAF_CONNECTED_OUTPUT/, "connected server stdout is passed into the sandbox preview");

const jsx = [{ name: "App.jsx", content: "export default function App(){ return <h1>Hello React</h1>; }" }, { name: "App.css", content: "h1 { color: red; }" }];
assert.equal(detectOutputMode({ currentFile: jsx[0], files: jsx, runnerCapabilities: runner }).mode, "react-preview");
const reactDocument = createReactPreviewDocument(jsx, "App.jsx", "codeleaf-test");
assert.match(reactDocument, /@babel\/standalone/);
assert.match(reactDocument, /@remix-run\/router@1\.21\.0\/dist\/router\.umd\.js/, "React Router's Remix router UMD dependency should load first");
assert.match(reactDocument, /react-router@6\.28\.0\/dist\/umd\/react-router\.development\.js/, "React Router core UMD should load before React Router DOM");
assert.match(reactDocument, /react-router-dom@6\.28\.0\/dist\/umd\/react-router-dom\.development\.js/);
assert.match(reactDocument, /ReactDOM\.createRoot/);
assert.match(reactDocument, /Unsupported React preview dependency/);
assert.match(reactDocument, /connect-src 'none'/, "React preview must keep its network boundary closed");

assert.equal(isBrowserWorkspace(files), true);
assert.equal(getLanguageForFilename("app.jsx").key, "jsx");
assert.match(page, /detectOutputMode\(/);
assert.match(page, /CODELEAF TERMINAL/);
assert.match(page, /codeleaf:language-output/);
assert.match(page, /sandbox="allow-scripts"/);
assert.match(page, /runnerSupportedLanguages/);
assert.match(tryIt, /detectOutputMode\(/);
assert.match(tryIt, /createReactPreviewDocument/);
assert.match(styles, /\.workspace-terminal-idle/);
assert.match(styles, /workspace-web-connection-help/);
assert.match(workspaceSource, /export function detectOutputMode/);
assert.match(workspaceSource, /export function isBrowserWorkspace/);

console.log("PASS centralized runner modes: HTML/CSS/React preview, referenced JavaScript preview, explicit server-language connection, terminal defaults and unsupported-runtime boundaries.");
