"""Test Dart project starter routes using an isolated in-memory SQLite DB."""
from __future__ import annotations
from uuid import uuid4
import os, sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ["DATABASE_URL"] = "sqlite://"
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import main
from app.db import Base
from app.models import Course, Lesson, Module

def run() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with sessions() as db:
        course_id = uuid4()
        db.add(Course(id=course_id, slug="dart", title="Dart — From Beginner to Professional Practice", description="Local API test", category="Programming Languages", level="Beginner to Professional", published=False, sort_order=90))
        module_id = uuid4()
        db.add(Module(id=module_id, course_id=course_id, slug="introduction-to-dart", title="Introduction to Dart", sort_order=1, level="beginner"))
        db.add(Lesson(id=uuid4(), module_id=module_id, slug="introduction-to-dart", title="Introduction to Dart", sort_order=1, estimated_minutes=10, is_published=False, content={"id":"dart-lesson-001", "module_slug":"introduction-to-dart", "level":"beginner", "track":"core-foundations", "keywords":["dart"], "prerequisites":[], "previous_lesson_id":None, "next_lesson_id":"dart-lesson-002", "learning_outcomes":["Explain Dart","Run a small program"], "_codeleaf_course_slug":"dart", "content":{"knowledge_check_file":"exams/question-files/lesson-001-questions.json"}}))
        db.commit()
    def override_get_db():
        db = sessions()
        try: yield db
        finally: db.close()
    prior_env = main.settings.app_env
    prior_preview = main.settings.preview_draft_courses
    main.app.dependency_overrides[main.get_db] = override_get_db
    main.settings.app_env = "development"
    main.settings.preview_draft_courses = True
    try:
        client = TestClient(main.app)
        response = client.get("/api/courses/dart/projects")
        assert response.status_code == 200, response.text
        items = response.json()["items"]
        assert len(items) == 14, f"expected 14 projects, got {len(items)}"
        first = items[0]
        assert first.get("starter_files") and first.get("starter_readme")
        assert "reference_solution_file" not in first, "protected solution path leaked"
        slug = first["slug"]
        source = client.get(f"/api/courses/dart/projects/{slug}/starter-files/0")
        assert source.status_code == 200, source.text
        assert source.text.startswith("// CodeLeaf Dart project starter")
        assert 'filename="main.dart"' in source.headers.get("content-disposition", "")
        manifest = client.get(f"/api/courses/dart/projects/{slug}/starter-files/1")
        assert manifest.status_code == 200, manifest.text
        assert manifest.text.startswith("name: command_line_calculator")
        assert 'filename="pubspec.yaml"' in manifest.headers.get("content-disposition", "")
        readme = client.get(f"/api/courses/dart/projects/{slug}/starter-files/readme")
        assert readme.status_code == 200, readme.text
        assert "objective" in readme.text.lower() and "dart test" in readme.text

        # Public question retrieval must omit answer keys/explanations; grading can return feedback after submission.
        check = client.get("/api/courses/dart/lessons/introduction-to-dart/knowledge-check")
        assert check.status_code == 200, check.text
        question_items = check.json()["questions"]
        assert len(question_items) == 3
        assert all("answer_key" not in q and "explanation" not in q for q in question_items)
        import json
        course_root = main.COURSE_CONTENT_ROOT / "dart"
        answer_bank = json.loads((course_root / "exams/question-files/lesson-001-questions.json").read_text(encoding="utf-8"))
        first_question = answer_bank["questions"][0]
        graded = client.post("/api/courses/dart/lessons/introduction-to-dart/knowledge-check/submit", json={"answers": {first_question["id"]: first_question["answer_key"]}})
        assert graded.status_code == 200, graded.text
        assert graded.json()["correct_count"] == 1
        assert graded.json()["results"][0]["correct_answer"] == first_question["answer_key"]

        missing = client.get(f"/api/courses/dart/projects/{slug}/starter-files/999")
        assert missing.status_code == 404, missing.text
        main.settings.preview_draft_courses = False
        hidden = client.get("/api/courses/dart/projects")
        assert hidden.status_code == 404, hidden.text
        print("PASS: Dart project list, .dart/.yaml downloads, README, draft-preview gate, knowledge-check answer-key withholding/grading, invalid index, and solution-path exclusion.")
    finally:
        main.app.dependency_overrides.clear()
        main.settings.app_env = prior_env
        main.settings.preview_draft_courses = prior_preview
        Base.metadata.drop_all(engine)
        engine.dispose()

if __name__ == "__main__": run()
