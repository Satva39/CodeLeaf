const LANGUAGE_CONFIGS = {
  html: { label: "HTML", extension: "html", filename: "index.html", execution: "browser-html" },
  css: { label: "CSS", extension: "css", filename: "styles.css", execution: "browser-html" },
  javascript: { label: "JavaScript", extension: "js", filename: "script.js", execution: "runner-javascript" },
  typescript: { label: "TypeScript", extension: "ts", filename: "main.ts", execution: "static" },
  python: { label: "Python", extension: "py", filename: "main.py", execution: "runner-python" },
  c: { label: "C", extension: "c", filename: "main.c", execution: "static" },
  cpp: { label: "C++", extension: "cpp", filename: "main.cpp", execution: "static" },
  csharp: { label: "C#", extension: "cs", filename: "Program.cs", execution: "static" },
  java: { label: "Java", extension: "java", filename: "Main.java", execution: "static" },
  php: { label: "PHP", extension: "php", filename: "index.php", execution: "static" },
  sql: { label: "SQL", extension: "sql", filename: "query.sql", execution: "static" },
  postgresql: { label: "PostgreSQL", extension: "sql", filename: "query.sql", execution: "static" },
  mysql: { label: "MySQL", extension: "sql", filename: "query.sql", execution: "static" },
  sqlite: { label: "SQLite", extension: "sql", filename: "query.sql", execution: "static" },
  redis: { label: "Redis CLI", extension: "redis", filename: "commands.redis", execution: "static" },
  bash: { label: "Bash", extension: "sh", filename: "main.sh", execution: "static" },
  powershell: { label: "PowerShell", extension: "ps1", filename: "main.ps1", execution: "static" },
  r: { label: "R", extension: "r", filename: "main.R", execution: "static" },
  go: { label: "Go", extension: "go", filename: "main.go", execution: "static" },
  rust: { label: "Rust", extension: "rs", filename: "main.rs", execution: "static" },
  kotlin: { label: "Kotlin", extension: "kt", filename: "Main.kt", execution: "static" },
  swift: { label: "Swift", extension: "swift", filename: "main.swift", execution: "static" },
  dart: { label: "Dart", extension: "dart", filename: "main.dart", execution: "static" },
  ruby: { label: "Ruby", extension: "rb", filename: "main.rb", execution: "static" },
  lua: { label: "Lua", extension: "lua", filename: "main.lua", execution: "static" },
  solidity: { label: "Solidity", extension: "sol", filename: "Contract.sol", execution: "static" },
  json: { label: "JSON / YAML", extension: "json", filename: "data.json", execution: "static" },
  xml: { label: "XML", extension: "xml", filename: "document.xml", execution: "static" },
  jsx: { label: "React / JSX", extension: "jsx", filename: "App.jsx", execution: "browser-react" },
  vue: { label: "Vue", extension: "vue", filename: "App.vue", execution: "static" },
  sass: { label: "Sass", extension: "scss", filename: "styles.scss", execution: "static" },
  asp: { label: "ASP", extension: "asp", filename: "default.asp", execution: "static" },
  excel: { label: "Excel", extension: "csv", filename: "data.csv", execution: "static" },
  docker: { label: "Docker", extension: "Dockerfile", filename: "Dockerfile", execution: "static" },
  dsa: { label: "Algorithms", extension: "py", filename: "main.py", execution: "runner-python" },
  plain: { label: "Text", extension: "txt", filename: "notes.txt", execution: "static" },
  yaml: { label: "YAML / CI config", extension: "yml", filename: "config.yml", execution: "static" },
  angular: { label: "Angular", extension: "ts", filename: "app.component.ts", execution: "static" },
  angularjs: { label: "AngularJS", extension: "js", filename: "app.js", execution: "static" },
  bootstrap: { label: "Bootstrap", extension: "html", filename: "index.html", execution: "browser-html" },
  git: { label: "Git", extension: "md", filename: "README.md", execution: "static" },
  tailwind: { label: "Tailwind CSS", extension: "html", filename: "index.html", execution: "browser-html" },
  django: { label: "Django / Python", extension: "py", filename: "views.py", execution: "static" },
  flask: { label: "Flask / Python", extension: "py", filename: "app.py", execution: "static" },
  expressjs: { label: "Express.js", extension: "js", filename: "server.js", execution: "static" },
  fastapi: { label: "FastAPI / Python", extension: "py", filename: "main.py", execution: "static" },
  data: { label: "Data science / Python", extension: "py", filename: "analysis.py", execution: "static" },
  aws: { label: "AWS configuration", extension: "yml", filename: "template.yml", execution: "static" },
  githubactions: { label: "GitHub Actions", extension: "yml", filename: "workflow.yml", execution: "static" },
  markdown: { label: "Markdown", extension: "md", filename: "README.md", execution: "static" },
};

