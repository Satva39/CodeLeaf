"""Self-contained API contract checks using a temporary SQLite database.

Run from backend/: python scripts/test_course_api_contract.py
The script never uses the configured PostgreSQL database and deletes its temporary DB on exit.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import timedelta
from pathlib import Path
import sys

# Set test-only settings before importing app.config/app.db. Environment values take
# precedence over the repository .env file, preventing this test from touching production.
_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-api-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'contract.db'}"
os.environ["JWT_SECRET"] = "test-only-secret-not-for-deployment"
os.environ["APP_ENV"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.main import TOKEN_ALGORITHM, app, calculate_streaks, utc_now
from app.auth_security import token_digest
from app.models import (
    Course,
    Entitlement,
    AuthSession,
    Exercise,
    Lesson,
    Module,
    User,
    XPTransaction,
)

# Keep this API contract fixture independent from real course content in the
# repository. The test uses the slug "html", which can also have a real course
# directory with projects and assets; isolating that directory makes its
# assertions deterministic and prevents tests from reading production content.
import app.main as main_module

_TEST_CONTENT_ROOT = Path(_TEMP_DIR.name) / "content" / "courses"
_TEST_HTML_ROOT = _TEST_CONTENT_ROOT / "html"
(_TEST_HTML_ROOT / "assets" / "diagrams").mkdir(parents=True, exist_ok=True)
(_TEST_HTML_ROOT / "projects").mkdir(parents=True, exist_ok=True)
(_TEST_HTML_ROOT / "course.json").write_text(
    json.dumps({"project_files": ["projects/001-draft-project.json"]}),
    encoding="utf-8",
)
(_TEST_HTML_ROOT / "projects" / "001-draft-project.json").write_text(
    json.dumps(
        {
            "id": "html-test-project",
            "slug": "draft-project",
            "title": "Draft fixture",
            "sequence": 1,
            "status": "draft",
        }
    ),
    encoding="utf-8",
)
(_TEST_HTML_ROOT / "assets" / "diagrams" / "module-01-overview.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675"><title>Test fixture</title></svg>',
    encoding="utf-8",
)
(_TEST_HTML_ROOT / "assets" / "diagrams" / "module-01-overview.diagram.json").write_text(
    json.dumps({
        "renderer": "codeleaf-native-dynamic-diagram",
        "title": "Safe test diagram",
        "layout": {"kind": "flow", "columns": 2, "rows": 1},
        "nodes": [
            {"id": "a", "order": 0, "row": 0, "column": 0, "title": "Source", "sourceTextIndices": [0], "labels": [{"source_index": 0, "text": "Source", "role": "title"}]},
            {"id": "b", "order": 1, "row": 0, "column": 1, "title": "Result", "sourceTextIndices": [1], "labels": [{"source_index": 1, "text": "Result", "role": "title"}]},
        ],
        "edges": [{"from": "a", "to": "b", "direction": "right", "kind": "arrow"}],
        "source_text": [{"index": 0, "text": "Source"}, {"index": 1, "text": "Result"}],
        "source_text_count": 2,
        "text_mapping_complete": True,
        "metadata_text_indices": [],
        "header_labels": [],
        "annotations": [],
    }),
    encoding="utf-8",
)
(_TEST_HTML_ROOT / "assets" / "diagrams" / "private-data.json").write_text(
    json.dumps({"answer_key": "must-not-be-public"}), encoding="utf-8"
)
main_module.COURSE_CONTENT_ROOT = _TEST_CONTENT_ROOT


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = User(
            email="api-contract@example.invalid",
            display_name="Test Learner",
            password_hash="test-only-no-password-login",
            username="api-contract-test",
        )
        course = Course(
            slug="html",
            title="HTML Contract Test",
            description="test",
            category="Web Development",
            level="Beginner",
            published=False,
            sort_order=1,
        )
        db.add_all([user, course])
        db.flush()
        module = Module(
            course_id=course.id,
            slug="intro",
            title="Introduction",
            sort_order=1,
            level="Core",
        )
        db.add(module)
        db.flush()
        first = Lesson(
            module_id=module.id,
            slug="introduction-to-html",
            title="Introduction to HTML",
            sort_order=1,
            estimated_minutes=10,
            is_published=False,
            content={
                "id": "html-lesson-001",
                "module_slug": "intro",
                "level": "beginner",
                "track": "core",
                "learning_outcomes": ["Explain HTML.", "Make a valid page."],
                "_codeleaf_course_slug": "html",
                "content": {
                    "intro": "A learner-safe intro.",
                    "content_blocks": [
                        {
                            "type": "diagram",
                            "title": "Overview",
                            "asset_path": "diagrams/module-01-overview.svg",
                            "alt_text": "Course diagram",
                            "caption": "Visual map",
                        },
                        {"type": "paragraph", "text": "Example"},
                    ],
                    "knowledge_check_file": "exams/question-files/lesson-001-questions.json",
                    "solution_notes": "Use the hint after the first attempt.",
                },
                "sources": [
                    {
                        "title": "HTML Living Standard",
                        "url": "https://html.spec.whatwg.org/",
                    }
                ],
            },
        )
        second = Lesson(
            module_id=module.id,
            slug="your-first-html-document",
            title="Your First HTML Document",
            sort_order=2,
            estimated_minutes=10,
            is_published=False,
            content={
                "id": "html-lesson-009",
                "module_slug": "intro",
                "level": "beginner",
                "track": "core",
                "learning_outcomes": ["Create a document.", "Check page structure."],
                "content": {"intro": "A second lesson.", "content_blocks": []},
                "sources": [],
            },
        )
        db.add_all([first, second])
        db.flush()
        exercise = Exercise(
            lesson_id=first.id,
            slug="html-choice-test",
            title="Choice test",
            exercise_type="choice",
            prompt="Choose yes.",
            starter={"options": ["yes", "no"]},
            public_tests=[],
            acceptance_criteria=["Choose yes"],
            hints=["Read the prompt."],
            solution={"answer": "yes"},
            grading_config={"mode": "choice", "correct_answer": "yes"},
            sequence=1,
            difficulty="easy",
            xp_points=20,
            is_published=False,
        )
        db.add(exercise)
        db.commit()
        user_id = user.id
        first_id = first.id
        second_id = second.id

    client = TestClient(app)
    readiness_response = client.get("/api/ready")
    require(
        readiness_response.status_code == 200
        and readiness_response.json().get("status") == "ready",
        "readiness endpoint verifies the database and required schema tables",
    )
    hidden = client.get("/api/courses/html/outline")
    require(
        hidden.status_code == 404,
        "draft/unpublished lessons are hidden from public outline by default",
    )

    settings.preview_draft_courses = True
    still_hidden = client.get("/api/courses/html/outline")
    require(
        still_hidden.status_code == 404,
        "draft preview remains disabled outside local development even when the flag is enabled",
    )

    # Explicit development opt-in should preview only manifest-tagged draft content.
    settings.app_env = "development"
    preview_outline = client.get("/api/courses/html/outline")
    require(
        preview_outline.status_code == 200
        and preview_outline.json().get("status") == "preview"
        and preview_outline.json().get("lesson_count") == 1
        and preview_outline.json()["modules"][0]["lessons"][0]["slug"]
        == "introduction-to-html",
        "opt-in local preview exposes only course-tagged draft lessons",
    )
    preview_lesson = client.get("/api/courses/html/lessons/introduction-to-html")
    require(
        preview_lesson.status_code == 200
        and "knowledge_check_file" not in preview_lesson.text
        and "reference_solution_file" not in preview_lesson.text,
        "local draft preview still withholds protected answer-key paths",
    )
    preview_exercises = client.get(
        "/api/courses/html/lessons/introduction-to-html/exercises"
    )
    require(
        preview_exercises.status_code == 200
        and preview_exercises.json().get("items")
        and "correct_answer" not in preview_exercises.text
        and "solution" not in preview_exercises.text,
        "local draft preview exposes learner-safe exercise prompts only",
    )
    preview_featured = client.get("/api/exercises/featured?limit=30")
    require(
        preview_featured.status_code == 200
        and preview_featured.json().get("preview_mode") is True
        and any(
            item.get("slug") == "html-choice-test"
            for item in preview_featured.json().get("items", [])
        )
        and "correct_answer" not in preview_featured.text
        and '"solution"' not in preview_featured.text,
        "featured exercise list includes imported drafts in local preview without grader answers",
    )
    settings.app_env = "test"
    settings.preview_draft_courses = False

    # Authentication is required for learner progress and exercise submissions.
    unauthenticated = client.post(
        "/api/me/progress/html/introduction-to-html", json={"timezone": "UTC"}
    )
    require(
        unauthenticated.status_code == 401, "progress endpoint requires authentication"
    )

    with SessionLocal() as db:
        db.get(Course, course.id).published = True
        db.get(Lesson, first_id).is_published = True
        db.get(Lesson, second_id).is_published = True
        db.query(Exercise).filter(Exercise.lesson_id == first_id).update(
            {Exercise.is_published: True}
        )
        db.commit()
    session_expires_at = utc_now() + timedelta(hours=1)
    with SessionLocal() as db:
        token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": int(session_expires_at.timestamp()),
            },
            settings.jwt_secret,
            algorithm=TOKEN_ALGORITHM,
        )
        # Auth now requires an active server-side session record as well as a valid JWT.
        db.add(AuthSession(token_hash=token_digest(token), user_id=user_id, expires_at=session_expires_at))
        db.commit()
    client.headers.update({"Authorization": f"Bearer {token}"})

    outline_response = client.get("/api/courses/html/outline")
    require(
        outline_response.status_code == 200
        and outline_response.json()["lesson_count"] == 2,
        "published outline returns only published lesson metadata",
    )
    lesson_response = client.get("/api/courses/html/lessons/introduction-to-html")
    lesson_body = lesson_response.json()
    require(
        lesson_response.status_code == 200
        and "knowledge_check_file" not in lesson_body["content"]
        and "answer_key" not in lesson_response.text
        and "reference_solution_file" not in lesson_response.text,
        "lesson API omits protected question paths and answer-key/reference-solution fields",
    )
    asset_response = client.get(
        "/api/courses/html/assets/diagrams/module-01-overview.svg"
    )
    require(
        asset_response.status_code == 200
        and "image/svg+xml" in asset_response.headers.get("content-type", ""),
        "asset endpoint serves an allowed SVG with the correct media type",
    )
    dynamic_diagram_response = client.get(
        "/api/courses/html/assets/diagrams/module-01-overview.diagram.json"
    )
    require(
        dynamic_diagram_response.status_code == 200
        and dynamic_diagram_response.json().get("renderer") == "codeleaf-native-dynamic-diagram"
        and len(dynamic_diagram_response.json().get("nodes", [])) == 2,
        "asset endpoint serves the dynamic diagram JSON model from the expected URL",
    )
    private_json_response = client.get("/api/courses/html/assets/diagrams/private-data.json")
    require(
        private_json_response.status_code == 404,
        "asset endpoint does not expose arbitrary JSON files inside the asset directory",
    )
    projects_response = client.get("/api/courses/html/projects")
    require(
        projects_response.status_code == 200
        and projects_response.json()["items"] == [],
        "draft project briefs are excluded from the public project API",
    )
    exercises_response = client.get(
        "/api/courses/html/lessons/introduction-to-html/exercises"
    )
    require(
        exercises_response.status_code == 200
        and "solution" not in exercises_response.text
        and "correct_answer" not in exercises_response.text,
        "public exercise listing omits reference solution and grader answer",
    )

    first_completion = client.post(
        "/api/me/progress/html/introduction-to-html", json={"timezone": "UTC"}
    )
    second_completion = client.post(
        "/api/me/progress/html/introduction-to-html", json={"timezone": "UTC"}
    )
    require(
        first_completion.status_code == 200
        and first_completion.json()["xp_awarded"] == 20,
        "first Free-plan lesson completion awards 20 XP",
    )
    require(
        second_completion.status_code == 200
        and second_completion.json()["xp_awarded"] == 0,
        "repeating lesson completion does not award duplicate XP",
    )

    with SessionLocal() as db:
        db.add(Entitlement(user_id=user_id, plan_id="max", status="active"))
        db.commit()
    boosted_completion = client.post(
        "/api/me/progress/html/your-first-html-document", json={"timezone": "UTC"}
    )
    require(
        boosted_completion.status_code == 200
        and boosted_completion.json()["base_xp"] == 20
        and boosted_completion.json()["xp_awarded"] == 30,
        "Max entitlement applies the server-side 1.5x lesson XP boost",
    )

    wrong = client.post(
        "/api/me/exercises/html/introduction-to-html/html-choice-test/submit",
        json={"answer": "no", "timezone": "UTC"},
    )
    correct = client.post(
        "/api/me/exercises/html/introduction-to-html/html-choice-test/submit",
        json={"answer": "yes", "timezone": "UTC"},
    )
    retry = client.post(
        "/api/me/exercises/html/introduction-to-html/html-choice-test/submit",
        json={"answer": "yes", "timezone": "UTC"},
    )
    require(
        wrong.status_code == 200
        and not wrong.json()["correct"]
        and wrong.json()["xp_awarded"] == 0,
        "incorrect exercise answer awards no XP",
    )
    require(
        correct.status_code == 200
        and correct.json()["correct"]
        and correct.json()["xp_awarded"] == 30,
        "correct exercise answer receives the server-side boosted reward",
    )
    require(
        retry.status_code == 200 and retry.json()["xp_awarded"] == 0,
        "repeated correct exercise submission cannot award XP twice",
    )

    with SessionLocal() as db:
        rewards = db.query(XPTransaction).filter(XPTransaction.user_id == user_id).all()
        require(
            len(rewards) == 3 and sum(row.awarded_points for row in rewards) == 80,
            "XP transaction table records exactly three unique rewards totaling 80 XP",
        )

    today = utc_now().date()
    streak = calculate_streaks(
        [today - timedelta(days=1), today, today - timedelta(days=4)], "UTC"
    )
    require(
        streak["current_streak"] == 2
        and streak["longest_streak"] == 2
        and streak["today_active"],
        "streak calculation counts consecutive qualifying days without bridging a gap",
    )

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    _TEMP_DIR.cleanup()
    print(
        "All API contract, reward idempotency, authorization, draft privacy, and streak checks passed."
    )


if __name__ == "__main__":
    main()
