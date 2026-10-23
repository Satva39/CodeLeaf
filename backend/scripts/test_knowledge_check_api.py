"""Exercise the protected knowledge-check API against a temporary SQLite database.

Run from backend/: python scripts/test_knowledge_check_api.py
Uses only temporary test data and never touches the configured PostgreSQL database.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-knowledge-check-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'knowledge-check.db'}"
os.environ["JWT_SECRET"] = "test-only-secret-not-for-deployment"
os.environ["APP_ENV"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.config import settings
from app.db import Base, SessionLocal, engine
import app.main as main_module
from app.models import Course, Lesson, Module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    temp_content_root = Path(_TEMP_DIR.name) / "content" / "courses"
    course_dir = temp_content_root / "php"
    question_path = (
        course_dir / "exams" / "question-files" / "lesson-001-questions.json"
    )
    question_path.parent.mkdir(parents=True, exist_ok=True)
    question_set = {
        "id": "php-test-knowledge-check",
        "lesson_id": "php-lesson-001",
        "lesson_slug": "intro",
        "title": "Test knowledge check",
        "status": "published",
        "questions": [
            {
                "id": "php-test-q-01",
                "type": "single_choice",
                "prompt": "Which option is safe?",
                "options": ["safe", "unsafe"],
                "answer_key": "safe",
                "explanation": "Choose the validated option.",
            },
            {
                "id": "php-test-q-02",
                "type": "single_choice",
                "prompt": "What should be checked?",
                "options": ["nothing", "input"],
                "answer_key": "input",
                "explanation": "Check untrusted inputs.",
            },
        ],
    }
    question_path.write_text(json.dumps(question_set), encoding="utf-8")
    old_root = main_module.COURSE_CONTENT_ROOT
    old_preview = settings.preview_draft_courses
    old_env = settings.app_env
    main_module.COURSE_CONTENT_ROOT = temp_content_root
    settings.preview_draft_courses = False
    settings.app_env = "test"
    client: TestClient | None = None
    try:
        with SessionLocal() as db:
            course = Course(
                slug="php",
                title="PHP test course",
                description="test",
                category="Backend & APIs",
                level="Beginner",
                published=True,
                sort_order=1,
            )
            db.add(course)
            db.flush()
            module = Module(
                course_id=course.id,
                slug="foundations",
                title="Foundations",
                sort_order=1,
                level="Core",
            )
            db.add(module)
            db.flush()
            lesson = Lesson(
                module_id=module.id,
                slug="intro",
                title="PHP intro",
                sort_order=1,
                estimated_minutes=10,
                is_published=True,
                content={
                    "id": "php-lesson-001",
                    "_codeleaf_course_slug": "php",
                    "content": {
                        "knowledge_check_file": "exams/question-files/lesson-001-questions.json"
                    },
                },
            )
            db.add(lesson)
            db.commit()

        client = TestClient(main_module.app)
        quiz_url = "/api/courses/php/lessons/intro/knowledge-check"
        initial = client.get(quiz_url)
        require(initial.status_code == 200, "published knowledge check can be fetched")
        require(
            "answer_key" not in initial.text
            and "explanation" not in initial.text
            and "correct_answer" not in initial.text,
            "GET response withholds answer keys and explanations",
        )
        require(
            len(initial.json().get("questions", [])) == 2,
            "GET response returns all learner-safe question prompts and options",
        )

        submitted = client.post(
            f"{quiz_url}/submit",
            json={"answers": {"php-test-q-01": "safe", "php-test-q-02": "nothing"}},
        )
        payload = submitted.json()
        require(
            submitted.status_code == 200
            and payload.get("correct_count") == 1
            and payload.get("answered_count") == 2,
            "submission is graded server-side and returns the expected score",
        )
        require(
            payload.get("results", [])[0].get("correct_answer") == "safe"
            and payload.get("results", [])[1].get("explanation")
            == "Check untrusted inputs.",
            "answer and explanation feedback is returned only after submission",
        )
        invalid_option = client.post(
            f"{quiz_url}/submit", json={"answers": {"php-test-q-01": "not-an-option"}}
        )
        require(invalid_option.status_code == 422, "non-option answers are rejected")
        unknown_id = client.post(
            f"{quiz_url}/submit", json={"answers": {"other-question": "safe"}}
        )
        require(unknown_id.status_code == 422, "unknown question IDs are rejected")

        question_set["status"] = "draft"
        question_path.write_text(json.dumps(question_set), encoding="utf-8")
        draft_hidden = client.get(quiz_url)
        require(
            draft_hidden.status_code == 404,
            "draft knowledge checks are hidden outside local preview",
        )
    finally:
        # Close the HTTP client and dispose SQLAlchemy's SQLite connection pool
        # before TemporaryDirectory cleanup runs on Windows. An open pooled
        # connection can otherwise keep knowledge-check.db locked at interpreter exit.
        try:
            if client is not None:
                client.close()
        finally:
            try:
                engine.dispose()
            finally:
                main_module.COURSE_CONTENT_ROOT = old_root
                settings.preview_draft_courses = old_preview
                settings.app_env = old_env
    print("Knowledge-check API test completed.")


if __name__ == "__main__":
    main()