function normalizeToken(value) {
  return String(value || "").trim().toLowerCase().replaceAll("\\", "/").replace(/\s+/g, " ");
}

export function resolveLanguage(courseSlug = "html", codeLanguage = "") {
  const values = [normalizeToken(codeLanguage), normalizeToken(courseSlug)].filter(Boolean);
  const aliases = [
    [["c++", "cpp", "c plus plus", "c/c++"], "cpp"],
    [["c#", "csharp", "c sharp", "c-sharp"], "csharp"],
    [["javascript", "java script", "js", "node", "node.js", "nodejs"], "javascript"],
    [["typescript", "type script", "ts"], "typescript"],
    [["python", "python3", "py"], "python"],
    [["postgresql", "postgres", "postgre sql"], "postgresql"],
    [["mysql", "my sql"], "mysql"],
    [["sqlite", "sqlite3"], "sqlite"],
    [["react", "jsx", "react.js", "reactjs", "nextjs", "next.js"], "jsx"],
    [["angular"], "angular"], [["angularjs", "angular.js"], "angularjs"],
    [["vue", "vue.js", "vuejs"], "vue"],
    [["bootstrap"], "bootstrap"], [["tailwind", "tailwind-css", "tailwind css"], "tailwind"],
    [["django"], "django"], [["flask"], "flask"], [["expressjs", "express.js", "express", "node", "node.js", "nodejs"], "expressjs"],
    [["fastapi"], "fastapi"], [["numpy", "pandas", "scipy", "pytorch", "scikit-learn", "scikit learn", "data-science", "data science", "generative-ai", "generative ai", "cybersecurity", "web-application-security"], "data"],
    [["aws", "cloudformation"], "aws"], [["github-actions", "github actions"], "githubactions"],
    [["ai", "artificial intelligence"], "data"],
    [["git", "version control"], "git"], [["markdown", "md"], "markdown"],
    [["jquery"], "javascript"], [["mongodb"], "javascript"], [["redis"], "redis"], [["linux"], "bash"],
    [["rest-api-development", "rest api development"], "javascript"], [["json-yaml", "json and yaml"], "yaml"],
    [["sass", "scss"], "sass"],
    [["html", "html5"], "html"],
    [["css", "css3"], "css"],
    [["sql", "database query"], "sql"],
    [["c", "c language", "c programming"], "c"],
    [["php"], "php"], [["java"], "java"], [["python"], "python"],
    [["bash", "shell", "shell script"], "bash"],
    [["powershell", "ps1"], "powershell"],
    [["rust", "rustlang"], "rust"], [["golang", "go language", "go"], "go"],
    [["kotlin"], "kotlin"], [["swift"], "swift"], [["dart", "flutter"], "dart"],
    [["ruby", "rb"], "ruby"], [["lua"], "lua"], [["r", "r language", "r programming"], "r"],
    [["xml"], "xml"], [["json"], "json"], [["yaml", "yml", "json and yaml", "json-yaml"], "yaml"],
    [["solidity"], "solidity"], [["asp", "asp.net"], "asp"],
    [["excel", "spreadsheet"], "excel"], [["docker", "dockerfile"], "docker"],
    [["dsa", "data structures and algorithms"], "dsa"],
  ];
  for (const value of values) {
    for (const [names, key] of aliases) {
      if (names.includes(value)) return { key, ...LANGUAGE_CONFIGS[key] };
    }
    if (value.includes("c++")) return { key: "cpp", ...LANGUAGE_CONFIGS.cpp };
    if (value.includes("c#") || value.includes("csharp")) return { key: "csharp", ...LANGUAGE_CONFIGS.csharp };
    if (value.includes("python")) return { key: "python", ...LANGUAGE_CONFIGS.python };
    if (value.includes("javascript") || value === "js") return { key: "javascript", ...LANGUAGE_CONFIGS.javascript };
    if (value.includes("typescript")) return { key: "typescript", ...LANGUAGE_CONFIGS.typescript };
  }
  return { key: "plain", ...LANGUAGE_CONFIGS.plain };
}

