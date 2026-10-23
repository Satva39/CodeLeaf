"""Exercise the C++ project/starter routes against an isolated in-memory SQLite DB.

Run from backend/: python scripts/test_cpp_project_starter_api.py
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
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with test_sessions() as db:
        db.add(
            Course(
                id=uuid4(),
                slug="cpp",
                title="C++ — From Beginner to Professional",
                description="local API test",
                category="Programming",
                level="Beginner",
                published=False,
                sort_order=90,
            )
        )
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
        response = client.get("/api/courses/cpp/projects")
        assert response.status_code == 200, response.text
        items = response.json()["items"]
        assert len(items) == 13, f"expected 13 draft projects, got {len(items)}"
        first = items[0]
        assert first.get(
            "starter_files"
        ), "project response omitted starter file references"
        assert first.get("starter_readme"), "project response omitted starter README"
        assert "reference_solution_file" not in first, "protected solution path leaked"

        slug = first["slug"]
        source_response = client.get(
            f"/api/courses/cpp/projects/{slug}/starter-files/0"
        )
        assert source_response.status_code == 200, source_response.text
        assert source_response.text.startswith(
            "#include"
        ), "starter source was not returned"
        assert 'filename="main.cpp"' in source_response.headers.get(
            "content-disposition", ""
        )

        readme_response = client.get(
            f"/api/courses/cpp/projects/{slug}/starter-files/readme"
        )
        assert readme_response.status_code == 200, readme_response.text
        assert "starter files" in readme_response.text.lower()

        missing_response = client.get(
            f"/api/courses/cpp/projects/{slug}/starter-files/999"
        )
        assert missing_response.status_code == 404, missing_response.text

        main.settings.preview_draft_courses = False
        hidden_response = client.get("/api/courses/cpp/projects")
        assert hidden_response.status_code == 404, hidden_response.text
        print(
            "PASS: project list, starter source, README download, invalid-index "
            "rejection, draft-visibility gate, and solution-path exclusion."
        )
    finally:
        main.app.dependency_overrides.clear()
        main.settings.app_env = prior_env
        main.settings.preview_draft_courses = prior_preview
        Base.metadata.drop_all(engine)
        engine.dispose()


if __name__ == "__main__":
    run()
