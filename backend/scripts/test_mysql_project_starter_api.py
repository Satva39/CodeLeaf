"""Verify MySQL project SQL starter downloads and draft privacy using SQLite only.

Run from backend/: python scripts/test_mysql_project_starter_api.py
No configured DATABASE_URL or production database is used.
"""
from __future__ import annotations

from uuid import uuid4
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.db import Base
from app.models import Course


def run() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with test_sessions() as db:
        db.add(Course(
            id=uuid4(), slug="mysql", title="MySQL — local test",
            description="local API test", category="Database", level="Beginner",
            published=False, sort_order=90,
        ))
        db.commit()

    def override_get_db():
        db = test_sessions()
        try:
            yield db
        finally:
            db.close()

    prior_env = main.settings.app_env
    prior_preview = main.settings.preview_draft_courses
    main.app.dependency_overrides[main.get_db] = override_get_db
    main.settings.app_env = "development"
    main.settings.preview_draft_courses = True
    try:
        client = TestClient(main.app)
        response = client.get("/api/courses/mysql/projects")
        assert response.status_code == 200, response.text
        items = response.json()["items"]
        assert len(items) == 11, f"expected 11 draft projects, got {len(items)}"
        assert all("reference_solution_file" not in p for p in items), "protected path leaked"

        starter_response = client.get(
            "/api/courses/mysql/projects/student-management-database/starter-files/0"
        )
        assert starter_response.status_code == 200, starter_response.text
        assert "CREATE TABLE students" in starter_response.text
        assert 'filename="001-student-management.sql"' in starter_response.headers.get(
            "content-disposition", ""
        )

        missing_response = client.get(
            "/api/courses/mysql/projects/student-management-database/starter-files/999"
        )
        assert missing_response.status_code == 404, missing_response.text

        main.settings.preview_draft_courses = False
        hidden_response = client.get("/api/courses/mysql/projects")
        assert hidden_response.status_code == 404, hidden_response.text
        print("PASS: MySQL starter SQL download, draft preview gate, invalid index rejection, and protected solution path exclusion.")
    finally:
        main.app.dependency_overrides.clear()
        main.settings.app_env = prior_env
        main.settings.preview_draft_courses = prior_preview
        Base.metadata.drop_all(engine)
        engine.dispose()


if __name__ == "__main__":
    run()