export function defaultSourceForLanguage(languageKey) {
  const examples = {
    plain: "Write notes or pseudocode here.\n",
    redis: "SET greeting \"Hello, CodeLeaf!\"\nGET greeting\nINCR page:views\nGET page:views\n",
    aws: "AWSTemplateFormatVersion: '2010-09-09'\nDescription: Minimal example template\nResources: {}\n",
    githubactions: "name: CodeLeaf checks\non: [push, pull_request]\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: echo 'Add your validation command here'\n",
    angular: "import { Component } from '@angular/core';\n\n@Component({ selector: 'app-root', template: `<h1>{{ title }}</h1>` })\nexport class AppComponent { title = 'Hello, Angular!'; }\n",
    angularjs: "const app = angular.module('codeleafApp', []);\napp.controller('MainController', function ($scope) {\n  $scope.message = 'Hello, AngularJS!';\n});\n",
    bootstrap: "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Bootstrap demo</title></head><body><main class=\"container py-4\"><h1 class=\"text-success\">Hello, Bootstrap!</h1><p>Edit this HTML and preview it.</p></main></body></html>",
    tailwind: "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Tailwind demo</title></head><body><main class=\"mx-auto max-w-3xl p-8\"><h1 class=\"text-3xl font-bold\">Hello, Tailwind CSS!</h1><p>Utility classes are visible in source; add local CSS to experiment without a network dependency.</p></main></body></html>",
    git: "# CodeLeaf Git notes\n\n- `git status` shows working-tree changes.\n- `git add` stages selected files.\n- `git commit` records a checkpoint.\n",
    django: "from django.http import HttpResponse\n\ndef home(request):\n    return HttpResponse(\"Hello, Django!\")\n",
    flask: "from flask import Flask\n\napp = Flask(__name__)\n\n@app.get(\"/\")\ndef home():\n    return \"Hello, Flask!\"\n",
    expressjs: "const express = require('express');\nconst app = express();\n\napp.get('/', (_req, res) => res.send('Hello, Express!'));\napp.listen(3000);\n",
    fastapi: "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\ndef home():\n    return {\"message\": \"Hello, FastAPI!\"}\n",
    data: "# Start with a small, reproducible analysis.\nvalues = [12, 18, 21, 21, 28]\nmean = sum(values) / len(values)\nprint(f\"count={len(values)}, mean={mean:.1f}\")\n",
    html: "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>My CodeLeaf Page</title>\n</head>\n<body>\n  <h1>Hello, CodeLeaf!</h1>\n  <p>Edit this example and run it.</p>\n</body>\n</html>",
    css: "body {\n  font-family: system-ui, sans-serif;\n  margin: 2rem;\n}\n\nh1 { color: #0da875; }",
    javascript: "console.log('Hello from CodeLeaf!');",
    typescript: "const greeting: string = 'Hello from CodeLeaf!';\nconsole.log(greeting);",
    python: "name = input('What is your name? ')\nprint(f'Hello, {name}!')",
    c: "#include <stdio.h>\n\nint main(void) {\n    printf(\"Hello, C!\\n\");\n    return 0;\n}",
    cpp: "#include <iostream>\n\nint main() {\n    std::cout << \"Hello, C++!\\n\";\n    return 0;\n}",
    csharp: "using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine(\"Hello, C#!\");\n    }\n}",
    java: "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, Java!\");\n    }\n}",
    php: "<?php\necho \"Hello, PHP!\" . PHP_EOL;",
    sql: "SELECT 'Hello, CodeLeaf!' AS message;",
    postgresql: "SELECT version();",
    mysql: "SELECT VERSION();",
    sqlite: "SELECT sqlite_version();",
    bash: "#!/usr/bin/env bash\nprintf '%s\\n' 'Hello, CodeLeaf!'",
    powershell: "Write-Output 'Hello, CodeLeaf!'",
    r: "message <- 'Hello, CodeLeaf!'\nprint(message)",
    go: "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"Hello, Go!\")\n}",
    rust: "fn main() {\n    println!(\"Hello, Rust!\");\n}",
    kotlin: "fun main() {\n    println(\"Hello, Kotlin!\")\n}",
    swift: "print(\"Hello, Swift!\")",
    dart: "void main() {\n  print('Hello, Dart!');\n}",
    ruby: "puts 'Hello, Ruby!'",
    lua: "print('Hello, Lua!')",
    solidity: "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\n\ncontract HelloCodeLeaf {\n    string public message = \"Hello, CodeLeaf!\";\n}",
    json: "{\n  \"message\": \"Hello, CodeLeaf!\"\n}",
    yaml: "name: codeleaf-demo\nversion: 1\nmessage: Hello, CodeLeaf!\n",
    markdown: "# Hello, CodeLeaf!\n\nWrite notes, explain the concept, and link useful resources.\n",
    xml: "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<message>Hello, CodeLeaf!</message>",
    jsx: "export default function App() {\n  return <h1>Hello, CodeLeaf!</h1>;\n}",
    vue: "<template>\n  <h1>Hello, CodeLeaf!</h1>\n</template>\n\n<script setup>\n</script>",
    sass: "$accent: #0da875;\n\nbody\n  font-family: system-ui, sans-serif\n\nh1\n  color: $accent",
    asp: "<% Response.Write(\"Hello, CodeLeaf!\") %>",
    excel: "name,message\nCodeLeaf,Hello!",
    docker: "FROM python:3.13-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"main.py\"]",
    dsa: "def main():\n    print('Hello, CodeLeaf!')\n\nif __name__ == '__main__':\n    main()",
  };
  return examples[languageKey] || "# Start writing here.\n";
}

