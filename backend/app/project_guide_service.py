"""Build learner-safe project guides and starter kits from CodeLeaf project manifests.

This module deliberately excludes protected reference-solution files. Files explicitly
embedded as starter content are preserved. Manifest entries that only describe a path and
purpose receive clearly-labelled starter scaffolds so every project has a browsable guide.
"""

from __future__ import annotations

import html
import json
import posixpath
import re
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

# Text-only source files that may be served from a course's own content directory.
TEXT_SUFFIXES = {
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".py",
    ".pyi",
    ".sql",
    ".md",
    ".txt",
    ".json",
    ".xml",
    ".xsd",
    ".xsl",
    ".xslt",
    ".dtd",
    ".xq",
    ".yml",
    ".yaml",
    ".sh",
    ".bash",
    ".php",
    ".java",
    ".c",
    ".h",
    ".hpp",
    ".cpp",
    ".cc",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".lua",
    ".kt",
    ".swift",
    ".dart",
    ".toml",
    ".ini",
    ".cfg",
    ".properties",
    ".ps1",
    ".psm1",
    ".r",
    ".tf",
    ".gradle",
    ".groovy",
    ".sol",
    ".dockerignore",
    ".gitignore",
    ".ipynb",
    ".csv",
    ".tsv",
}
MAX_SOURCE_BYTES = 400_000


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_rel_path(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip().replace("\\", "/")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return None
    parts = [part for part in value.split("/") if part not in ("", ".")]
    if not parts or any(part == ".." for part in parts):
        return None
    result = "/".join(parts)
    return result + "/" if value.endswith("/") else result


def is_protected_project_path(raw: Any) -> bool:
    """Identify solution/private files that must never reach learner-facing starter APIs."""
    path = _safe_rel_path(raw)
    if not path:
        return True
    parts = [part.casefold() for part in PurePosixPath(path.rstrip("/")).parts]
    protected_segments = {
        "solution", "solutions", "answer-key", "answer-keys", "answer_key",
        "answer_keys", "answerkeys", "private", "secrets",
    }
    if any(part in protected_segments or part == ".env" or part.startswith(".env.") for part in parts):
        return True
    filename = parts[-1] if parts else ""
    return bool(re.match(r"^(?:solution|answer[-_]?key|answerkey)(?:[._-]|$)", filename))


def _slug_text(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "project")).strip("-").lower()
    return text or "project"


