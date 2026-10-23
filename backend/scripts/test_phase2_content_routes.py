"""Integration checks for structured references and project guide starter ZIPs.

Run from backend/: python scripts/test_phase2_content_routes.py
The test uses a temporary SQLite database and temporary course content.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-phase2-content-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'content.db'}"
os.environ["JWT_SECRET"] = "Phase2-content-test-only-secret-not-for-deployment-2026"
os.environ["APP_ENV"] = "development"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
import app.main as main_module  # noqa: E402
from app.models import Course  # noqa: E402


def check(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    content_root = Path(_TEMP_DIR.name) / "courses"
    course_dir = content_root / "html"
    (course_dir / "references" / "entries").mkdir(parents=True, exist_ok=True)
    (course_dir / "projects").mkdir(parents=True, exist_ok=True)
    manifest = {
        "course": {"slug": "html", "title": "HTML Test Course", "description": "Test course"},
        "status": "published",
        "reference_index": "references/reference-index.json",
        "project_files": ["projects/profile-page.json"],
        "assessment_files": [],
        "module_files": [],
    }
    (course_dir / "course.json").write_text(json.dumps(manifest), encoding="utf-8")
    reference_index = {
        "id": "html-reference-index",
        "status": "published",
        "checked_on": "2026-10-22",
        "references": ["references/entries/html-standard.json"],
    }
    (course_dir / "references" / "reference-index.json").write_text(json.dumps(reference_index), encoding="utf-8")
    reference_entry = {
        "id": "html-standard",
        "slug": "html-standard",
        "title": "HTML Standard",
        "status": "published",
        "url": "https://html.spec.whatwg.org/multipage/",
        "publisher": "WHATWG",
        "supports": ["HTML elements", "Document structure"],
        "explanation": "The standard defines the requirements for HTML documents and elements.",
        "example": "<!doctype html>\n<html lang=\"en\">…</html>",
        "related_lesson_slugs": ["document-structure"],
    }
    (course_dir / "references" / "entries" / "html-standard.json").write_text(json.dumps(reference_entry), encoding="utf-8")
    project = {
        "id": "html-project-test",
        "slug": "profile-page",
        "title": "Profile Page",
        "status": "published",
        "objective": "Build an accessible profile page.",
        "architecture": [{"component": "index.html", "responsibility": "Defines page structure."}],
        "troubleshooting": [{"problem": "Styles do not load", "check": "Confirm the relative path."}],
        "setup_steps": [{"label": "Open", "command": "Open index.html in a browser."}],
        "milestones": [{"sequence": 1, "title": "Create semantics", "acceptance_criteria": ["Use main and headings."]}],
        "tests": [{"name": "Basic structure", "mode": "contains_all", "required_strings": ["<main>", "<h1>"]}],
        "starter_files": [
            {"path": "index.html", "language": "html", "contents": "<!doctype html>\n<html lang=\"en\"><main><h1>Starter profile</h1></main></html>"},
            {"path": "solution/answer.html", "language": "html", "contents": "PRIVATE-SOLUTION-MUST-NOT-APPEAR"},
            {"path": "answer-key.json", "language": "json", "contents": "{\"answer_key\":\"private\"}"},
            {"path": ".env", "language": "text", "contents": "SECRET=value"},
            {"path": "../escape.html", "language": "html", "contents": "OUTSIDE-ROOT"},
        ],
        "starter_readme": "README.md",
        "reference_solution": {"path": "solutions/private-answer.html", "contents": "PRIVATE-SOLUTION-MUST-NOT-APPEAR"},
    }
    (course_dir / "projects" / "profile-page.json").write_text(json.dumps(project), encoding="utf-8")

    old_root = main_module.COURSE_CONTENT_ROOT
    old_preview = settings.preview_draft_courses
    old_env = settings.app_env
    main_module.COURSE_CONTENT_ROOT = content_root
    settings.preview_draft_courses = False
    settings.app_env = "development"
    client: TestClient | None = None
    try:
        with SessionLocal() as db:
            db.add(Course(slug="html", title="HTML Test Course", description="Test", category="Web", level="Beginner", published=True, sort_order=1))
            db.commit()
        client = TestClient(main_module.app)

        references = client.get("/api/courses/html/references")
        reference_payload = references.json()
        check(references.status_code == 200 and len(reference_payload["items"]) == 1, "reference index loads separate entry JSON files")
        entry = reference_payload["items"][0]
        check(entry["slug"] == "html-standard" and entry["publisher"] == "WHATWG", "reference API preserves entry identity and publisher metadata")
        check(entry["explanation"] and entry["example"] and entry["related_lesson_slugs"] == ["document-structure"], "reference entry includes explanation, example and related lessons")
        check(entry["url"].startswith("https://"), "reference entries only expose valid HTTPS source links in this fixture")

        project_list = client.get("/api/courses/html/projects")
        check(project_list.status_code == 200 and len(project_list.json()["items"]) == 1, "published project list returns the authored project")
        list_text = project_list.text
        check("solution/answer.html" not in list_text and "answer-key.json" not in list_text and ".env" not in list_text, "project list hides protected starter paths")

        guide_response = client.get("/api/courses/html/projects/profile-page")
        guide = guide_response.json()
        check(guide_response.status_code == 200 and guide["project"]["slug"] == "profile-page", "project guide resolves by stable project slug")
        check(guide["architecture"][0]["component"] == "index.html" and guide["troubleshooting"][0]["problem"] == "Styles do not load", "project guide returns architecture and troubleshooting content")
        check(any(item["path"] == "index.html" and "Starter profile" in item["contents"] for item in guide["files"]), "project guide preserves embedded starter file contents")
        guide_text = guide_response.text
        check("PRIVATE-SOLUTION-MUST-NOT-APPEAR" not in guide_text and "SECRET=value" not in guide_text, "project guide response does not expose private solution or environment contents")

        starter = client.get("/api/courses/html/projects/profile-page/starter-kit.zip")
        check(starter.status_code == 200 and starter.headers.get("content-type", "").startswith("application/zip"), "project starter download returns a ZIP archive")
        with ZipFile(BytesIO(starter.content)) as archive:
            names = archive.namelist()
            check(archive.testzip() is None, "starter ZIP integrity check passes")
            check(any(name.endswith("/index.html") for name in names), "starter ZIP contains the declared HTML entry file")
            check(not any("solution" in name.casefold() or "answer-key" in name.casefold() or "/.env" in name.casefold() for name in names), "starter ZIP excludes solution, answer-key and environment paths")
            all_content = "\n".join(archive.read(name).decode("utf-8", errors="replace") for name in names)
            check("PRIVATE-SOLUTION-MUST-NOT-APPEAR" not in all_content and "SECRET=value" not in all_content and "OUTSIDE-ROOT" not in all_content, "starter ZIP does not include protected or traversal content")
    finally:
        try:
            if client is not None:
                client.close()
        finally:
            engine.dispose()
            main_module.COURSE_CONTENT_ROOT = old_root
            settings.preview_draft_courses = old_preview
            settings.app_env = old_env
    print("Phase 2 content route and starter ZIP tests completed.")


if __name__ == "__main__":
    main()
