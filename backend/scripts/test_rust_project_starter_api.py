"""Exercise Rust project/starter routes against an isolated in-memory SQLite DB.

Run from backend/: python scripts/test_rust_project_starter_api.py
Never uses the configured development/production database.
"""

from __future__ import annotations

from uuid import uuid4
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
# The imported application settings must not try to construct a PostgreSQL engine.
# Requests below are separately routed to an isolated in-memory SQLite database.
os.environ["DATABASE_URL"] = "sqlite://"

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
                slug="rust",
                title="Rust — From Beginner to Professional Practice",
                description="local API test",
                category="Systems Programming",
                level="Beginner to Advanced",
                published=False,
                sort_order=35,
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
        response = client.get("/api/courses/rust/projects")
        assert response.status_code == 200, response.text
        items = response.json()["items"]
        assert len(items) == 9, f"expected 9 projects, got {len(items)}"
        first = items[0]
        assert first.get("starter_files"), "project response omitted starter references"
        assert first.get("starter_readme"), "project response omitted starter README"
        assert "reference_solution_file" not in first, "protected solution path leaked"

        slug = first["slug"]
        source = client.get(f"/api/courses/rust/projects/{slug}/starter-files/0")
        assert source.status_code == 200, source.text
        assert source.text.startswith("// CodeLeaf Rust project starter")
        assert 'filename="main.rs"' in source.headers.get("content-disposition", "")

        manifest = client.get(f"/api/courses/rust/projects/{slug}/starter-files/1")
        assert manifest.status_code == 200, manifest.text
        assert manifest.text.startswith("[package]")
        assert 'filename="Cargo.toml"' in manifest.headers.get(
            "content-disposition", ""
        )

        readme = client.get(f"/api/courses/rust/projects/{slug}/starter-files/readme")
        assert readme.status_code == 200, readme.text
        assert "purpose" in readme.text.lower()

        missing = client.get(f"/api/courses/rust/projects/{slug}/starter-files/999")
        assert missing.status_code == 404, missing.text

        main.settings.preview_draft_courses = False
        hidden = client.get("/api/courses/rust/projects")
        assert hidden.status_code == 404, hidden.text
        print(
            "PASS: Rust project list, .rs/.toml starter downloads, README, invalid index, "
            "draft-preview gate, and reference-solution path exclusion."
        )
    finally:
        main.app.dependency_overrides.clear()
        main.settings.app_env = prior_env
        main.settings.preview_draft_courses = prior_preview
        Base.metadata.drop_all(engine)
        engine.dispose()


if __name__ == "__main__":
    run()