export function starterFiles({ courseSlug = "html", codeLanguage = "", source = "", title = "" } = {}) {
  const language = resolveLanguage(courseSlug, codeLanguage);
  const code = typeof source === "string" && source.trim() ? source : defaultSourceForLanguage(language.key);
  const makeFile = (name, content, languageKey = language.key) => ({
    id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}-${name}`,
    name,
    language: languageKey,
    content,
  });
  if (language.execution === "browser-html") {
    const htmlFile = makeFile(
      "index.html",
      ["html", "bootstrap", "tailwind"].includes(language.key) ? code : defaultSourceForLanguage("html"),
      "html",
    );
    const cssFile = makeFile(
      "styles.css",
      language.key === "css" ? code : "body { font-family: system-ui, sans-serif; padding: 2rem; }\nh1 { color: #0da875; }",
      "css",
    );
    const jsFile = makeFile("script.js", defaultSourceForLanguage("javascript"), "javascript");
    // When a learner comes from a CSS lesson, make the CSS their active first tab,
    // while still retaining the HTML document for the preview.
    return language.key === "css" ? [cssFile, htmlFile, jsFile] : [htmlFile, cssFile, jsFile];
  }
  const filename = title && language.key === "plain"
    ? `${String(title).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "notes"}.${language.extension}`
    : language.filename;
  return [makeFile(filename, code, language.key)];
}

export function safeWorkspaceFilename(value) {
  const name = String(value || "").trim();
  if (!name || name.length > 100 || name === "." || name === ".." || name === "__codeleaf_project_config__.json") return false;
  if (/[<>:"/\\|?*\x00-\x1f]/.test(name)) return false;
  return !name.endsWith(".");
}

export function openSeededWorkspace(mode, payload = {}) {
  if (typeof window === "undefined") return false;
  const seed = typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
  try {
    window.localStorage.setItem(`codeleaf:workspace-seed:${seed}`, JSON.stringify(payload));
  } catch {
    return false;
  }
  const course = encodeURIComponent(payload.courseSlug || "html");
  const lesson = encodeURIComponent(payload.lessonSlug || "");
  const url = mode === "try"
    ? `/try/${course}${lesson ? `/${lesson}` : ""}?seed=${encodeURIComponent(seed)}`
    : `/playground?seed=${encodeURIComponent(seed)}&language=${encodeURIComponent(payload.language || payload.courseSlug || "html")}`;
  const popup = window.open(url, "_blank");
  if (popup) { try { popup.opener = null; } catch { /* Browser may deny opener updates. */ } }
  else window.location.assign(url);
  return true;
}

export function getLanguageForFilename(filename) {
  const name = String(filename || "").toLowerCase();
  const ext = name.includes(".") ? name.split(".").pop() : name;
  const byExtension = {
    html: "html", htm: "html", css: "css", js: "javascript", mjs: "javascript", cjs: "javascript",
    py: "python", c: "c", h: "c", cpp: "cpp", cc: "cpp", cxx: "cpp", hpp: "cpp",
    cs: "csharp", java: "java", php: "php", sql: "sql", r: "r", go: "go", rs: "rust", kt: "kotlin",
    swift: "swift", dart: "dart", rb: "ruby", lua: "lua", sh: "bash", bash: "bash", ps1: "powershell",
    ts: "typescript", tsx: "typescript", jsx: "jsx", vue: "vue", scss: "sass", sass: "sass", xml: "xml",
    json: "json", yaml: "yaml", yml: "yaml", md: "markdown", redis: "redis", sol: "solidity", csv: "excel", asp: "asp", txt: "plain",
  };
  const key = byExtension[ext] || (name === "dockerfile" ? "docker" : "plain");
  return { key, ...LANGUAGE_CONFIGS[key] };
}

export function compatibleFilename(candidate, language) {
  const name = String(candidate || "").trim();
  if (name && safeWorkspaceFilename(name) && getLanguageForFilename(name).key === language?.key) {
    return name;
  }
  return language?.filename || "notes.txt";
}

function filenameOf(value) {
  return String(value || "").trim().replaceAll("\\", "/").split("/").pop().toLowerCase();
}

function findFileByName(files, name) {
  const target = filenameOf(name);
  if (!target) return null;
  return (Array.isArray(files) ? files : []).find((file) => filenameOf(file?.name) === target) || null;
}

function referencedLocalFiles(html, tagName, attributeName) {
  const references = [];
  const tagPattern = new RegExp(`<${tagName}\\b[^>]*>`, "gi");
  const attributePattern = new RegExp(`\\b${attributeName}\\s*=\\s*(["'])(.*?)\\1`, "i");
  for (const tag of String(html || "").match(tagPattern) || []) {
    const match = tag.match(attributePattern);
    if (!match) continue;
    const value = match[2].trim();
    if (!value || /^(?:[a-z]+:|\/\/|#|data:)/i.test(value)) continue;
    references.push(filenameOf(value.split(/[?#]/)[0]));
  }
  return references.filter(Boolean);
}

/**
 * One resolver is shared by Try It and the multi-file Playground. It deliberately
 * does not infer a web connection from the mere presence of index.html.
 */
export function detectOutputMode({
  currentFile = null,
  files = [],
  runnerCapabilities = ["python", "javascript"],
  webConnection = null,
} = {}) {
  const currentName = String(currentFile?.name || "");
  const currentLanguage = getLanguageForFilename(currentName);
  const htmlFiles = (Array.isArray(files) ? files : []).filter((file) => /\.html?$/i.test(file?.name || ""));
  const htmlEntry = findFileByName(files, webConnection?.entryFile) || htmlFiles[0] || null;
  const supports = new Set((Array.isArray(runnerCapabilities) ? runnerCapabilities : []).map((item) => String(item).toLowerCase()));

  if (/\.html?$/i.test(currentName)) {
    return { mode: "browser-preview", reason: "html-entry", entryFile: currentName, language: "html" };
  }
  if (/\.css$/i.test(currentName)) {
    return { mode: "browser-preview", reason: "stylesheet-preview", entryFile: htmlEntry?.name || "", language: "css" };
  }
  if (/\.jsx$/i.test(currentName) || currentLanguage.key === "jsx") {
    return { mode: "react-preview", reason: "react-entry", entryFile: currentName, language: "jsx" };
  }

  if (/\.(?:m?js|cjs)$/i.test(currentName) || currentLanguage.key === "javascript") {
    const referenced = htmlFiles.some((html) => referencedLocalFiles(html.content, "script", "src").includes(filenameOf(currentName)));
    if (referenced) {
      const entry = htmlFiles.find((html) => referencedLocalFiles(html.content, "script", "src").includes(filenameOf(currentName)));
      return { mode: "browser-preview", reason: "javascript-referenced-by-html", entryFile: entry?.name || "", language: "javascript" };
    }
  }

  const connectionIsExplicit = webConnection?.enabled === true
    && filenameOf(webConnection?.languageFile) === filenameOf(currentName)
    && Boolean(findFileByName(files, webConnection?.entryFile))
    && Boolean(findFileByName(files, webConnection?.languageFile));
  if (connectionIsExplicit && supports.has(currentLanguage.key)) {
    return {
      mode: "connected-preview",
      reason: "explicit-language-html-connection",
      entryFile: findFileByName(files, webConnection.entryFile)?.name || "",
      languageFile: currentName,
      language: currentLanguage.key,
    };
  }

  return {
    mode: "terminal",
    reason: connectionIsExplicit ? "connected-runtime-unavailable" : "non-browser-language",
    language: currentLanguage.key,
    runnerSupported: supports.has(currentLanguage.key),
  };
}

export function isBrowserWorkspace(files) {
  return Array.isArray(files) && files.some((file) => /\.html?$/i.test(file?.name || ""));
}

function scriptBridge(messageSource) {
  return `<script>(function(){var source=${JSON.stringify(String(messageSource))};var send=function(kind,args){var output=Array.from(args||[]).map(function(value){if(typeof value==='string')return value;try{return JSON.stringify(value)}catch(_){return String(value)}}).join(' ');try{parent.postMessage({source:source,kind:kind,output:output,error:kind==='error'?output:''},'*')}catch(_){}};['log','info','warn','error'].forEach(function(kind){var original=console[kind].bind(console);console[kind]=function(){send(kind,arguments);original.apply(console,arguments)}});window.addEventListener('error',function(event){send('error',[event.message||'Preview error'])});window.addEventListener('unhandledrejection',function(event){send('error',[event.reason&&event.reason.message||event.reason||'Unhandled promise rejection'])})})();<\/script>`;
}

function injectIntoHead(html, markup) {
  if (/<head[\s>]/i.test(html)) return html.replace(/<head([^>]*)>/i, `<head$1>${markup}`);
  return html.replace(/<html([^>]*)>/i, `<html$1><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${markup}</head>`);
}

function safeInlineText(value, closingTag) {
  return String(value || "").replace(new RegExp(`</${closingTag}`, "gi"), `<\\/${closingTag}`);
}

export function createBrowserDocument(files, messageSource = "codeleaf-playground-output", options = {}) {
  const collection = Array.isArray(files) ? files : [];
  const requestedEntry = findFileByName(collection, options.entryFile);
  const htmlFile = requestedEntry || collection.find((file) => /\.html?$/i.test(file?.name || "")) || null;
  const activeFile = findFileByName(collection, options.activeFileName);
  const activeCss = activeFile && /\.css$/i.test(activeFile.name) ? activeFile : null;
  let html = htmlFile?.content || defaultSourceForLanguage("html");
  const cssFiles = collection.filter((file) => /\.css$/i.test(file?.name || ""));
  const jsFiles = collection.filter((file) => /\.(?:m?js|cjs)$/i.test(file?.name || ""));
  const cssRefs = referencedLocalFiles(html, "link", "href");
  const jsRefs = referencedLocalFiles(html, "script", "src");
  const inlineStyles = [];

  for (const cssName of cssRefs) {
    const file = findFileByName(cssFiles, cssName);
    if (!file) continue;
    const style = `<style data-codeleaf-file="${file.name}">${safeInlineText(file.content, "style")}</style>`;
    inlineStyles.push(style);
    const linkPattern = new RegExp(`<link\\b(?=[^>]*\\bhref\\s*=\\s*(["'])${cssName.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&")}\\1)[^>]*>`, "gi");
    html = html.replace(linkPattern, "");
  }
  if (!cssRefs.length && cssFiles.length === 1) {
    inlineStyles.push(`<style data-codeleaf-file="${cssFiles[0].name}">${safeInlineText(cssFiles[0].content, "style")}</style>`);
  }
  if (activeCss && !inlineStyles.some((style) => style.includes(`data-codeleaf-file="${activeCss.name}"`))) {
    inlineStyles.push(`<style data-codeleaf-active-css="true">${safeInlineText(activeCss.content, "style")}</style>`);
  }

  for (const jsName of jsRefs) {
    const file = findFileByName(jsFiles, jsName);
    if (!file) continue;
    const script = `<script data-codeleaf-file="${file.name}">${safeInlineText(file.content, "script")}<\/script>`;
    const escaped = jsName.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&");
    const scriptPattern = new RegExp(`<script\\b(?=[^>]*\\bsrc\\s*=\\s*(["'])${escaped}\\1)[^>]*>\\s*<\\/script\\s*>`, "gi");
    html = html.replace(scriptPattern, script);
  }

  const connected = options.connectedOutput && typeof options.connectedOutput === "object"
    ? `<script>window.CODELEAF_CONNECTED_OUTPUT=${JSON.stringify(options.connectedOutput).replace(/</g, "\\u003c")};window.CODELEAF_CONNECTED_LANGUAGE=${JSON.stringify(options.connectedOutput.language || "")};document.addEventListener('DOMContentLoaded',function(){window.dispatchEvent(new CustomEvent('codeleaf:language-output',{detail:window.CODELEAF_CONNECTED_OUTPUT}));});<\/script>`
    : "";
  const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'">`;
  const bridge = scriptBridge(messageSource);
  html = injectIntoHead(html, `<meta charset="utf-8">${csp}${inlineStyles.join("")}${bridge}${connected}`);
  return html;
}

/**
 * Build a restricted React preview document. React/Babel assets are pinned to
 * explicit CDN versions; user code runs only inside an opaque sandboxed iframe.
 * Relative JS/JSX imports and CSS side-effect imports are resolved from the
 * in-memory workspace. Unknown npm packages fail with a visible error.
 */
export function createReactPreviewDocument(files, entryFile, messageSource = "codeleaf-playground-output") {
  const collection = Array.isArray(files) ? files : [];
  const entry = findFileByName(collection, entryFile) || collection.find((file) => /\.jsx$/i.test(file?.name || ""));
  const sources = Object.fromEntries(collection.map((file) => [filenameOf(file.name), { name: file.name, content: String(file.content || "") }]));
  const css = collection.filter((file) => /\.css$/i.test(file?.name || "")).map((file) => `<style data-codeleaf-file="${file.name}">${safeInlineText(file.content, "style")}</style>`).join("");
  const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval' https://unpkg.com; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'">`;
  const payload = JSON.stringify({ files: sources, entryFile: entry?.name || "" }).replace(/</g, "\\u003c");
  const bootstrap = `(function(){
    var source=${JSON.stringify(String(messageSource))};
    var project=${payload};
    var report=function(kind,message){try{parent.postMessage({source:source,kind:kind,output:String(message||''),error:kind==='error'?String(message||''):''},'*')}catch(_){}};
    var showError=function(error){var message=error&&error.message?error.message:String(error||'React preview failed');var node=document.getElementById('preview-error');if(node){node.hidden=false;node.textContent=message}report('error',message)};
    window.onerror=function(message,_url,line,column,error){showError(error||message);return true};
    window.addEventListener('unhandledrejection',function(event){showError(event.reason||'Unhandled promise rejection')});
    var modules={
      'react':function(){return window.React},
      'react-dom':function(){return window.ReactDOM},
      'react-dom/client':function(){return {createRoot:window.ReactDOM.createRoot.bind(window.ReactDOM),hydrateRoot:window.ReactDOM.hydrateRoot&&window.ReactDOM.hydrateRoot.bind(window.ReactDOM)}},
      'react-router-dom':function(){if(!window.ReactRouterDOM)throw new Error('React Router runtime did not load.');return window.ReactRouterDOM}
    };
    var cache={};
    function findLocal(request,parent){
      var clean=String(request||'').replace(/^\\.\\//,'').replace(/\\.(?:jsx?|tsx?|css)$/i,'').toLowerCase();
      var direct=clean.split('/').pop();
      var keys=Object.keys(project.files);
      var match=keys.find(function(key){return key.replace(/\\.(?:jsx?|tsx?|css)$/i,'')===direct});
      if(!match)throw new Error('Cannot resolve local import "'+request+'" from '+parent+'. Add the file to this flat workspace or remove the import.');
      return match;
    }
    function loadModule(key){
      if(cache[key])return cache[key].exports;
      var file=project.files[key];
      if(!file)throw new Error('Project file not found: '+key);
      if(/\\.css$/i.test(file.name))return {};
      if(!window.Babel)throw new Error('The JSX compiler did not load. Check the connection and refresh the preview.');
      var compiled=window.Babel.transform(file.content,{filename:file.name,presets:[['env',{modules:'commonjs',targets:{chrome:'100'}}],'react']}).code;
      var module={exports:{}};cache[key]=module;
      function localRequire(request){
        if(Object.prototype.hasOwnProperty.call(modules,request))return modules[request]();
        if(request.startsWith('.'))return loadModule(findLocal(request,file.name));
        if(request.endsWith('.css'))return {};
        throw new Error('Unsupported React preview dependency "'+request+'". Supported packages: react, react-dom, react-dom/client and react-router-dom.');
      }
      new Function('require','module','exports','React','ReactDOM',compiled)(localRequire,module,module.exports,window.React,window.ReactDOM);
      return module.exports;
    }
    try{
      if(!project.entryFile)throw new Error('Choose an App.jsx or main.jsx file to preview.');
      var key=project.entryFile.toLowerCase().split('/').pop();
      var exports=loadModule(key);
      var App=exports&&exports.default||exports&&exports.App||exports&&exports.default&&exports.default.default;
      if(typeof App==='function')window.ReactDOM.createRoot(document.getElementById('root')).render(window.React.createElement(App));
      else if(!document.getElementById('root').hasChildNodes())throw new Error('The selected React entry did not render an application. Export a default React component or render it with createRoot().');
      report('log','React preview compiled successfully.');
    }catch(error){showError(error)}
  })();`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}${css}<title>CodeLeaf React Preview</title></head><body><div id="root"></div><pre id="preview-error" hidden style="white-space:pre-wrap;overflow-wrap:anywhere;margin:16px;padding:12px;border:1px solid #dc6b6b;border-radius:8px;color:#7f1d1d;background:#fff1f1;font:13px/1.5 ui-monospace,monospace"></pre><script src="https://unpkg.com/react@18.3.1/umd/react.development.js"><\/script><script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"><\/script><script src="https://unpkg.com/@remix-run/router@1.21.0/dist/router.umd.js"><\/script><script src="https://unpkg.com/react-router@6.28.0/dist/umd/react-router.development.js"><\/script><script src="https://unpkg.com/react-router-dom@6.28.0/dist/umd/react-router-dom.development.js"><\/script><script src="https://unpkg.com/@babel/standalone@7.29.7/babel.min.js"><\/script><script>${bootstrap}</script></body></html>`;
}
