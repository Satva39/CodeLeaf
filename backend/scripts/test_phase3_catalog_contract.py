"""Phase 3 catalog and course-scoping regression checks using temporary SQLite data.

Run from backend/: python scripts/test_phase3_catalog_contract.py
The test does not access the configured production database or real course manifests.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-phase3-catalog-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'phase3.db'}"
os.environ["JWT_SECRET"] = "phase3-test-only-secret-not-for-deployment"
os.environ["APP_ENV"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
import app.main as main_module  # noqa: E402
from app.main import TOKEN_ALGORITHM, utc_now  # noqa: E402
from app.auth_security import token_digest  # noqa: E402
from app.models import AuthSession, Course, Exercise, Lesson, Module, User  # noqa: E402


def check(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS {message}")


def write_course_content(content_root: Path, slug: str, title: str) -> None:
    course_dir = content_root / slug
    (course_dir / "references" / "entries").mkdir(parents=True, exist_ok=True)
    (course_dir / "projects").mkdir(parents=True, exist_ok=True)
    manifest = {
        "course": {
            "slug": slug,
            "title": title,
            "audience": [f"Learners studying {title}"],
            "prerequisites": ["Basic computer skills"],
            "learning_outcomes": [f"Apply {title} fundamentals"],
        },
        "status": "published",
        "reference_index": "references/reference-index.json",
        "project_files": ["projects/published-project.json", "projects/draft-project.json"],
    }
    (course_dir / "course.json").write_text(json.dumps(manifest), encoding="utf-8")
    index = {
        "id": f"{slug}-reference-index",
        "status": "published",
        "references": [
            "references/entries/published-reference.json",
            "references/entries/draft-reference.json",
        ],
    }
    (course_dir / "references" / "reference-index.json").write_text(json.dumps(index), encoding="utf-8")
    for state in ("published", "draft"):
        reference = {
            "id": f"{slug}-{state}-reference",
            "slug": f"{slug}-{state}-reference",
            "title": f"{title} {state.title()} Reference",
            "status": state,
            "url": f"https://example.invalid/{slug}/{state}",
            "publisher": "CodeLeaf test fixture",
        }
        (course_dir / "references" / "entries" / f"{state}-reference.json").write_text(
            json.dumps(reference), encoding="utf-8"
        )
        project = {
            "id": f"{slug}-{state}-project",
            "slug": f"{slug}-{state}-project",
            "title": f"{title} {state.title()} Project",
            "status": state,
            "objective": f"Build a test project for {title}.",
            "milestones": [],
            "starter_files": [],
        }
        (course_dir / "projects" / f"{state}-project.json").write_text(
            json.dumps(project), encoding="utf-8"
        )


def main() -> None:
    Base.metadata.create_all(bind=engine)
    content_root = Path(_TEMP_DIR.name) / "courses"
    write_course_content(content_root, "html", "HTML Test Course")
    write_course_content(content_root, "python", "Python Test Course")
    old_root = main_module.COURSE_CONTENT_ROOT
    old_preview = settings.preview_draft_courses
    old_env = settings.app_env
    main_module.COURSE_CONTENT_ROOT = content_root
    settings.preview_draft_courses = False
    settings.app_env = "test"
    client: TestClient | None = None
    try:
        user_id = None
        with SessionLocal() as db:
            user = User(
                email="phase3-catalog@example.invalid",
                display_name="Phase 3 Learner",
                password_hash="test-only-not-a-real-password-hash",
                username="phase3-catalog-test",
            )
            db.add(user)
            db.flush()
            user_id = user.id
            for order, slug, title in (
                (1, "html", "HTML Test Course"),
                (2, "python", "Python Test Course"),
            ):
                course = Course(
                    slug=slug,
                    title=title,
                    description=f"Published description for {title}.",
                    category="Test Technology",
                    level="Beginner",
                    published=True,
                    sort_order=order,
                )
                db.add(course)
                db.flush()
                module = Module(
                    course_id=course.id,
                    slug=f"{slug}-intro",
                    title=f"{title} Introduction",
                    sort_order=1,
                    level="Core",
                )
                db.add(module)
                db.flush()
                lesson = Lesson(
                    module_id=module.id,
                    slug=f"{slug}-lesson",
                    title=f"{title} Lesson",
                    sort_order=1,
                    estimated_minutes=15,
                    is_published=True,
                    content={"_codeleaf_course_slug": slug},
                )
                draft_lesson = Lesson(
                    module_id=module.id,
                    slug=f"{slug}-draft-lesson",
                    title=f"{title} Draft Lesson",
                    sort_order=2,
                    estimated_minutes=99,
                    is_published=False,
                    content={"_codeleaf_course_slug": slug},
                )
                db.add_all([lesson, draft_lesson])
                db.flush()
                db.add_all([
                    Exercise(
                        lesson_id=lesson.id,
                        slug=f"{slug}-exercise",
                        title=f"{title} Exercise",
                        exercise_type="coding",
                        prompt=f"Practice {title}.",
                        starter={"language": slug, "code": "# code challenge starter"},
                        is_published=True,
                        sequence=1,
                    ),
                    Exercise(
                        lesson_id=lesson.id,
                        slug=f"{slug}-short-answer",
                        title=f"{title} Short Answer (must be hidden)",
                        exercise_type="short_answer",
                        prompt="Write a short paragraph about this topic.",
                        starter={"response_template": "Answer:"},
                        is_published=True,
                        sequence=2,
                    ),
                    Exercise(
                        lesson_id=lesson.id,
                        slug=f"{slug}-draft-exercise",
                        title=f"{title} Draft Exercise",
                        exercise_type="short_answer",
                        prompt="Unpublished exercise fixture.",
                        is_published=False,
                        sequence=2,
                    ),
                ])
            db.commit()

        client = TestClient(main_module.app)
        catalog_response = client.get("/api/courses")
        check(catalog_response.status_code == 200, "public catalog endpoint responds successfully")
        catalog = {item["slug"]: item for item in catalog_response.json()["items"]}
        for slug in ("html", "python"):
            row = catalog[slug]
            check(row["status"] == "published" and row["lesson_count"] == 1, f"{slug} status and lesson count use published database records")
            check(row["module_count"] == 1 and row["estimated_minutes"] == 15, f"{slug} module/time counts exclude unpublished lessons")
            check(row["reference_count"] == 1 and row["project_count"] == 1, f"{slug} reference/project counts include only published manifest entries")
            check(row["practice_count"] == 1, f"{slug} practice count includes only MCQs and code challenges")
            check(row["audience"] == [f"Learners studying {row['title']}"] and row["learning_outcomes"], f"{slug} catalog details retain authored learning metadata")

        html_refs = client.get("/api/courses/html/references")
        python_refs = client.get("/api/courses/python/references")
        check(html_refs.status_code == 200 and [x["slug"] for x in html_refs.json()["items"]] == ["html-published-reference"], "HTML references contain only HTML published entries")
        check(python_refs.status_code == 200 and [x["slug"] for x in python_refs.json()["items"]] == ["python-published-reference"], "Python references contain only Python published entries")

        html_projects = client.get("/api/courses/html/projects")
        python_projects = client.get("/api/courses/python/projects")
        check(html_projects.status_code == 200 and [x["slug"] for x in html_projects.json()["items"]] == ["html-published-project"], "HTML projects contain only HTML published guides")
        check(python_projects.status_code == 200 and [x["slug"] for x in python_projects.json()["items"]] == ["python-published-project"], "Python projects contain only Python published guides")

        html_practice = client.get("/api/courses/html/exercises?limit=100")
        python_practice = client.get("/api/courses/python/exercises?limit=100")
        check(html_practice.status_code == 200 and [x["slug"] for x in html_practice.json()["items"]] == ["html-exercise"], "HTML practice contains only published code challenges and excludes short answers")
        check(python_practice.status_code == 200 and [x["slug"] for x in python_practice.json()["items"]] == ["python-exercise"], "Python practice contains only published code challenges and excludes short answers")
        check("Draft" not in html_refs.text + html_projects.text + html_practice.text, "unpublished reference/project/practice fixtures stay hidden")

        unauthenticated_bookmarks = client.get("/api/me/bookmarks")
        check(unauthenticated_bookmarks.status_code == 401, "signed-out bookmark requests stay protected")
        session_expires_at = utc_now() + timedelta(hours=1)
        token = jwt.encode(
            {"sub": str(user_id), "exp": int(session_expires_at.timestamp())},
            settings.jwt_secret,
            algorithm=TOKEN_ALGORITHM,
        )
        # Auth now requires an active server-side session record as well as a valid JWT.
        with SessionLocal() as db:
            db.add(AuthSession(token_hash=token_digest(token), user_id=user_id, expires_at=session_expires_at))
            db.commit()
        client.headers.update({"Authorization": f"Bearer {token}"})
        created = client.put("/api/me/bookmarks/html/html-lesson")
        repeated = client.put("/api/me/bookmarks/html/html-lesson")
        saved = client.get("/api/me/bookmarks")
        saved_items = saved.json().get("items", [])
        check(created.status_code == 200 and repeated.status_code == 200, "authenticated bookmark add is repeat-safe")
        check(len(saved_items) == 1 and saved_items[0]["title"] == "HTML Test Course Lesson", "account bookmarks reload from server records with authoritative lesson titles")
        removed = client.delete("/api/me/bookmarks/html/html-lesson")
        check(removed.status_code == 200 and client.get("/api/me/bookmarks").json().get("items", []) == [], "account bookmark removal persists across subsequent reads")
    finally:
        if client is not None:
            client.close()
        engine.dispose()
        main_module.COURSE_CONTENT_ROOT = old_root
        settings.preview_draft_courses = old_preview
        settings.app_env = old_env
    print("Phase 3 catalog and course-scoping checks completed.")


if __name__ == "__main__":
    main()