def _requirements(project: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for key in ("required_features", "acceptance_criteria", "target_skills", "skills"):
        for item in _as_list(project.get(key)):
            if isinstance(item, str) and item.strip() and item not in result:
                result.append(item.strip())
    return result[:18]


def _milestones(project: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        item for item in _as_list(project.get("milestones")) if isinstance(item, dict)
    ]
    if rows:
        return sorted(rows, key=lambda item: int(item.get("sequence") or 0))
    requirements = _requirements(project)
    if not requirements:
        requirements = [
            "Review the requirements and define a small working version.",
            "Implement the core behavior and its error/empty states.",
            "Test the expected result and document how to run the project.",
        ]
    return [
        {
            "sequence": index,
            "title": str(item),
            "acceptance_criteria": [
                "Implement this requirement and verify it with a repeatable test."
            ],
        }
        for index, item in enumerate(requirements, start=1)
    ]


def _course_runtime(course_slug: str, project: dict[str, Any]) -> dict[str, Any]:
    slug = course_slug.lower().replace("_", "-")
    files = [
        str(entry.get("path", "")) if isinstance(entry, dict) else str(entry)
        for entry in _as_list(project.get("starter_files"))
    ]
    joined = " ".join(files).lower()
    if slug in {"html", "css", "bootstrap", "jquery", "xml", "javascript"}:
        return {
            "label": "Browser project",
            "requirements": [
                "A modern web browser",
                "A code editor (VS Code recommended)",
            ],
            "commands": [
                {
                    "label": "Open the project",
                    "command": "Open index.html in your browser, or use the VS Code Live Server extension.",
                },
                {
                    "label": "Verify",
                    "command": "Resize the browser, test all links and controls, and inspect the browser console.",
                },
            ],
            "note": "If the manifest names a different HTML entry file, open that file instead of index.html.",
        }
    if (
        slug
        in {
            "react",
            "nextjs",
            "vue",
            "angular",
            "angularjs",
            "javascript",
            "typescript",
            "nodejs",
            "expressjs",
            "tailwindcss",
            "sass",
        }
        or "package.json" in joined
    ):
        commands = [
            {"label": "Install dependencies", "command": "npm install"},
            {"label": "Start development", "command": "npm run dev"},
            {"label": "Production build", "command": "npm run build"},
        ]
        if slug in {"nodejs", "expressjs"}:
            commands[1] = {"label": "Start the application", "command": "npm start"}
        if slug == "angular":
            commands[1] = {
                "label": "Start development",
                "command": "npm start  (or ng serve if configured)",
            }
        return {
            "label": "Node.js project",
            "requirements": ["Node.js LTS", "npm"],
            "commands": commands,
            "note": "Use the scripts actually present in package.json; the commands above are common defaults.",
        }
    if slug in {
        "python",
        "flask",
        "fastapi",
        "django",
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "pytorch",
        "datascience",
        "ai",
        "gen-ai",
    } or any(name.endswith(".py") for name in files):
        if slug == "flask":
            commands = [
                {"label": "Create environment", "command": "py -m venv .venv"},
                {
                    "label": "Activate on Windows",
                    "command": ".\\.venv\\Scripts\\Activate.ps1",
                },
                {
                    "label": "Install dependencies",
                    "command": "pip install -r requirements.txt",
                },
                {"label": "Run locally", "command": "flask --app app run --debug"},
            ]
        elif slug == "fastapi":
            commands = [
                {"label": "Create environment", "command": "py -m venv .venv"},
                {
                    "label": "Activate on Windows",
                    "command": ".\\.venv\\Scripts\\Activate.ps1",
                },
                {
                    "label": "Install dependencies",
                    "command": "pip install -r requirements.txt",
                },
                {"label": "Run locally", "command": "uvicorn app.main:app --reload"},
            ]
        elif slug == "django":
            commands = [
                {"label": "Create environment", "command": "py -m venv .venv"},
                {
                    "label": "Activate on Windows",
                    "command": ".\\.venv\\Scripts\\Activate.ps1",
                },
                {
                    "label": "Install dependencies",
                    "command": "pip install -r requirements.txt",
                },
                {"label": "Run locally", "command": "python manage.py runserver"},
            ]
        else:
            commands = [
                {"label": "Create environment", "command": "py -m venv .venv"},
                {
                    "label": "Activate on Windows",
                    "command": ".\\.venv\\Scripts\\Activate.ps1",
                },
                {
                    "label": "Install dependencies",
                    "command": "pip install -r requirements.txt  (if present)",
                },
                {
                    "label": "Run locally",
                    "command": "python main.py  (or the entry file listed in this guide)",
                },
            ]
        return {
            "label": "Python project",
            "requirements": [
                "Python 3.11+ recommended",
                "PowerShell or another terminal",
            ],
            "commands": commands,
            "note": "Adjust the entry point to match the actual files in this project.",
        }
    if (
        slug in {"docker", "linux", "bash", "github-actions", "aws"}
        or "dockerfile" in joined
        or "docker-compose" in joined
    ):
        return {
            "label": "DevOps / infrastructure project",
            "requirements": [
                "The relevant CLI or local container runtime",
                "Use a disposable development environment for experiments",
            ],
            "commands": [
                {
                    "label": "Review configuration",
                    "command": "Read the README and inspect every command before running it.",
                },
                {
                    "label": "Validate safely",
                    "command": "Run the tool's configuration/lint check in a local or sandbox environment.",
                },
                {
                    "label": "Run the lab",
                    "command": "Follow the tool-specific command documented in the generated README.",
                },
            ],
            "note": "Cloud resources can cost money. Do not apply infrastructure changes to production from a learning project.",
        }
    if slug in {
        "c",
        "cpp",
        "java",
        "go",
        "rust",
        "ruby",
        "php",
        "lua",
        "solidity",
        "kotlin",
        "swift",
        "dart",
        "csharp",
    }:
        commands_map = {
            "c": [
                {"label": "Compile", "command": "gcc main.c -o app"},
                {"label": "Run (PowerShell)", "command": ".\\app.exe"},
            ],
            "cpp": [
                {"label": "Compile", "command": "g++ main.cpp -o app"},
                {"label": "Run (PowerShell)", "command": ".\\app.exe"},
            ],
            "java": [
                {"label": "Compile", "command": "javac Main.java"},
                {"label": "Run", "command": "java Main"},
            ],
            "go": [{"label": "Run", "command": "go run ."}],
            "rust": [{"label": "Run", "command": "cargo run"}],
            "ruby": [{"label": "Run", "command": "ruby main.rb"}],
            "php": [
                {
                    "label": "Run local web server",
                    "command": "php -S localhost:8000 -t public",
                }
            ],
            "lua": [{"label": "Run", "command": "lua main.lua"}],
            "solidity": [
                {
                    "label": "Compile and test",
                    "command": "Use the project's pinned Solidity toolchain and local test network; never deploy to mainnet for this tutorial.",
                }
            ],
            "kotlin": [
                {
                    "label": "Run",
                    "command": "kotlinc Main.kt -include-runtime -d app.jar; java -jar app.jar",
                }
            ],
            "swift": [{"label": "Run", "command": "swift main.swift"}],
            "dart": [{"label": "Run", "command": "dart run"}],
            "csharp": [{"label": "Run", "command": "dotnet run"}],
        }
        return {
            "label": "Compiled / runtime project",
            "requirements": [
                "Install the runtime/compiler for this course",
                "Use the versions specified in project files",
            ],
            "commands": commands_map.get(
                slug,
                [
                    {
                        "label": "Run",
                        "command": "Use the runtime and entry point specified in this project's README.",
                    }
                ],
            ),
            "note": "File names and commands can differ by project; follow the file list and README first.",
        }
    if slug in {"sql", "mysql", "postgresql", "sqlite", "mongodb", "redis", "excel"}:
        return {
            "label": "Data / query project",
            "requirements": [
                "The database or desktop tool appropriate to this course",
                "Use a local practice dataset",
            ],
            "commands": [
                {
                    "label": "Review schema/data",
                    "command": "Read the provided schema and input data before running queries.",
                },
                {
                    "label": "Run the project",
                    "command": "Execute scripts in a local database/workbook, then compare results with the expected checks.",
                },
            ],
            "note": "SQL syntax and import commands vary by database engine. Use the exact engine identified by the course.",
        }
    return {
        "label": "Technology project",
        "requirements": ["The runtime and tools listed in the course lessons"],
        "commands": [
            {
                "label": "Read setup instructions",
                "command": "Open README.md and follow its version-pinned setup steps.",
            },
            {
                "label": "Verify",
                "command": "Run the available checks and compare actual behavior with the acceptance criteria.",
            },
        ],
        "note": "This guide uses the project manifest. Confirm any environment-specific setup before running commands.",
    }


def _generated_readme(
    project: dict[str, Any], files: list[dict[str, Any]], runtime: dict[str, Any]
) -> str:
    lines = [
        f"# {project.get('title') or 'Guided project'}",
        "",
        "## Goal",
        str(
            project.get("objective")
            or project.get("scenario")
            or "Build the project described in this guide."
        ),
        "",
        "## Prerequisites",
    ]
    prereqs = _as_list(project.get("prerequisites")) or _as_list(
        project.get("prerequisite_lesson_ids")
    )
    lines.extend(
        [f"- {item}" for item in prereqs] or ["- Review the related course lessons."]
    )
    lines += ["", "## File map"]
    for item in files:
        lines.append(
            f"- `{item['path']}` — {item.get('purpose') or ('Starter code for ' + item['path'])}"
        )
    lines += ["", "## Build steps"]
    for index, item in enumerate(_milestones(project), 1):
        lines.append(f"{index}. **{item.get('title', 'Milestone')}**")
        for criterion in _as_list(item.get("acceptance_criteria")):
            lines.append(f"   - {criterion}")
    lines += ["", "## Run locally"]
    for step in _as_list(runtime.get("commands")):
        lines.append(f"- **{step.get('label', 'Step')}:** `{step.get('command', '')}`")
    lines += ["", "## Quality checklist"]
    checklist = (
        _as_list(project.get("tests"))
        or _as_list(project.get("tests_and_validation"))
        or _as_list(project.get("test_plan"))
    )
    if checklist:
        for test in checklist:
            if isinstance(test, str):
                lines.append(f"- {test}")
            elif isinstance(test, dict):
                lines.append(
                    f"- {test.get('name') or test.get('title') or test.get('purpose') or json.dumps(test, ensure_ascii=False)}"
                )
    else:
        lines.extend(
            [
                "- Test the expected path and at least one invalid/empty input.",
                "- Check keyboard accessibility and a narrow screen when relevant.",
                "- Re-run the project from a clean environment.",
            ]
        )
    lines += [
        "",
        "## Important",
        "Some files in older project manifests specify only a path and purpose. Their code is generated starter scaffolding, not a reviewed full solution. Complete each TODO, meet the acceptance criteria, and run the tests before treating the project as finished.",
        "",
    ]
    return "\n".join(lines)


def _template_for_file(
    course_slug: str,
    project: dict[str, Any],
    path: str,
    purpose: str,
    sibling_paths: list[str],
) -> tuple[str, str]:
    title = str(project.get("title") or "Guided Project")
    objective = str(
        project.get("objective")
        or project.get("scenario")
        or "Implement the project requirements."
    )
    slug = course_slug.lower()
    file_path = PurePosixPath(path)
    name = file_path.name.lower()
    suffix = file_path.suffix.lower()
    features = _requirements(project)[:6]
    title_h = html.escape(title)
    feature_list_html = (
        "\n".join(f"      <li>{html.escape(feature)}</li>" for feature in features)
        or "      <li>Complete the project requirements</li>"
    )
    css_path = next(
        (
            candidate
            for candidate in sibling_paths
            if candidate.lower().endswith(".css")
        ),
        None,
    )
    js_path = next(
        (
            candidate
            for candidate in sibling_paths
            if candidate.lower().endswith(".js")
            and not candidate.lower().endswith(".config.js")
        ),
        None,
    )
    jsx_path = next(
        (
            candidate
            for candidate in sibling_paths
            if candidate.lower().endswith((".jsx", ".tsx"))
            and PurePosixPath(candidate).name.lower()
            in {"main.jsx", "main.tsx", "index.jsx", "index.tsx"}
        ),
        None,
    )
    if slug == "react" and jsx_path:
        js_path = jsx_path
    relative_css = (
        posixpath.relpath(css_path, str(file_path.parent)) if css_path else None
    )
    relative_js = posixpath.relpath(js_path, str(file_path.parent)) if js_path else None

    if name == "requirements.txt":
        if slug == "flask":
            return "Flask>=3.0,<4.0\n", "text"
        if slug == "fastapi":
            return "fastapi>=0.115,<1.0\nuvicorn[standard]>=0.30,<1.0\n", "text"
        if slug == "django":
            return "Django>=5.1,<6.0\n", "text"
        return "# Add pinned dependencies after choosing verified versions.\n", "text"
    if name == "pyproject.toml":
        return (
            '[project]\nname = "'
            + _slug_text(title)
            + '"\nversion = "0.1.0"\nrequires-python = "~=3.13"\ndependencies = []\n',
            "toml",
        )
    if name == "readme.md" and file_path.parent == PurePosixPath("."):
        # The root README is filled after all file paths have been normalized.
        return "", "markdown"
    if suffix == ".md":
        return (
            f"# {title} — {file_path.stem}\n\nPurpose: {purpose or objective}\n\n## Implementation notes\n\n- Follow the related project milestone.\n- Document expected behavior and error states.\n- Add a repeatable test before marking the task complete.\n",
            "markdown",
        )
    if suffix in {".html", ".htm"}:
        css_tag = (
            f'  <link rel="stylesheet" href="{html.escape(relative_css)}">\n'
            if relative_css
            else ""
        )
        if relative_js and (
            slug in {"react", "vue", "typescript", "nextjs"}
            or PurePosixPath(relative_js).suffix.lower() in {".jsx", ".tsx"}
        ):
            js_tag = (
                f'  <script type="module" src="{html.escape(relative_js)}"></script>\n'
            )
        else:
            js_tag = (
                f'  <script src="{html.escape(relative_js)}" defer></script>\n'
                if relative_js
                else ""
            )
        content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(objective, quote=True)}">
  <title>{title_h}</title>
{css_tag}{js_tag}</head>
<body>
  <header class="site-header">
    <div class="container"><p class="eyebrow">CODELEAF PROJECT</p><h1>{title_h}</h1><p>{html.escape(objective)}</p></div>
  </header>
  <main class="container">
    <section aria-labelledby="features-title" class="panel">
      <h2 id="features-title">Project checklist</h2>
      <ul>
{feature_list_html}
      </ul>
    </section>
    <section aria-labelledby="work-title">
      <h2 id="work-title">Build your version</h2>
      <p>Implement the milestones in order. Replace this scaffold with the behavior described in the guide.</p>
      <!-- TODO: implement the project-specific interactions and states. -->
    </section>
  </main>
  <footer class="container"><p>Built as a CodeLeaf learning project.</p></footer>
