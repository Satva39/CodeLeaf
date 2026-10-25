"""Integration checks for the Phase 2 exam, certificate and XP contracts.

Run from backend/: python scripts/test_phase2_exam_api.py
All rows/content are isolated in a temporary SQLite database and folder.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-phase2-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'phase2.db'}"
os.environ["JWT_SECRET"] = (
    "Phase2-test-only-secret-value-which-is-not-for-deployment-2026"
)
os.environ["APP_ENV"] = "development"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Response  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, func  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
import app.main as main_module  # noqa: E402
from app.auth_security import create_session  # noqa: E402
from app.models import (  # noqa: E402
    Certificate,
    Course,
    Entitlement,
    Exercise,
    ExerciseProgress,
    ExamAttempt,
    Lesson,
    LessonProgress,
    Module,
    User,
    XPTransaction,
)


def check(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)
    print(f"PASS {message}")


def write_course(root: Path, slug: str, capstone: bool) -> None:
    course_dir = root / slug
    exam_dir = course_dir / "exams"
    questions_dir = exam_dir / "question-files"
    questions_dir.mkdir(parents=True, exist_ok=True)
    question_files = []
    for number in range(1, 4):
        relative = f"question-files/lesson-{number:03d}-questions.json"
        question_files.append(relative)
        question_set = {
            "id": f"{slug}-lesson-{number:03d}",
            "lesson_id": f"{slug}-lesson-{number:03d}",
            "lesson_slug": f"lesson-{number:03d}",
            "status": "published",
            "questions": [
                {
                    "id": f"{slug}-q-{number:03d}",
                    "type": "single_choice",
                    "prompt": f"Question for lesson {number}?",
                    "options": [f"Correct {number}", f"Wrong {number}"],
                    "answer_key": f"Correct {number}",
                    "explanation": f"The test explanation for lesson {number}.",
                }
            ],
        }
        (questions_dir / f"lesson-{number:03d}-questions.json").write_text(
            json.dumps(question_set), encoding="utf-8"
        )
    blueprint = {
        "id": f"{slug}-exam",
        "title": f"{slug.upper()} Skills Assessment",
        "status": "published",
        "question_files": question_files,
        "project_submission": (
            "The capstone project is a human-reviewed requirement."
            if capstone
            else "No human-reviewed capstone is required."
        ),
        "recommended_settings": {"duration_minutes": 30, "suggested_pass_percent": 70},
        "topic_distribution": [
            {
                "topic": "Test fundamentals",
                "lesson_range": [1, 3],
                "weight_percent": 100,
            }
        ],
    }
    exam_dir.mkdir(parents=True, exist_ok=True)
    (exam_dir / "exam-blueprint.json").write_text(
        json.dumps(blueprint), encoding="utf-8"
    )
    manifest = {
        "course": {
            "slug": slug,
            "title": f"{slug.upper()} test course",
            "description": "temporary test course",
        },
        "status": "published",
        "assessment_files": ["exams/exam-blueprint.json"],
        "module_files": [],
        "project_files": [],
    }
    (course_dir / "course.json").write_text(json.dumps(manifest), encoding="utf-8")


def make_user(db, suffix: str) -> User:
    user = User(
        email=f"{suffix}@example.test",
        username=f"{suffix}",
        display_name=f"{suffix} learner",
        password_hash="test-only-hash",
        avatar={},
        theme="dark",
    )
    db.add(user)
    db.flush()
    return user


def set_cookie(client: TestClient, user: User) -> None:
    """Authenticate with a real persisted server session and its CSRF pair."""
    with SessionLocal() as db:
        persisted = db.get(User, user.id)
        if persisted is None:
            raise AssertionError("test user disappeared before session setup")
        persisted.is_email_verified = True
        response = Response()
        token = create_session(persisted, response, db)
        claims = main_module.jwt.decode(token, settings.jwt_secret, algorithms=[main_module.TOKEN_ALGORITHM])
        csrf_value = claims["csrf"]
    client.cookies.set(main_module.SESSION_COOKIE, token)
    client.cookies.set("codeleaf_csrf", csrf_value)
    client.headers.update({"origin": "http://localhost:5173", "x-csrf-token": csrf_value})


def answer_map(questions: list[dict], all_correct: bool = True) -> dict[str, str]:
    answers = {}
    for q in questions:
        options = q["options"]
        answers[q["id"]] = options[0] if all_correct else options[-1]
    return answers


def main() -> None:
    Base.metadata.create_all(bind=engine)
    content_root = Path(_TEMP_DIR.name) / "courses"
    write_course(content_root, "html", capstone=True)
    write_course(content_root, "css", capstone=False)
    old_root = main_module.COURSE_CONTENT_ROOT
    old_preview = settings.preview_draft_courses
    old_env = settings.app_env
    main_module.COURSE_CONTENT_ROOT = content_root
    settings.preview_draft_courses = False
    settings.app_env = "development"
    client: TestClient | None = None
    try:
        users: dict[str, User] = {}
        lesson_ids: dict[str, list[object]] = {}
        with SessionLocal() as db:
            for slug in ("html", "css"):
                course = Course(
                    slug=slug,
                    title=f"{slug.upper()} test course",
                    description="test",
                    category="Web",
                    level="Beginner",
                    published=True,
                    sort_order=1,
                )
                db.add(course)
                db.flush()
                module = Module(
                    course_id=course.id,
                    slug="core",
                    title="Core",
                    sort_order=1,
                    level="Core",
                )
                db.add(module)
                db.flush()
                ids = []
                for number in range(1, 4):
                    lesson = Lesson(
                        module_id=module.id,
                        slug=f"lesson-{number:03d}",
                        title=f"Lesson {number}",
                        sort_order=number,
                        estimated_minutes=5,
                        is_published=True,
                        content={
                            "id": f"{slug}-lesson-{number:03d}",
                            "_codeleaf_course_slug": slug,
                            "content": {},
                        },
                    )
                    db.add(lesson)
                    db.flush()
                    ids.append(lesson.id)
                lesson_ids[slug] = ids
            # This course must not be visible outside local draft preview.
            db.add(
                Course(
                    slug="draftcourse",
                    title="Draft course",
                    description="draft",
                    category="Web",
                    level="Beginner",
                    published=False,
                    sort_order=3,
                )
            )
            for suffix in [
                "html_learner",
                "css_learner",
                "failed_learner",
                "other_learner",
                "free",
                "pro",
                "max",
                "full_access",
            ]:
                users[suffix] = make_user(db, suffix)
            for plan in ("pro", "max", "full_access"):
                db.add(
                    Entitlement(user_id=users[plan].id, plan_id=plan, status="active")
                )
            # Eligible exam users have completed all required lessons. HTML still has a human-review gate.
            for suffix, slug in (("html_learner", "html"), ("css_learner", "css")):
                for lesson_id in lesson_ids[slug]:
                    db.add(
                        LessonProgress(
                            user_id=users[suffix].id,
                            lesson_id=lesson_id,
                            completed=True,
                            time_spent_seconds=1,
                        )
                    )
            # An exercise used to prove server XP rules and protected grader config.
            exercise = Exercise(
                lesson_id=lesson_ids["css"][0],
                slug="test-exercise",
                title="Test exercise",
                exercise_type="choice",
                prompt="Choose the safe answer",
                starter={},
                public_tests=[],
                acceptance_criteria=[],
                hints=[],
                solution={"private_test_note": "do-not-return"},
                grading_config={
                    "mode": "choice",
                    "correct_answer": "correct-private-value",
                },
                sequence=1,
                difficulty="easy",
                xp_points=20,
                is_published=True,
            )
            db.add(exercise)
            db.commit()
        client = TestClient(main_module.app)

        unauthenticated = client.post("/api/courses/css/exam/start", json={})
        check(
            unauthenticated.status_code == 401,
            "starting an exam requires authentication",
        )
        draft_hidden = client.get("/api/courses/draftcourse/exam")
        check(
            draft_hidden.status_code == 404,
            "draft course exam stays hidden when preview is disabled",
        )

        exam_catalog = client.get("/api/exams/catalog")
        check(exam_catalog.status_code == 200, "exam availability catalog responds successfully")
        catalog_items = {
            item["slug"]: item for item in exam_catalog.json().get("items", [])
        }
        check(
            catalog_items.get("html", {}).get("available") is True
            and catalog_items.get("css", {}).get("available") is True,
            "published exams appear as available in the certificates catalog",
        )
        check(
            catalog_items.get("ai", {}).get("available") is False,
            "courses without a published database record remain roadmap entries",
        )
        check(
            "answer_key" not in exam_catalog.text and "explanation" not in exam_catalog.text,
            "exam availability catalog never exposes private question-bank data",
        )

        # The HTML exam info and generated attempt must not disclose keys/explanations.
        set_cookie(client, users["html_learner"])
        info = client.get("/api/courses/html/exam")
        check(
            info.status_code == 200 and info.json()["question_count"] == 3,
            "published exam metadata is returned",
        )
        check(
            "answer_key" not in info.text and "explanation" not in info.text,
            "public exam metadata excludes answer keys and explanations",
        )
        started = client.post("/api/courses/html/exam/start", json={})
        start_payload = started.json()
        check(
            started.status_code == 201 and len(start_payload.get("questions", [])) == 3,
            "authenticated learner starts a server-stored exam attempt",
        )
        check(
            "answer_key" not in started.text and "explanation" not in started.text,
            "exam attempt response excludes answer keys and explanations",
        )
        attempt_id = start_payload["attempt_id"]

        # Ownership is enforced before the correct owner's attempt is submitted.
        set_cookie(client, users["other_learner"])
        foreign_attempt = client.get(f"/api/me/exams/{attempt_id}")
        check(
            foreign_attempt.status_code == 404,
            "exam attempts cannot be read by another learner",
        )
        set_cookie(client, users["html_learner"])
        in_progress = client.get(f"/api/me/exams/{attempt_id}")
        check(
            in_progress.status_code == 200 and "answer_key" not in in_progress.text,
            "owned in-progress attempt remains answer-key private",
        )
        invalid_option = client.post(
            f"/api/me/exams/{attempt_id}/submit",
            json={
                "answers": {
                    q["id"]: "not-an-option" for q in start_payload["questions"]
                }
            },
        )
        check(
            invalid_option.status_code == 422,
            "exam rejects answers outside the offered options",
        )
        unknown_id = client.post(
            f"/api/me/exams/{attempt_id}/submit",
            json={"answers": {"unknown": "Correct 1"}},
        )
        check(
            unknown_id.status_code == 422,
            "exam rejects unknown question IDs and missing answers",
        )
        submitted = client.post(
            f"/api/me/exams/{attempt_id}/submit",
            json={"answers": answer_map(start_payload["questions"])},
        )
        result = submitted.json()
        check(
            submitted.status_code == 200
            and result["passed"] is True
            and result["score_percent"] == 100,
            "exam is graded on the server and passing score is persisted",
        )
        check(
            result["certificate_status"] == "pending_capstone_review"
            and result["certificate"] is None,
            "HTML capstone human-review requirement blocks automatic certificate issuance",
        )
        repeated = client.post(
            f"/api/me/exams/{attempt_id}/submit",
            json={"answers": answer_map(start_payload["questions"])},
        )
        check(
            repeated.status_code == 409,
            "repeated exam submissions cannot re-grade the same attempt",
        )
        completed_attempt = client.get(f"/api/me/exams/{attempt_id}")
        check(
            completed_attempt.status_code == 200
            and completed_attempt.json()["status"] == "submitted"
            and "answer_key" not in completed_attempt.text,
            "submitted attempt read is private and does not return raw answer keys",
        )

        # CSS is a test course with no human-reviewed capstone; passing + completion issues a credential.
        set_cookie(client, users["css_learner"])
        css_started = client.post("/api/courses/css/exam/start", json={}).json()
        css_result_response = client.post(
            f"/api/me/exams/{css_started['attempt_id']}/submit",
            json={"answers": answer_map(css_started["questions"])},
        )
        css_result = css_result_response.json()
        check(
            css_result_response.status_code == 200
            and css_result["certificate_status"] == "issued"
            and css_result["certificate"],
            "eligible course issues a certificate only after server-verified pass and lesson completion",
        )
        verify = client.get(
            f"/api/certificates/verify/{css_result['certificate']['public_id']}"
        )
        check(
            verify.status_code == 200 and verify.json().get("valid") is True,
            "issued certificate public verification endpoint confirms credential",
        )
        own_certs = client.get("/api/me/certificates")
        check(
            own_certs.status_code == 200
            and any(
                item["public_id"] == css_result["certificate"]["public_id"]
                for item in own_certs.json().get("items", [])
            ),
            "learner certificate list reads persisted backend-issued credentials",
        )

        # Failed exam: never issues a certificate and repeated wrong answers cannot earn XP.
        set_cookie(client, users["failed_learner"])
        failed_start = client.post("/api/courses/css/exam/start", json={}).json()
        failed_response = client.post(
            f"/api/me/exams/{failed_start['attempt_id']}/submit",
            json={"answers": answer_map(failed_start["questions"], all_correct=False)},
        )
        failed = failed_response.json()
        check(
            failed_response.status_code == 200
            and failed["passed"] is False
            and failed["certificate"] is None,
            "failed exam does not issue a certificate",
        )
        check(
            failed["certificate_status"] == "exam_not_passed",
            "failed exam eligibility has truthful status",
        )

        # XP is server-computed: Free/Pro get 20, Max/Full Access get 30; lesson/exercise duplicates get 0.
        expected = {"free": 20, "pro": 20, "max": 30, "full_access": 30}
        for suffix, expected_xp in expected.items():
            set_cookie(client, users[suffix])
            first = client.post(
                "/api/me/progress/css/lesson-001",
                json={"time_spent_seconds": 1, "timezone": "UTC"},
            )
            second = client.post(
                "/api/me/progress/css/lesson-001",
                json={"time_spent_seconds": 1, "timezone": "UTC"},
            )
            check(
                first.status_code == 200 and first.json()["xp_awarded"] == expected_xp,
                f"{suffix} lesson XP matches server policy ({expected_xp})",
            )
            check(
                second.status_code == 200 and second.json()["xp_awarded"] == 0,
                f"{suffix} repeat lesson completion awards no duplicate XP",
            )
            wrong = client.post(
                "/api/me/exercises/css/lesson-001/test-exercise/submit",
                json={"answer": "wrong-private-value", "timezone": "UTC"},
            )
            right = client.post(
                "/api/me/exercises/css/lesson-001/test-exercise/submit",
                json={"answer": "correct-private-value", "timezone": "UTC"},
            )
            retry = client.post(
                "/api/me/exercises/css/lesson-001/test-exercise/submit",
                json={"answer": "correct-private-value", "timezone": "UTC"},
            )
            check(
                wrong.status_code == 200
                and not wrong.json()["correct"]
                and wrong.json()["xp_awarded"] == 0,
                f"{suffix} incorrect exercise answer awards no XP",
            )
            check(
                right.status_code == 200 and right.json()["xp_awarded"] == expected_xp,
                f"{suffix} correct exercise earns {expected_xp} XP once",
            )
            check(
                retry.status_code == 200 and retry.json()["xp_awarded"] == 0,
                f"{suffix} repeated correct exercise submission awards no extra XP",
            )

        # Authenticated read path must omit exercise answer key and private solution.
        set_cookie(client, users["free"])
        exercise_list = client.get("/api/courses/css/exercises")
        # The exercise index may be empty unless the authored lesson links it, but it must not leak the private answer.
        check(
            "correct-private-value" not in exercise_list.text
            and "do-not-return" not in exercise_list.text,
            "exercise listing never exposes grading keys or private solution content",
        )

        # Exam attempts alone do not create XP transactions.
        with SessionLocal() as db:
            html_xp = (
                db.scalar(
                    select(func.count(XPTransaction.id)).where(
                        XPTransaction.user_id == users["html_learner"].id
                    )
                )
                or 0
            )
            attempts = db.scalar(select(func.count(ExamAttempt.id))) or 0
            check(html_xp == 0, "exam submission by itself does not award activity XP")
            check(attempts == 3, "attempt records persist once per started exam")
            check(
                (db.scalar(select(func.count(Certificate.id))) or 0) == 1,
                "only fully eligible non-capstone test learner receives a certificate",
            )
    finally:
        try:
            if client is not None:
                client.close()
        finally:
            engine.dispose()
            main_module.COURSE_CONTENT_ROOT = old_root
            settings.preview_draft_courses = old_preview
            settings.app_env = old_env
    print("Phase 2 exam, certificate, and XP API tests completed.")


if __name__ == "__main__":
    main()
