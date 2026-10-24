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
  jsx: { label: "React / JSX", extension: "jsx", filename: "App.jsx", execution: "static" },
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
  if (!name || name.length > 100 || name === "." || name === "..") return false;
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

export function isBrowserWorkspace(files) {
  return Array.isArray(files) && files.some((file) => /\.html?$/i.test(file.name)) && files.some((file) => /\.css$/i.test(file.name) || /\.html?$/i.test(file.name));
}

export function createBrowserDocument(files, messageSource = "codeleaf-try-output") {
  const htmlFile = files.find((file) => /\.html?$/i.test(file.name));
  const cssFile = files.find((file) => /\.css$/i.test(file.name));
  const jsFile = files.find((file) => /\.(m?js|cjs)$/i.test(file.name));
  const html = htmlFile?.content || defaultSourceForLanguage("html");
  const css = cssFile?.content || "";
  const js = jsFile?.content || "";
  const style = `<style>${css.replace(/<\/style/gi, "<\\/style")}</style>`;
  const bridge = `<script>(function(){var source=${JSON.stringify(String(messageSource))};var send=function(kind,args){var output=Array.from(args||[]).map(function(value){if(typeof value==='string')return value;try{return JSON.stringify(value)}catch(_){return String(value)}}).join(' ');try{parent.postMessage({source:source,kind:kind,output:output,error:kind==='error'?output:''},'*')}catch(_){}};['log','info','warn','error'].forEach(function(kind){var original=console[kind].bind(console);console[kind]=function(){send(kind,arguments);original.apply(console,arguments)}});window.addEventListener('error',function(event){send('error',[event.message||'Preview error'])})})();<\/script>`;
  const script = js ? `<script>${js.replace(/<\/script/gi, "<\\/script")}<\/script>` : "";
  const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'">`;
  if (/<head[\s>]/i.test(html)) {
    let result = html.replace(/<head([^>]*)>/i, `<head$1><meta charset="utf-8">${csp}${style}${bridge}`);
    if (script) result = /<\/body>/i.test(result) ? result.replace(/<\/body>/i, `${script}</body>`) : `${result}${script}`;
    return result;
  }
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}${style}${bridge}</head><body>${html}${script}</body></html>`;
}
