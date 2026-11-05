import assert from "node:assert/strict";
import {
  resolveLanguage,
  getLanguageForFilename,
  starterFiles,
  detectOutputMode,
  createSassPreviewDocument,
  createAngularJSPreviewDocument,
  defaultSourceForLanguage,
} from "../src/lib/languageWorkspace.js";

const pistonKeys = ["c", "cpp", "python", "python2", "javascript", "typescript", "java", "csharp", "go", "rust", "php", "ruby", "kotlin", "swift", "dart", "r", "bash", "powershell", "lua", "perl", "scala", "groovy", "haskell", "elixir", "erlang", "clojure", "ocaml", "fsharp", "fortran", "cobol", "pascal", "raku", "julia", "octave", "nim", "zig", "crystal", "vlang", "d", "freebasic", "basic", "basicnet", "cjam", "brainfuck", "befunge93", "awk", "dash", "sqlite", "prolog", "racket", "lisp", "smalltalk", "emacslisp", "coffeescript", "fsi", "llvmir", "nasm", "nasm64", "iverilog", "ponylang", "emojicode", "forte", "forth", "dragon", "cow", "husk", "jelly", "rockstar", "vyxal", "matl", "golfscript", "osabie", "pyth", "samarium", "retina", "bqn", "japt", "brachylog", "paradoc", "yeethon", "pure"];
for (const key of pistonKeys) {
  const language = resolveLanguage(key, key);
  assert.equal(language.key, key, `${key} should resolve to the exact Runner registry key`);
  const files = starterFiles({ courseSlug: key, codeLanguage: key });
  assert.ok(files.length > 0, `${key} should create a starter file`);
  assert.equal(
    getLanguageForFilename(files[0].name, key).key,
    key,
    `${files[0].name} should retain the ${key} runtime key`,
  );
  const mode = detectOutputMode({
    currentFile: files[0],
    files,
    runnerCapabilities: [key],
  });
  assert.equal(mode.mode, "terminal", `${key} should use isolated terminal execution`);
  assert.equal(mode.runnerSupported, true, `${key} should reflect the live runtime capability`);
}

const structuredKeys = ["xml", "json", "yaml", "excel", "markdown", "plain", "docker", "aws", "githubactions", "git", "toml", "redis"];
const playgroundSource = (await import("node:fs/promises")).readFile;
const page = await playgroundSource(new URL("../src/pages/PlaygroundPage.jsx", import.meta.url), "utf8");
for (const key of structuredKeys) {
  assert.ok(page.includes(`"${key}"`), `Playground should register structured tool ${key}`);
}
assert.ok(page.includes("/api/playground/tools/run"), "Playground should call the authenticated format-tool API");
assert.ok(page.includes("runStructuredTool"), "Playground should route structured formats to their tool adapter");

console.log(`PASS: ${pistonKeys.length} Piston language keys resolve to starter files and terminal capability mode.`);
console.log(`PASS: ${structuredKeys.length} structured/simulator types route through the dedicated safe Playground tool API.`);

const sassFile = { name: "styles.scss", language: "sass", content: "$accent: teal; .card { color: $accent; }" };
const sassMode = detectOutputMode({ currentFile: sassFile, files: [sassFile], runnerCapabilities: [] });
assert.equal(sassMode.mode, "sass-preview");
const sassDoc = createSassPreviewDocument(sassFile.content);
assert.ok(sassDoc.includes("https://jspm.dev/sass"), "Sass should load the Dart Sass browser compiler");
assert.ok(sassDoc.includes("compileString"), "Sass source should be compiled, not merely displayed");
assert.ok(sassDoc.includes("data-codeleaf-compiled-sass"), "Compiled CSS should be applied to the preview");
const sassInjection = createSassPreviewDocument("</script><script>alert(1)</script>");
assert.ok(!sassInjection.includes("</script><script>alert(1)"), "Sass source must be escaped in the generated iframe");

const angularSource = defaultSourceForLanguage("angularjs");
const angularFile = { name: "app.js", language: "angularjs", content: angularSource };
const angularMode = detectOutputMode({ currentFile: angularFile, files: [angularFile], runnerCapabilities: [] });
assert.equal(angularMode.mode, "angularjs-preview");
const angularDoc = createAngularJSPreviewDocument(angularSource);
assert.ok(angularDoc.includes("https://cdnjs.cloudflare.com/ajax/libs/angular.js/1.8.3/angular.min.js"));
assert.ok(angularDoc.includes('ng-app="codeleafApp"'));
assert.ok(angularDoc.includes('ng-controller="MainController"'));
assert.ok(angularDoc.includes('sandbox') === false, "The iframe sandbox attribute is owned by the Playground component, not its document.");

const playgroundSourceText = await playgroundSource(new URL("../src/pages/PlaygroundPage.jsx", import.meta.url), "utf8");
assert.ok(playgroundSourceText.includes('sandbox="allow-scripts"'), "Preview must run in a script-only sandbox.");
assert.ok(playgroundSourceText.includes("createSassPreviewDocument"));
assert.ok(playgroundSourceText.includes("createAngularJSPreviewDocument"));
console.log("PASS: Sass compiles and previews in an isolated browser document.");
console.log("PASS: AngularJS starter code runs in its isolated browser runtime.");
