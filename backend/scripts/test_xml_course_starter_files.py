"""Test XML-related project starter file downloads with temporary SQLite and course files.

Run from backend/: python scripts/test_xml_course_starter_files.py
This test does not use the configured development/production database.
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
import sys

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-xml-starter-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'starter-test.db'}"
os.environ["JWT_SECRET"] = "xml-starter-test-secret-not-for-deployment"
os.environ["APP_ENV"] = "development"
os.environ["PREVIEW_DRAFT_COURSES"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.models import Course
import app.main as main_module
from app.main import app

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")

def main() -> None:
    Base.metadata.create_all(bind=engine)
    courses_root = Path(_TEMP_DIR.name) / "courses"
    course_root = courses_root / "xml"
    project_root = course_root / "projects"
    starter_root = project_root / "starter-files" / "sample"
    starter_root.mkdir(parents=True)
    (course_root / "course.json").write_text(json.dumps({"course":{"slug":"xml","title":"XML test course"},"project_files":["projects/test-project.json"]}),encoding="utf-8")
    files = {
        "README.md": "# XML starter\n",
        "sample.xml": "<catalog/>\n",
        "catalog.xsd": "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"/>\n",
        "catalog.xsl": "<xsl:stylesheet version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\"/>\n",
        "query.xq": "1 + 1\n",
        "catalog.dtd": "<!ELEMENT catalog EMPTY>\n",
        "catalog.xslt": "<xsl:stylesheet version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\"/>\n",
        "notes.txt": "Plain-text transformation notes\n",
        "not-allowed.exe": "not a real executable\n",
    }
    for name, value in files.items():
        (starter_root / name).write_text(value,encoding="utf-8")
    starter_files=[f"projects/starter-files/sample/{name}" for name in files]
    project={"id":"xml-test-project","slug":"xml-test-project","title":"XML starter route test","status":"draft","sequence":1,"starter_files":starter_files,"starter_readme":starter_files[0]}
    (project_root / "test-project.json").write_text(json.dumps(project),encoding="utf-8")

    old_root = main_module.COURSE_CONTENT_ROOT
    old_env = settings.app_env
    old_preview = settings.preview_draft_courses
    main_module.COURSE_CONTENT_ROOT = courses_root
    settings.app_env = "development"
    settings.preview_draft_courses = True
    with SessionLocal() as db:
        db.add(Course(slug="xml",title="XML test course",description="test",category="Data Formats",level="Beginner",published=False,sort_order=999))
        db.commit()
    client=TestClient(app)
    try:
        listed=client.get("/api/courses/xml/projects")
        require(listed.status_code == 200 and listed.json()["items"][0]["slug"] == "xml-test-project", "draft project is visible only in explicit local preview")
        for index, suffix in [(1,".xml"),(2,".xsd"),(3,".xsl"),(4,".xq"),(5,".dtd"),(6,".xslt"),(7,".txt")]:
            response=client.get(f"/api/courses/xml/projects/xml-test-project/starter-files/{index}")
            require(response.status_code == 200 and bool(response.text), f"explicitly listed {suffix} starter can be downloaded")
        denied=client.get("/api/courses/xml/projects/xml-test-project/starter-files/8")
        require(denied.status_code == 404, "unapproved executable suffix is rejected")
    finally:
        client.close()
        engine.dispose()
        main_module.COURSE_CONTENT_ROOT = old_root
        settings.app_env = old_env
        settings.preview_draft_courses = old_preview
    print("XML course starter-file API test completed.")

if __name__ == "__main__":
    try:
        main()
    finally:
        _TEMP_DIR.cleanup()