</body>
</html>
"""
        return content, "html"
    if suffix in {".css", ".scss", ".sass"}:
        content = """/* Responsive starter styles. Add project-specific component styles as you implement milestones. */
:root { color-scheme: light; --ink: #172033; --muted: #5d6b82; --surface: #ffffff; --line: #dbe3ed; --accent: #087f66; --accent-soft: #e2f7ef; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; font: 1rem/1.65 system-ui, -apple-system, Segoe UI, sans-serif; color: var(--ink); background: #f4f7fb; }
.container { width: min(1100px, calc(100% - 2rem)); margin-inline: auto; }
.site-header { padding: clamp(2rem, 6vw, 5rem) 0; background: #102036; color: white; }
.site-header p { max-width: 70ch; color: #c8d6e8; }
.eyebrow { color: #36dbb1; font-size: .75rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
main { padding-block: 2rem; }
.panel, section { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1rem, 3vw, 1.5rem); margin-block: 1rem; }
button, .button { display: inline-flex; gap: .5rem; align-items: center; border: 0; border-radius: .7rem; padding: .75rem 1rem; background: var(--accent); color: white; font: inherit; cursor: pointer; }
input, textarea, select { max-width: 100%; width: 100%; padding: .75rem; border: 1px solid var(--line); border-radius: .5rem; font: inherit; }
:focus-visible { outline: 3px solid #2ccda7; outline-offset: 3px; }
@media (min-width: 720px) { .feature-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; } }
"""
        return content, "css"
    if suffix in {".js", ".mjs", ".cjs"}:
        if slug == "vue" and name in {"main.js", "index.js"}:
            return (
                'import { createApp } from "vue";\nimport App from "./App.vue";\nimport "./style.css";\n\ncreateApp(App).mount("#app");\n',
                "javascript",
            )
        if (
            "package.json" in sibling_paths
            and slug in {"nodejs", "expressjs"}
            or slug in {"nodejs", "expressjs"}
            and name in {"server.js", "app.js", "index.js"}
        ):
            return (
                f"""// Starter server for {title}. Implement the project-specific routes and validation.
const express = require("express");
const app = express();
const port = Number(process.env.PORT || 3000);
app.use(express.json());
app.get("/health", (_req, res) => res.json({{ status: "ok", project: {json.dumps(title)} }}));
app.get("/", (_req, res) => res.json({{ message: {json.dumps(objective)}, nextStep: "Implement the required project routes" }}));
// TODO: add the routes, data access, validation, and tests required by the guide.
app.listen(port, () => console.log(`{title} listening on ${{port}}`));
""",
                "javascript",
            )
        return (
            f"""// {title}
// Purpose: {purpose or objective}
// TODO: implement the project-specific behaviors listed in the guide.

document.addEventListener("DOMContentLoaded", () => {{
  const status = document.querySelector("[data-project-status]");
  if (status) status.textContent = "Project scaffold loaded. Implement the next milestone.";

  // Add event listeners for project controls here. Validate inputs and handle empty/error states.
}});
""",
            "javascript",
        )
    if suffix == ".ts":
        return (
            f"""// {title}
// {purpose or objective}
export type ProjectStatus = "idle" | "ready" | "error";

export function describeProject(): string {{
  return {json.dumps(title)};
}}

// TODO: implement project-specific types and pure functions, then add tests.
""",
            "typescript",
        )
    if suffix == ".tsx":
        return (
            f"""import React from "react";

type ProjectProps = {{ title?: string }};

export default function ProjectView({{ title = {json.dumps(title)} }}: ProjectProps) {{
  return (
    <main>
      <h1>{{title}}</h1>
      <p>{{{json.dumps(objective)}}}</p>
      {{/* TODO: implement the project-specific interactions and states. */}}
    </main>
  );
}}
""",
            "tsx",
        )
    if suffix == ".vue":
        return (
            f"""<script setup>
import {{ ref }} from "vue";
const title = ref({json.dumps(title)});
const status = ref("Ready to build");
// TODO: implement the project-specific behavior and states.
</script>

<template>
  <main class="project-shell">
    <p class="eyebrow">CodeLeaf guided project</p>
    <h1>{{{{ title }}}}</h1>
    <p>{{{json.dumps(objective)}}}</p>
    <p aria-live="polite">{{{{ status }}}}</p>
  </main>
</template>
""",
            "vue",
        )
    if suffix == ".svelte":
        return (
            f"""<script>
  let title = {json.dumps(title)};
  let status = "Ready to build";
  // TODO: implement the project-specific behavior and states.
</script>

<main>
  <p class="eyebrow">CodeLeaf guided project</p>
  <h1>{{{{title}}}}</h1>
  <p>{{{json.dumps(objective)}}}</p>
  <p aria-live="polite">{{{{status}}}}</p>
</main>
""",
            "svelte",
        )
    if suffix == ".jsx":
        if name in {"main.jsx", "index.jsx"}:
            return (
                """import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(<React.StrictMode><App /></React.StrictMode>);
""",
                "jsx",
            )
        cards = (
            "\n".join(
                f'        <li className="feature-card" key={index}>{json.dumps(feature)}</li>'
                for index, feature in enumerate(features)
            )
            or '        <li className="feature-card">Complete the project requirements</li>'
        )
        return (
            f"""import {{ useState }} from "react";

const projectTitle = {json.dumps(title)};
const projectFeatures = {json.dumps(features, ensure_ascii=False, indent=2)};

export default function App() {{
  const [completed, setCompleted] = useState([]);
  function toggleFeature(feature) {{
    setCompleted((current) => current.includes(feature) ? current.filter((item) => item !== feature) : [...current, feature]);
  }}
  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">CodeLeaf guided project</p>
        <h1>{{projectTitle}}</h1>
        <p>{html.escape(objective)}</p>
      </header>
      <section aria-labelledby="requirements-title">
        <h2 id="requirements-title">Project requirements</h2>
        <ul className="feature-list">
          {{projectFeatures.map((feature) => (
            <li key={{feature}}>
              <label><input type="checkbox" checked={{completed.includes(feature)}} onChange={{() => toggleFeature(feature)}} /> {{feature}}</label>
            </li>
          ))}}
        </ul>
        <p aria-live="polite">{{completed.length}} of {{projectFeatures.length}} checklist items completed.</p>
      </section>
      {{/* TODO: implement the domain-specific screens, data, and interactions required by the milestones. */}}
    </main>
  );
}}
""",
            "jsx",
        )
    if suffix in {".py", ".pyi"}:
        if slug == "flask" and name in {"app.py", "main.py"}:
            return (
                f'''"""{title} — Flask starter application."""
from flask import Flask, render_template

app = Flask(__name__)

@app.get("/
def home():
    """Render the project home page. Add project-specific routes here."""
    return {{"project": {title!r}, "message": {objective!r}, "next_step": "Implement the milestones"}}

@app.get("/health")
def health():
    return {{"status": "ok"}}

if __name__ == "__main__":
    app.run(debug=True)
'''.replace('@app.get("/\ndef', '@app.get("/")\ndef'),
                "python",
            )
        if (slug == "fastapi" or "fastapi" in path.lower()) and name in {
            "main.py",
            "app.py",
        }:
            return (
                f'''"""{title} — FastAPI starter."""
from fastapi import FastAPI

app = FastAPI(title={title!r})

@app.get("/")
def read_root() -> dict[str, str]:
    return {{"project": {title!r}, "message": {objective!r}, "next_step": "Implement the milestones"}}

@app.get("/health")
def health() -> dict[str, str]:
    return {{"status": "ok"}}

# TODO: add project-specific schemas, validation, persistence, and tests.
''',
                "python",
            )
        if (
            name.startswith("test_")
            or "/tests/" in path.lower()
            or path.lower().startswith("tests/")
        ):
            return (
                '''"""Tests to implement for the project. Replace placeholders with behavior assertions."""

def test_project_requirements_are_documented():
    """Keep at least one executable test tied to a real requirement."""
    assert True  # TODO: replace with assertions against the implemented behavior.
''',
                "python",
            )
        return (
            f'''"""{title} — Python starter module."""
from __future__ import annotations


def run() -> None:
    """Entry point; implement the project milestones in small, testable functions."""
    print({title!r})
    print({objective!r})
    # TODO: implement the required features and error/empty states.


def main() -> None:
    run()


if __name__ == "__main__":
    main()
''',
            "python",
        )
    if suffix == ".py" and name == "app.py" and slug == "flask":
        return (
            'from flask import Flask\napp = Flask(__name__)\n\n@app.get("/")\ndef home():\n    return "Implement the project home page"\n',
            "python",
        )
    if suffix == ".py" and name in {"main.py", "app.py"} and slug == "fastapi":
        return (
            'from fastapi import FastAPI\napp = FastAPI()\n\n@app.get("/")\ndef root():\n    return {"status": "ok"}\n',
            "python",
        )
    if suffix == ".py" and name in {"requirements.txt", "pyproject.toml"}:
        if slug == "flask":
            return "Flask>=3.0,<4.0\n"
        if slug == "fastapi":
            return "fastapi>=0.115,<1.0\nuvicorn[standard]>=0.30,<1.0\n"
    if suffix == ".txt" and name == "requirements.txt":
        if slug == "flask":
            return "Flask>=3.0,<4.0\n", "text"
        if slug == "fastapi":
            return "fastapi>=0.115,<1.0\nuvicorn[standard]>=0.30,<1.0\n", "text"
        return "# Add pinned dependencies after choosing verified versions.\n", "text"
    if name == "package.json":
        if slug == "nextjs":
            data = {
                "name": _slug_text(title),
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                },
                "dependencies": {
                    "next": "^15.0.0",
                    "react": "^19.0.0",
                    "react-dom": "^19.0.0",
                },
            }
        elif slug == "react":
            data = {
                "name": _slug_text(title),
                "private": True,
                "version": "1.0.0",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview",
                },
                "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0"},
                "devDependencies": {"@vitejs/plugin-react": "^4.3.0", "vite": "^6.0.0"},
            }
        elif slug == "vue":
            data = {
                "name": _slug_text(title),
                "private": True,
                "version": "1.0.0",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview",
                },
                "dependencies": {"vue": "^3.5.0"},
                "devDependencies": {"@vitejs/plugin-vue": "^5.2.0", "vite": "^6.0.0"},
            }
        elif slug in {"angular", "angularjs"}:
            deps = (
                {"angular": "^1.8.3"}
                if slug == "angularjs"
                else {
                    "@angular/common": "^19.0.0",
                    "@angular/compiler": "^19.0.0",
                    "@angular/core": "^19.0.0",
                    "@angular/platform-browser": "^19.0.0",
                    "@angular/router": "^19.0.0",
                    "rxjs": "~7.8.0",
                    "zone.js": "~0.15.0",
                }
            )
            data = {
                "name": _slug_text(title),
                "private": True,
                "version": "1.0.0",
                "scripts": {"start": "ng serve", "build": "ng build"},
                "dependencies": deps,
                "devDependencies": {"@angular/cli": "^19.0.0", "typescript": "~5.7.0"},
            }
        elif slug == "typescript":
            data = {
                "name": _slug_text(title),
                "private": True,
                "version": "1.0.0",
                "scripts": {"dev": "vite", "build": "vite build"},
                "devDependencies": {"typescript": "~5.7.0", "vite": "^6.0.0"},
            }
        elif slug in {"expressjs", "nodejs"}:
            data = {
                "name": _slug_text(title),
                "version": "1.0.0",
                "private": True,
                "scripts": {"start": "node app.js", "dev": "node --watch app.js"},
                "dependencies": {"express": "^5.0.0"},
            }
        else:
            data = {
                "name": _slug_text(title),
                "version": "1.0.0",
                "private": True,
                "scripts": {"start": "node app.js"},
            }
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n", "json"
    if name == "vite.config.js":
        if slug == "react":
            return (
                'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\nexport default defineConfig({ plugins: [react()] });\n',
                "javascript",
            )
        if slug == "vue":
            return (
                'import { defineConfig } from "vite";\nimport vue from "@vitejs/plugin-vue";\nexport default defineConfig({ plugins: [vue()] });\n',
                "javascript",
            )
        return (
            'import { defineConfig } from "vite";\nexport default defineConfig({});\n',
            "javascript",
        )
    if name == "dockerfile" or suffix == ".dockerfile":
        if slug in {"python", "flask", "fastapi", "django"}:
            return (
                f"""FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Adjust this entry point for the app's actual framework and module.
CMD ["python", "main.py"]
""",
                "dockerfile",
            )
        return (
            """FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""",
            "dockerfile",
        )
    if suffix in {".yml", ".yaml"}:
        if "docker-compose" in name or name == "compose.yaml" or name == "compose.yml":
            return (
                """services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: development
    restart: unless-stopped
""",
                "yaml",
            )
        if ".github/workflows/" in path:
            return (
                """name: Project checks
on:
  push:
  pull_request:
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
      - name: Validate project files
        run: echo "Add the project's real lint, test, and build commands here"
""",
                "yaml",
            )
        return (
            f"# {title}\n# {purpose or 'Configuration scaffold'}\n# TODO: set schema-valid project-specific options.\n",
            "yaml",
        )
    if suffix == ".sql":
        if slug == "mysql":
            return (
                f"""-- {title}
-- Starter schema. Align columns and constraints with the project requirements.
CREATE TABLE IF NOT EXISTS project_records (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- TODO: add project-specific tables, indexes, relationships and sample rows.
""",
                "sql",
            )
        if slug == "sqlite":
            return (
                f"""-- {title}
CREATE TABLE IF NOT EXISTS project_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- TODO: add project-specific tables and representative data.
""",
                "sql",
            )
        return (
            f"""-- {title}
CREATE TABLE IF NOT EXISTS project_records (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- TODO: add project-specific tables, foreign keys, indexes and validation queries.
""",
            "sql",
        )
    if suffix == ".java":
        class_name = re.sub(r"[^A-Za-z0-9]", "", file_path.stem) or "Main"
        class_name = class_name[0].upper() + class_name[1:]
        return (
            f"""/** {title}. {purpose or objective} */
public class {class_name} {{
    public static void main(String[] args) {{
        System.out.println({json.dumps(title)});
        System.out.println({json.dumps(objective)});
        // TODO: implement the milestones as small methods and verify edge cases.
    }}
}}
""",
            "java",
        )
    if suffix == ".c":
        return (
            f"""/* {title} — {purpose or objective} */
#include <stdio.h>

int main(void) {{
    puts({json.dumps(title)});
    /* TODO: parse inputs, implement the required behavior, and handle invalid input. */
    return 0;
}}
""",
            "c",
        )
    if suffix in {".cpp", ".cc", ".hpp", ".h"}:
        if suffix in {".hpp", ".h"}:
            guard = _slug_text(file_path.stem).upper().replace("-", "_") + "_H"
            return (
                f"""#ifndef {guard}
#define {guard}

// TODO: declare the project-specific types and functions here.

#endif // {guard}
""",
                "cpp",
            )
        return (
            f"""#include <iostream>
#include <string>

int main() {{
    std::cout << {json.dumps(title)} << "\\n";
    // TODO: implement: {objective}
    return 0;
}}
""",
            "cpp",
        )
    if suffix == ".go":
        return (
            f"""package main

import "fmt"

func main() {{
    fmt.Println({json.dumps(title)})
    // TODO: implement and test the project's required behavior.
}}
""",
            "go",
        )
    if suffix == ".rs":
        return (
            f"""fn main() {{
    println!({json.dumps(title)});
    // TODO: implement the project behavior and return useful errors for invalid input.
}}
""",
            "rust",
        )
    if suffix == ".php":
        return (
            f"""<?php
// {title}
declare(strict_types=1);

header('Content-Type: text/html; charset=utf-8');
echo '<h1>' . htmlspecialchars({json.dumps(title)}, ENT_QUOTES, 'UTF-8') . '</h1>';
echo '<p>' . htmlspecialchars({json.dumps(objective)}, ENT_QUOTES, 'UTF-8') . '</p>';
// TODO: implement project-specific routes, validation, and templates.
""",
            "php",
        )
    if suffix == ".rb":
        return (
            f"""# {title}
def main
  puts {json.dumps(title)}
  # TODO: implement the project requirements and handle invalid input.
end

main if $PROGRAM_NAME == __FILE__
""",
            "ruby",
        )
    if suffix == ".lua":
        return (
            f"""-- {title}
local function main()
  print({json.dumps(title)})
  -- TODO: implement the project requirements and check invalid input.
end

main()
""",
            "lua",
        )
    if suffix == ".sh" or suffix == ".bash":
        return (
            f"""#!/usr/bin/env bash
set -euo pipefail

# {title}
echo {json.dumps(title)}
# TODO: implement a safe, repeatable workflow. Avoid destructive commands by default.
""",
            "bash",
        )
    if suffix in {".ps1", ".psm1"}:
        return (
            f"""# {title}
$ErrorActionPreference = "Stop"
Write-Host {json.dumps(title)}
# TODO: implement steps with explicit validation; never overwrite important data silently.
""",
            "powershell",
        )
    if suffix == ".xml":
        return (
            f"""<?xml version="1.0" encoding="UTF-8"?>
<project name={json.dumps(title)}>
  <description>{html.escape(objective)}</description>
  <!-- TODO: add the elements and schema required by the project. -->
</project>
""",
            "xml",
        )
    if suffix == ".json":
        return (
            json.dumps(
                {
                    "project": title,
                    "description": objective,
                    "items": [],
                    "TODO": "Replace this scaffold with the project-specific data contract.",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            "json",
        )
    if suffix == ".toml":
        return (
            f"""[project]
name = "{_slug_text(title)}"
version = "0.1.0"
description = {json.dumps(objective)}
""",
            "toml",
        )
    if suffix == ".sol":
        return (
            f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract {_slug_text(file_path.stem).replace('-', '_').title().replace('_', '') or 'Project'} {{
    // {title}
    // TODO: implement state changes and access controls; test on a local chain first.
}}
""",
            "solidity",
        )
    if suffix == ".r":
        return (
            f"""# {title}
# TODO: load the project dataset and validate its columns before analysis.

project_title <- {json.dumps(title)}
print(project_title)
""",
            "r",
        )
    if suffix in {".env", ".example"} or name == ".env.example":
        return (
            "# Add local-only configuration values. Never commit real secrets.\nAPP_ENV=development\n",
            "text",
        )
    if name == ".gitignore":
        return (
            "# Local environments and generated files\n.env\n.env.*\n!.env.example\n.venv/\nnode_modules/\n__pycache__/\n*.py[cod]\ndist/\nbuild/\n",
            "text",
        )
    if suffix == ".ipynb":
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {title}\n",
                        f"{objective}\n",
                        "\n",
                        "Work through the project tasks below and record outputs.",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# TODO: load the provided dataset and implement the project analysis.\n"
                    ],
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {"name": "python"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        return json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", "json"
    return (
        f"# {path}\n# {purpose or objective}\n# TODO: implement this file using the project's milestones and acceptance criteria.\n",
        "text",
    )


def _default_entries(course_slug: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    slug = course_slug.lower()
    if slug in {"html", "css", "bootstrap", "jquery", "xml"}:
        names = [
            ("index.html", "Main page and semantic structure."),
            ("styles.css", "Responsive presentation."),
            ("app.js", "Progressive enhancement and interactions."),
        ]
    elif slug in {"react", "vue", "angular", "nextjs"}:
        names = [
            ("package.json", "Pinned scripts and dependencies."),
            ("src/App.jsx", "Main UI and project behavior."),
            ("src/styles.css", "Responsive styles."),
        ]
        if slug in {"react", "vue"}:
            names.append(("src/main.jsx", "Application entry point."))
    elif slug in {"flask", "fastapi", "django", "python"}:
        names = [
            (
                (
                    "main.py"
                    if slug == "python"
                    else "app.py" if slug == "flask" else "main.py"
                ),
                "Application entry point.",
            ),
            ("requirements.txt", "Project dependencies."),
            ("tests/test_project.py", "Project behavior tests."),
        ]
    elif slug in {"postgresql", "mysql", "sqlite", "sql"}:
        names = [
            ("schema.sql", "Database schema and constraints."),
            ("queries.sql", "Required queries and verification."),
        ]
    elif slug == "docker":
        names = [
            ("Dockerfile", "Container image configuration."),
            ("compose.yaml", "Local service orchestration."),
        ]
    elif slug in {"nodejs", "expressjs"}:
        names = [
            ("package.json", "Dependencies and scripts."),
            ("app.js", "Server and application routes."),
            ("tests/app.test.js", "Route and behavior tests."),
        ]
    else:
        names = [
            ("README.md", "Setup and implementation guide."),
            (
                "main.txt",
                "Project entry file; replace with technology-specific source.",
            ),
        ]
    return [{"path": path, "purpose": purpose} for path, purpose in names]


def build_project_guide(
    course_slug: str,
    course_doc: dict[str, Any],
    project_doc: dict[str, Any],
    course_dir: Path,
) -> dict[str, Any]:
    project = {
        key: project_doc[key]
        for key in (
            "id",
            "slug",
            "title",
            "sequence",
            "difficulty",
            "tier",
            "objective",
            "scenario",
            "prerequisites",
            "prerequisite_lesson_ids",
            "recommended_lesson_range",
            "recommended_module_range",
            "recommended_module_ranges",
            "recommended_lessons",
            "recommended_lesson_ids",
            "target_skills",
            "skills",
            "required_features",
            "stretch_features",
            "acceptance_criteria",
            "architecture",
            "troubleshooting",
            "setup_steps",
            "milestones",
            "tests",
            "tests_and_validation",
            "test_plan",
            "rubric",
            "rubric_total",
            "review_method",
            "status",
            "status_note",
        )
        if key in project_doc
    }
    raw_entries = _as_list(project_doc.get("starter_files"))
    entries: list[dict[str, Any]] = []
    for raw in raw_entries:
        if isinstance(raw, str):
            path = _safe_rel_path(raw)
            purpose = "Starter file listed in the project manifest."
            embedded = None
            lang = None
        elif isinstance(raw, dict):
            path = _safe_rel_path(raw.get("path") or raw.get("name"))
            purpose = str(raw.get("purpose") or "Starter source file.")
            embedded = (
                raw.get("contents") if isinstance(raw.get("contents"), str) else None
            )
            lang = raw.get("language") if isinstance(raw.get("language"), str) else None
        else:
            continue
        if not path or is_protected_project_path(path):
            continue
        if path.endswith("/"):
            entries.append(
                {
                    "path": path,
                    "purpose": purpose,
                    "is_directory": True,
                    "contents": "",
                    "language": "text",
                    "source_kind": "directory_placeholder",
                }
            )
            continue
        entries.append(
            {"path": path, "purpose": purpose, "embedded": embedded, "language": lang}
        )
    if not entries:
        entries = [
            {
                "path": _safe_rel_path(item["path"]),
                "purpose": item["purpose"],
                "embedded": None,
                "language": None,
            }
            for item in _default_entries(course_slug, project)
        ]

    # Fill in the minimum boot/configuration files that make a declared project easier to run.
    # Preserve the manifest's files; only add a file when an equivalent basename is absent.
    slug = course_slug.lower()
    foundations: list[tuple[str, str, set[str]]] = []
    if slug in {"html", "css", "bootstrap", "jquery", "javascript"}:
        foundations = [
            (
                "index.html",
                "Browser entry page and semantic structure.",
                {"index.html", "index.htm", "home.html"},
            ),
            (
                "styles.css",
                "Responsive presentation layer.",
                {"styles.css", "style.css", "app.css"},
            ),
            (
                "app.js",
                "Browser interaction entry point.",
                {"app.js", "script.js", "main.js", "index.js"},
            ),
        ]
    elif slug == "react":
        foundations = [
            (
                "package.json",
                "Development scripts and pinned frontend dependencies.",
                {"package.json"},
            ),
            ("index.html", "Vite browser entry document.", {"index.html"}),
            ("vite.config.js", "Vite configuration for React JSX.", {"vite.config.js"}),
            ("src/main.jsx", "React application entry point.", {"main.jsx", "main.js"}),
            (
                "src/App.jsx",
                "Main React application component.",
                {"app.jsx", "app.tsx"},
            ),
            (
                "src/styles.css",
                "Responsive application styling.",
                {"styles.css", "style.css"},
            ),
        ]
    elif slug == "vue":
        foundations = [
            (
                "package.json",
                "Development scripts and Vue dependencies.",
                {"package.json"},
            ),
            ("index.html", "Vite browser entry document.", {"index.html"}),
            (
                "vite.config.js",
                "Vite configuration for Vue single-file components.",
                {"vite.config.js"},
            ),
            ("src/main.js", "Vue application entry point.", {"main.js", "main.ts"}),
            ("src/App.vue", "Main Vue application component.", {"app.vue"}),
            (
                "src/style.css",
                "Responsive application styling.",
                {"style.css", "styles.css"},
            ),
        ]
    elif slug in {"nextjs"}:
        foundations = [
            (
                "package.json",
                "Next.js scripts and runtime dependencies.",
                {"package.json"},
            ),
            (
                "app/page.jsx",
                "Primary page route.",
                {"page.jsx", "page.tsx", "index.jsx"},
            ),
            (
                "app/globals.css",
                "Global responsive styles.",
                {"globals.css", "global.css"},
            ),
        ]
    elif slug in {"flask"}:
        foundations = [
            (
                "app.py",
                "Flask application and route entry point.",
                {"app.py", "main.py", "run.py"},
            ),
            ("requirements.txt", "Python runtime dependencies.", {"requirements.txt"}),
            (
                "templates/index.html",
                "Jinja template for the primary page.",
                {"index.html", "home.html"},
            ),
            (
                "static/styles.css",
                "Static styles for the Flask templates.",
                {"styles.css", "style.css", "app.css"},
            ),
            (
                "tests/test_app.py",
                "Automated tests for Flask routes.",
                {"test_app.py", "test_main.py", "test_project.py"},
            ),
        ]
    elif slug == "fastapi":
        foundations = [
            (
                "app/main.py",
                "FastAPI application and route entry point.",
                {"main.py", "app.py"},
            ),
            ("requirements.txt", "Python runtime dependencies.", {"requirements.txt"}),
            (
                "tests/test_main.py",
                "API behavior tests.",
                {"test_main.py", "test_app.py", "test_project.py"},
            ),
        ]
    elif slug in {"python", "django"}:
        foundations = [
            (
                "main.py" if slug == "python" else "manage.py",
                "Application entry point.",
                {"main.py", "app.py", "manage.py", "run.py"},
            ),
            ("requirements.txt", "Python runtime dependencies.", {"requirements.txt"}),
            (
                "tests/test_project.py",
                "Automated project tests.",
                {"test_project.py", "test_main.py", "test_app.py"},
            ),
        ]
    elif slug in {"nodejs", "expressjs"}:
        foundations = [
            ("package.json", "Scripts and runtime dependencies.", {"package.json"}),
            (
                "app.js",
                "Application entry point.",
                {"app.js", "server.js", "index.js", "main.js"},
            ),
            (
                "tests/app.test.js",
                "Repeatable behavior tests.",
                {"app.test.js", "server.test.js", "app.spec.js"},
            ),
        ]
    elif slug in {"postgresql", "mysql", "sqlite", "sql"}:
        foundations = [
            (
                "schema.sql",
                "Database schema, constraints, and relationships.",
                {"schema.sql", "01-schema.sql", "create_tables.sql"},
            ),
            (
                "queries.sql",
                "Project queries and verification statements.",
                {"queries.sql", "query.sql", "reports.sql"},
            ),
        ]
    elif slug == "docker":
        foundations = [
            (
                "Dockerfile",
                "Reproducible container image instructions.",
                {"dockerfile"},
            ),
            (
                "compose.yaml",
                "Local multi-service development configuration.",
                {
                    "compose.yaml",
                    "compose.yml",
                    "docker-compose.yml",
                    "docker-compose.yaml",
                },
            ),
        ]

    existing_names = {
        PurePosixPath(str(item.get("path", "")).rstrip("/")).name.lower()
        for item in entries
    }
    for foundation_path, foundation_purpose, equivalent_names in foundations:
        if existing_names.isdisjoint({name.lower() for name in equivalent_names}):
            entries.append(
                {
                    "path": foundation_path,
                    "purpose": foundation_purpose,
                    "embedded": None,
                    "language": None,
                }
            )
            existing_names.add(PurePosixPath(foundation_path).name.lower())

    # Directory-only declarations indicate where code belongs; create an appropriately
    # named starter component/test so the guide has an actual file to edit.
    extras: list[dict[str, Any]] = []
    existing = {item.get("path") for item in entries}
    for item in entries:
        path = item.get("path", "")
        if not path.endswith("/"):
            continue
        folder = path.rstrip("/")
        leaf = PurePosixPath(folder).name.lower()
        if leaf == "components":
            name = (
                "ProjectFeature.vue"
                if course_slug == "vue"
                else (
                    "ProjectFeature.jsx"
                    if course_slug in {"react", "angular", "angularjs", "nextjs"}
                    else "feature.py"
                )
            )
            extra_path = f"{folder}/{name}"
            if extra_path not in existing:
                extras.append(
                    {
                        "path": extra_path,
                        "purpose": "Example child file inside the declared components directory.",
                        "embedded": None,
                        "language": None,
                    }
                )
        elif leaf in {"tests", "test"}:
            name = (
                "test_project.py"
                if course_slug in {"python", "flask", "fastapi", "django"}
                else (
                    "app.test.js"
                    if course_slug in {"react", "nodejs", "expressjs", "javascript"}
                    else "README.md"
                )
            )
            extra_path = f"{folder}/{name}"
            if extra_path not in existing:
                extras.append(
                    {
                        "path": extra_path,
                        "purpose": "Test scaffold for the project behavior.",
                        "embedded": None,
                        "language": None,
                    }
                )
    entries.extend(extras)

    safe_files: list[dict[str, Any]] = []
    all_paths = [item["path"] for item in entries if not item.get("is_directory")]
    for item in entries:
        if item.get("is_directory"):
            safe_files.append(item)
            continue
        path = item["path"]
        suffix = PurePosixPath(path).suffix.lower()
        if item.get("embedded") is not None:
            contents = item["embedded"]
            source_kind = "provided_in_manifest"
        else:
            target = (course_dir / path).resolve()
            try:
                is_inside = course_dir.resolve() in target.parents
            except OSError:
                is_inside = False
            if is_inside and target.is_file() and suffix in TEXT_SUFFIXES:
                try:
                    if target.stat().st_size <= MAX_SOURCE_BYTES:
                        contents = target.read_text(encoding="utf-8")
                        source_kind = "provided_course_asset"
                    else:
                        contents = None
                        source_kind = "generated_scaffold"
                except (OSError, UnicodeDecodeError):
                    contents = None
                    source_kind = "generated_scaffold"
            else:
                contents = None
                source_kind = "generated_scaffold"
            if contents is None:
                contents, inferred_language = _template_for_file(
                    course_slug, project_doc, path, item.get("purpose", ""), all_paths
                )
                if not item.get("language"):
                    item["language"] = inferred_language
        if not item.get("language"):
            language_map = {
                ".html": "html",
                ".htm": "html",
                ".css": "css",
                ".scss": "scss",
                ".sass": "sass",
                ".js": "javascript",
                ".mjs": "javascript",
                ".cjs": "javascript",
                ".jsx": "jsx",
                ".ts": "typescript",
                ".tsx": "tsx",
                ".vue": "vue",
                ".py": "python",
                ".sql": "sql",
                ".md": "markdown",
                ".json": "json",
                ".yml": "yaml",
                ".yaml": "yaml",
                ".sh": "bash",
                ".php": "php",
                ".java": "java",
                ".c": "c",
                ".cpp": "cpp",
                ".go": "go",
                ".rs": "rust",
                ".rb": "ruby",
                ".lua": "lua",
                ".ps1": "powershell",
                ".xml": "xml",
                ".toml": "toml",
                ".sol": "solidity",
                ".r": "r",
            }
            item["language"] = language_map.get(suffix, "text")
        safe_files.append(
            {
                "path": path,
                "purpose": item.get("purpose", "Starter file."),
                "language": item.get("language", "text"),
                "contents": contents,
                "source_kind": source_kind,
                "is_directory": False,
            }
        )

    # Ensure a useful root README exists without accidentally mistaking tests/README.md
    # or docs/README.md for the project root README.
    runtime = _course_runtime(course_slug, project_doc)
    root_readme = next(
        (
            item
            for item in safe_files
            if not item.get("is_directory")
            and PurePosixPath(item.get("path", "")).parent == PurePosixPath(".")
            and PurePosixPath(item.get("path", "")).name.lower() == "readme.md"
        ),
        None,
    )
    if root_readme is None:
        safe_files.append(
            {
                "path": "README.md",
                "purpose": "Project setup, milestone, and validation instructions.",
                "language": "markdown",
                "contents": _generated_readme(project_doc, safe_files, runtime),
                "source_kind": "generated_scaffold",
                "is_directory": False,
            }
        )
    elif (
        not isinstance(root_readme.get("contents"), str)
        or not root_readme.get("contents", "").strip()
    ):
        root_readme["contents"] = _generated_readme(project_doc, safe_files, runtime)
        root_readme["language"] = "markdown"
        root_readme["source_kind"] = "generated_scaffold"

    # Any nested README that still lacks content gets a short path-specific guide.
    for item in safe_files:
        if (
            item.get("is_directory")
            or PurePosixPath(item.get("path", "")).name.lower() != "readme.md"
        ):
            continue
        if (
            not isinstance(item.get("contents"), str)
            or not item.get("contents", "").strip()
        ):
            item["contents"] = (
                f"# {project_doc.get('title') or 'Guided project'} — {item.get('path')}\n\n{item.get('purpose') or 'Add setup notes and verification steps for this folder.'}\n"
            )
            item["language"] = "markdown"
            item["source_kind"] = "generated_scaffold"

    runtime = _course_runtime(course_slug, project_doc)
    milestones = _milestones(project_doc)
    paths = [item["path"] for item in safe_files]
    tree = _build_tree(paths)
    provided_count = sum(
        1
        for item in safe_files
        if item.get("source_kind") in {"provided_in_manifest", "provided_course_asset"}
        and not item.get("is_directory")
    )
    generated_count = sum(
        1
        for item in safe_files
        if item.get("source_kind") == "generated_scaffold"
        and not item.get("is_directory")
    )
    architecture = _as_list(project_doc.get("architecture"))
    if not architecture:
        architecture = [
            {
                "component": item["path"],
                "responsibility": item.get("purpose") or "Project file; inspect its contents and extend it for the milestone.",
            }
            for item in safe_files
            if not item.get("is_directory")
        ]
    troubleshooting = _as_list(project_doc.get("troubleshooting"))
    if not troubleshooting:
        troubleshooting = [
            {"problem": "A relative file or image does not load", "check": "Confirm the filename and relative path, including letter case, then reload the page from the project entry point."},
            {"problem": "The page looks different on a narrow screen", "check": "Use the browser responsive preview, remove fixed content widths, and test long text and images for overflow."},
            {"problem": "Keyboard users cannot reach or understand a control", "check": "Use native links and buttons, verify visible focus, and make every input's purpose and validation error clear."},
            {"problem": "The HTML validator reports an error", "check": "Fix the first structural or nesting error, re-run the validator, and test the affected behavior in a browser."},
        ] if course_slug.lower() == "html" else [
            {"problem": "The project does not start", "check": "Read the first terminal error, confirm the runtime and dependencies, and run the documented command from the project root."},
            {"problem": "An expected result is missing", "check": "Check paths, input data, and console or terminal messages, then repeat the smallest reproducible step."},
            {"problem": "A validation check fails", "check": "Compare the result with the acceptance criteria and fix one issue at a time before re-running tests."},
        ]
    return {
        "course": {
            "slug": course_slug,
            "title": (course_doc.get("course") or {}).get("title") or course_slug,
            "description": (course_doc.get("course") or {}).get("description") or "",
        },
        "project": project,
        "files": safe_files,
        "folder_tree": tree,
        "milestones": milestones,
        "runtime": runtime,
        "architecture": architecture,
        "troubleshooting": troubleshooting,
        "setup_steps": _as_list(project_doc.get("setup_steps")) or runtime.get("commands", []),
        "quality_checks": _as_list(project_doc.get("tests"))
        or _as_list(project_doc.get("tests_and_validation"))
        or _as_list(project_doc.get("test_plan")),
        "required_features": _requirements(project_doc),
        "stretch_features": _as_list(project_doc.get("stretch_features")),
        "rubric": _as_list(project_doc.get("rubric")),
        "file_summary": {
            "total_files": sum(
                1 for item in safe_files if not item.get("is_directory")
            ),
            "provided_files": provided_count,
            "generated_scaffolds": generated_count,
            "directory_placeholders": sum(
                1 for item in safe_files if item.get("is_directory")
            ),
        },
        "content_notice": "Files included in the manifest are preserved. If an older manifest lists only a file path and purpose, CodeLeaf creates a labelled starter scaffold for that path; that scaffold is not a reviewed full solution. Finish the milestones and tests before treating the project as complete.",
    }


def _build_tree(paths: list[str]) -> list[dict[str, Any]]:
    root: dict[str, Any] = {"name": "project-root", "type": "directory", "children": {}}
    for raw in paths:
        safe = _safe_rel_path(raw)
        if not safe:
            continue
        is_dir = safe.endswith("/")
        parts = [part for part in safe.rstrip("/").split("/") if part]
        current = root
        for index, part in enumerate(parts):
            final = index == len(parts) - 1
            node_type = "directory" if (not final or is_dir) else "file"
            if part not in current["children"]:
                current["children"][part] = {
                    "name": part,
                    "type": node_type,
                    "children": {},
                }
            elif node_type == "directory":
                current["children"][part]["type"] = "directory"
            current = current["children"][part]

    flattened: list[dict[str, Any]] = []

    def walk(node: dict[str, Any], prefix: str = "", depth: int = 0) -> None:
        children = sorted(
            node["children"].values(),
            key=lambda value: (value["type"] != "directory", value["name"].lower()),
        )
        for child in children:
            flattened.append(
                {
                    "name": child["name"],
                    "path": f"{prefix}{child['name']}{'/' if child['type'] == 'directory' else ''}",
                    "type": child["type"],
                    "depth": depth,
                }
            )
            if child["type"] == "directory":
                walk(child, f"{prefix}{child['name']}/", depth + 1)

    walk(root)
    return flattened


def project_guide_zip(guide: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        project = guide.get("project") or {}
        root_name = _slug_text(project.get("slug") or project.get("title") or "project")
        for item in _as_list(guide.get("files")):
            path = _safe_rel_path(item.get("path")) if isinstance(item, dict) else None
            if not path or path.endswith("/") or item.get("is_directory"):
                continue
            contents = item.get("contents")
            if not isinstance(contents, str):
                continue
            archive.writestr(f"{root_name}/{path}", contents)
        if not any(
            str(info.filename).lower().endswith("/readme.md")
            for info in archive.infolist()
        ):
            archive.writestr(
                f"{root_name}/README.md",
                f"# {project.get('title', 'Guided project')}\n\n{project.get('objective', '')}\n",
            )
    return buffer.getvalue()
