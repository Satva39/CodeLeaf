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
    for file_number in range(1, 5):
        relative = f"question-files/lesson-{file_number:03d}-questions.json"
        question_files.append(relative)
        rows = []
        for local_index in range(1, 21):
            number = (file_number - 1) * 20 + local_index
            correct = f"{slug.upper()} correct answer {number}"
            rows.append({
                "id": f"{slug}-q-{number:03d}",
                "type": "single_choice",
                "prompt": f"{slug.upper()} test question {number}: which choice is correct?",
                "options": [
                    correct,
                    f"{slug.upper()} distractor A {number}",
                    f"{slug.upper()} distractor B {number}",
                    f"{slug.upper()} distractor C {number}",
                ],
                "answer_key": correct,
                "explanation": f"The test explanation for question {number}.",
                "lesson_id": f"{slug}-lesson-{file_number:03d}",
                "lesson_slug": f"lesson-{file_number:03d}",
            })
        question_set = {
            "id": f"{slug}-lesson-{file_number:03d}",
            "lesson_id": f"{slug}-lesson-{file_number:03d}",
            "lesson_slug": f"lesson-{file_number:03d}",
            "title": f"{slug.upper()} question set {file_number}",
            "status": "published",
            "questions": rows,
        }
        (questions_dir / f"lesson-{file_number:03d}-questions.json").write_text(
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
            {"topic": "Test fundamentals", "lesson_range": [1, 4], "weight_percent": 100}
        ],
    }
    exam_dir.mkdir(parents=True, exist_ok=True)
    (exam_dir / "exam-blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
    practical = {
        "id": f"{slug}-practical",
        "title": f"{slug.upper()} Intermediate Practical Assessment",
        "status": "published",
        "difficulty": "intermediate",
        "pass_percent": 70,
        "tasks": [{
            "id": "task-safe-response",
            "title": "Validate the expected response",
            "prompt": "Enter the exact course-specific validation token shown in this test fixture.",
            "submission_type": "text",
            "starter": "",
            "rubric": ["Return the expected token exactly."],
            "points": 100,
            "grader": {"type": "exact_text", "expected": f"{slug}_safe_response"},
        }],
    }
    (exam_dir / "practical-exam.json").write_text(json.dumps(practical), encoding="utf-8")
    manifest = {
        "course": {
            "slug": slug,
            "title": f"{slug.upper()} test course",
            "description": "temporary test course",
        },
        "status": "published",
        "assessment_files": ["exams/exam-blueprint.json", "exams/practical-exam.json"],
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


def answer_map(questions: list[dict], attempt_id: str, all_correct: bool = True) -> dict[str, str]:
    """Read private answer keys only in the isolated test DB to test server grading."""
    from uuid import UUID
    with SessionLocal() as db:
        attempt = db.get(ExamAttempt, UUID(attempt_id))
        if attempt is None:
            raise AssertionError("test attempt was not persisted")
        stored = {
            item["id"]: item
            for item in (attempt.answers_summary or {}).get("questions", [])
            if isinstance(item, dict) and item.get("id")
        }
    answers = {}
    for question in questions:
        full = stored[question["id"]]
        options = question["options"]
        correct = full["answer_key"]
        answers[question["id"]] = correct if all_correct else next(option for option in options if option != correct)
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
                "practical_failed_learner",
                "blocked_learner",
                "exercise_blocked_learner",
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
            # Users intended to start CSS exams have completed its required lessons.
            for suffix, slug in (
                ("html_learner", "html"),
                ("css_learner", "css"),
                ("failed_learner", "css"),
                ("practical_failed_learner", "css"),
                ("exercise_blocked_learner", "css"),
            ):
                for lesson_id in lesson_ids[slug]:
                    db.add(LessonProgress(user_id=users[suffix].id, lesson_id=lesson_id, completed=True, time_spent_seconds=1))
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
            db.flush()
            # The two learners who may take CSS exams have completed its only published exercise.
            for suffix in ("css_learner", "failed_learner", "practical_failed_learner"):
                db.add(ExerciseProgress(user_id=users[suffix].id, exercise_id=exercise.id, completed=True, attempts=1))
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

        # Learner progress must still be returned when an assessment stage is unavailable.
        set_cookie(client, users["blocked_learner"])
        blocked_progress_response = client.get("/api/me/certificate-eligibility")
        blocked_progress = {
            item["course_slug"]: item
            for item in blocked_progress_response.json().get("items", [])
        }
        check(
            blocked_progress_response.status_code == 200
            and blocked_progress.get("html", {}).get("total_lessons") == 3
            and blocked_progress.get("html", {}).get("lessons_complete") is False,
            "certificate eligibility returns lesson progress for incomplete learners",
        )
        set_cookie(client, users["exercise_blocked_learner"])
        exercise_progress_response = client.get("/api/me/certificate-eligibility")
        exercise_progress = {
            item["course_slug"]: item
            for item in exercise_progress_response.json().get("items", [])
        }
        check(
            exercise_progress_response.status_code == 200
            and exercise_progress.get("css", {}).get("lessons_complete") is True
            and exercise_progress.get("css", {}).get("exercises_complete") is False,
            "certificate eligibility separately identifies incomplete exercises",
        )

        # Simulate a missing practical assessment: progress remains available and exam
        # start stays blocked, rather than the frontend falling back to a generic roadmap.
        practical_path = content_root / "html" / "exams" / "practical-exam.json"
        practical_contents = practical_path.read_text(encoding="utf-8")
        try:
            practical_path.unlink()
            set_cookie(client, users["html_learner"])
            missing_practical_response = client.get("/api/me/certificate-eligibility")
            missing_practical_items = {
                item["course_slug"]: item
                for item in missing_practical_response.json().get("items", [])
            }
            html_missing_practical = missing_practical_items.get("html", {})
            check(
                missing_practical_response.status_code == 200
                and html_missing_practical.get("total_lessons") == 3
                and html_missing_practical.get("lessons_complete") is True
                and html_missing_practical.get("practical_exam_available") is False
                and html_missing_practical.get("start_exam_available") is False,
                "missing practical assessment does not hide progress and still blocks exam start",
            )
        finally:
            practical_path.write_text(practical_contents, encoding="utf-8")

        # The backend rejects direct API starts unless all published lessons and exercises are complete.
        set_cookie(client, users["blocked_learner"])
        blocked_start = client.post("/api/courses/html/exam/start", json={})
        check(
            blocked_start.status_code == 409
            and blocked_start.json().get("detail", {}).get("code") == "exam_prerequisites_incomplete",
            "exam start is blocked by server when required lesson progress is incomplete",
        )
        set_cookie(client, users["exercise_blocked_learner"])
        exercise_blocked = client.post("/api/courses/css/exam/start", json={})
        check(
            exercise_blocked.status_code == 409
            and "exercises" in exercise_blocked.json().get("detail", {}).get("missing_requirements", {}),
            "exam start is blocked by server when required exercise progress is incomplete",
        )
        with SessionLocal() as db:
            db.add(ExerciseProgress(user_id=users["exercise_blocked_learner"].id, exercise_id=exercise.id, completed=True, attempts=1))
            db.commit()
        changed_progress_start = client.post("/api/courses/css/exam/start", json={})
        changed_progress_attempt = changed_progress_start.json()
        check(changed_progress_start.status_code == 201, "eligible learner can start an MCQ attempt before progress changes")
        changed_progress_answers = answer_map(changed_progress_attempt["questions"], changed_progress_attempt["attempt_id"])
        with SessionLocal() as db:
            progress_row = db.scalar(select(ExerciseProgress).where(
                ExerciseProgress.user_id == users["exercise_blocked_learner"].id,
                ExerciseProgress.exercise_id == exercise.id,
            ))
            db.delete(progress_row)
            db.commit()
        active_attempt_read = client.get(f"/api/me/exams/{changed_progress_attempt['attempt_id']}")
        check(active_attempt_read.status_code == 409, "active exam attempt access rechecks current prerequisite progress")
        changed_progress_submit = client.post(
            f"/api/me/exams/{changed_progress_attempt['attempt_id']}/submit",
            json={"answers": changed_progress_answers},
        )
        check(
            changed_progress_submit.status_code == 409
            and changed_progress_submit.json().get("detail", {}).get("code") == "exam_prerequisites_incomplete",
            "MCQ submission rechecks course prerequisites on the server",
        )

        # The HTML exam info and generated attempt must not disclose keys/explanations.
        set_cookie(client, users["html_learner"])
        info = client.get("/api/courses/html/exam")
        check(
            info.status_code == 200 and info.json()["question_count"] == 80,
            "published exam metadata is returned",
        )
        check(
            "answer_key" not in info.text and "explanation" not in info.text,
            "public exam metadata excludes answer keys and explanations",
        )
        started = client.post("/api/courses/html/exam/start", json={})
        start_payload = started.json()
        check(
            started.status_code == 201 and len(start_payload.get("questions", [])) == 80,
            "authenticated learner starts a server-stored exam attempt",
        )
        check(
            "answer_key" not in started.text and "explanation" not in started.text,
            "exam attempt response excludes answer keys and explanations",
        )
        attempt_id = start_payload["attempt_id"]
        from uuid import UUID
        with SessionLocal() as db:
            private_attempt = db.get(ExamAttempt, UUID(attempt_id))
            private_questions = (private_attempt.answers_summary or {}).get("questions", [])
            answer_positions = [q["options"].index(q["answer_key"]) for q in private_questions]
            check(
                len(private_questions) == 80 and len(set(answer_positions)) >= 3,
                "per-attempt option shuffle preserves answer identity and varies correct positions",
            )

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
        html_answers = answer_map(start_payload["questions"], start_payload["attempt_id"])
        submitted = client.post(
            f"/api/me/exams/{attempt_id}/submit",
            json={"answers": html_answers},
        )
        result = submitted.json()
        check(
            submitted.status_code == 200
            and result["passed"] is True
            and result["score_percent"] == 100,
            "exam is graded on the server and passing score is persisted",
        )
        check(
            result["certificate_status"] == "practical_exam_required"
            and result["certificate"] is None,
            "passing the MCQ stage unlocks the practical instead of issuing a certificate or requiring project review",
        )
        repeated = client.post(
            f"/api/me/exams/{attempt_id}/submit",
            json={"answers": html_answers},
        )
        check(
            repeated.status_code == 409,
            "repeated exam submissions cannot re-grade the same attempt",
        )
        # Passing MCQ unlocks the mandatory practical, and only a successful practical can issue a certificate.
        html_practical_start = client.post("/api/courses/html/practical-exam/start", json={})
        html_practical_payload = html_practical_start.json()
        check(
            html_practical_start.status_code == 201 and len(html_practical_payload.get("tasks", [])) == 1,
            "passed MCQ attempt unlocks the practical assessment",
        )
        html_practical_submit = client.post(
            f"/api/me/practical-exams/{html_practical_payload['attempt_id']}/submit",
            json={"answers": {"task-safe-response": "html_safe_response"}},
        )
        html_practical_result = html_practical_submit.json()
        check(
            html_practical_submit.status_code == 200 and html_practical_result["passed"] is True
            and html_practical_result["certificate"] is not None,
            "certificate is issued only after all prerequisites, MCQ pass, and practical pass",
        )
        html_practical_repeat = client.post(
            f"/api/me/practical-exams/{html_practical_payload['attempt_id']}/submit",
            json={"answers": {"task-safe-response": "html_safe_response"}},
        )
        check(html_practical_repeat.status_code == 409, "replayed practical submission cannot create another certificate")

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
            json={"answers": answer_map(css_started["questions"], css_started["attempt_id"])},
        )
        css_result = css_result_response.json()
        check(
            css_result_response.status_code == 200
            and css_result["certificate_status"] == "practical_exam_required"
            and css_result["certificate"] is None,
            "passing CSS MCQ does not issue a certificate without a practical pass",
        )
        css_practical_started = client.post("/api/courses/css/practical-exam/start", json={})
        css_practical = css_practical_started.json()
        css_practical_result_response = client.post(
            f"/api/me/practical-exams/{css_practical['attempt_id']}/submit",
            json={"answers": {"task-safe-response": "css_safe_response"}},
        )
        css_practical_result = css_practical_result_response.json()
        check(
            css_practical_started.status_code == 201 and css_practical_result_response.status_code == 200
            and css_practical_result["passed"] is True and css_practical_result["certificate"] is not None,
            "CSS certificate is issued after both exam stages pass",
        )
        verify = client.get(
            f"/api/certificates/verify/{css_practical_result['certificate']['public_id']}"
        )
        check(
            verify.status_code == 200 and verify.json().get("valid") is True,
            "issued certificate public verification endpoint confirms credential",
        )
        own_certs = client.get("/api/me/certificates")
        check(
            own_certs.status_code == 200
            and any(
                item["public_id"] == css_practical_result["certificate"]["public_id"]
                for item in own_certs.json().get("items", [])
            ),
            "learner certificate list reads persisted backend-issued credentials",
        )

        # Failed exam: never issues a certificate and repeated wrong answers cannot earn XP.
        set_cookie(client, users["failed_learner"])
        failed_start = client.post("/api/courses/css/exam/start", json={}).json()
        failed_response = client.post(
            f"/api/me/exams/{failed_start['attempt_id']}/submit",
            json={"answers": answer_map(failed_start["questions"], failed_start["attempt_id"], all_correct=False)},
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

        # An MCQ pass followed by a failed practical still cannot issue a certificate.
        set_cookie(client, users["practical_failed_learner"])
        practical_failed_mcq = client.post("/api/courses/css/exam/start", json={}).json()
        practical_failed_mcq_result = client.post(
            f"/api/me/exams/{practical_failed_mcq['attempt_id']}/submit",
            json={"answers": answer_map(practical_failed_mcq["questions"], practical_failed_mcq["attempt_id"])},
        ).json()
        practical_failed_start = client.post("/api/courses/css/practical-exam/start", json={}).json()
        practical_failed_response = client.post(
            f"/api/me/practical-exams/{practical_failed_start['attempt_id']}/submit",
            json={"answers": {"task-safe-response": "not-the-expected-answer"}},
        )
        practical_failed = practical_failed_response.json()
        check(
            practical_failed_response.status_code == 200 and practical_failed["passed"] is False
            and practical_failed["certificate"] is None,
            "failed practical exam does not issue a certificate",
        )
        set_cookie(client, users["failed_learner"])
        no_mcq_practical = client.get("/api/courses/css/practical-exam")
        check(
            no_mcq_practical.status_code == 403,
            "practical assessment cannot be accessed without a passed MCQ attempt",
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

        # The exercise completion readback is server-persisted and scoped to the authenticated learner.
        set_cookie(client, users["free"])
        own_progress = client.get("/api/me/courses/css/exercise-progress")
        check(
            own_progress.status_code == 200
            and any(item["exercise_slug"] == "test-exercise" and item["completed"] for item in own_progress.json().get("items", [])),
            "successful exercise progress is visible from the server after submission",
        )
        set_cookie(client, users["other_learner"])
        foreign_progress = client.get("/api/me/courses/css/exercise-progress")
        check(
            foreign_progress.status_code == 200
            and all(not item["completed"] for item in foreign_progress.json().get("items", [])),
            "exercise completion is isolated per learner",
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
            check(attempts == 5, "attempt records persist once per started MCQ exam, including a prerequisite-change attempt")
            check(
                (db.scalar(select(func.count(Certificate.id))) or 0) == 2,
                "only learners who pass both exam stages receive certificates; project review is not a gate",
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
