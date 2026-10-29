"""Integration checks for subscription features added after the initial billing patch.

Run from backend/: python scripts/test_subscription_remaining_features.py
Uses an isolated SQLite database and mocked question-bank loader; no payments or AI calls.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

_TEMP = tempfile.TemporaryDirectory(prefix="codeleaf-subscription-remaining-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_TEMP.name) / 'remaining.db').as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "remaining-feature-tests-only-secret-never-deploy"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"
for key in ("AI_API_BASE_URL", "AI_API_KEY", "AI_MODEL"):
    os.environ.pop(key, None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Response  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.auth_security import create_session  # noqa: E402
from app.models import Course, Entitlement, MockAssessmentAttempt, User  # noqa: E402
from app.plan_entitlements import PLAN_DEFINITIONS  # noqa: E402
import app.main as main_module  # noqa: E402
import jwt  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def make_user(suffix: str, *, role: str = "learner") -> User:
    with SessionLocal() as db:
        user = User(
            email=f"{suffix}-{uuid4().hex[:8]}@example.invalid",
            username=f"{suffix}_{uuid4().hex[:10]}", display_name=f"{suffix} learner",
            password_hash="test-only-hash", is_email_verified=True, role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def authenticate(client: TestClient, user_id) -> None:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        response = Response()
        token = create_session(user, response, db)
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[main_module.TOKEN_ALGORITHM])
        csrf = claims["csrf"]
    client.cookies.clear()
    client.cookies.set(main_module.SESSION_COOKIE, token)
    client.cookies.set("codeleaf_csrf", csrf)
    client.headers.update({"origin": "http://localhost:5173", "x-csrf-token": csrf})


def grant(user_id, plan_id: str) -> None:
    with SessionLocal() as db:
        db.add(Entitlement(user_id=user_id, plan_id=plan_id, status="active", starts_at=datetime.now(timezone.utc) - timedelta(days=1), ends_at=None if plan_id == "full_access" else datetime.now(timezone.utc) + timedelta(days=30)))
        db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    client = TestClient(main_module.app)
    old_blueprint_loader = main_module._load_exam_blueprint
    old_question_loader = main_module._load_exam_question_pool
    old_content_root = main_module.COURSE_CONTENT_ROOT
    try:
        check([PLAN_DEFINITIONS[p]["limits"]["saved_snippets"] for p in ("free", "pro", "max", "full_access")] == [10, 100, 500, 1000], "saved snippet quotas are configurable for all four plans")
        free_user = make_user("remaining_free")
        authenticate(client, free_user.id)
        listing = client.get("/api/me/snippets")
        check(listing.status_code == 200 and listing.json()["usage"] == {"used": 0, "limit": 10, "storage_used_bytes": 0, "storage_limit_bytes": 1024 ** 3}, "snippet endpoint returns real account usage and Free allowance")
        saved = client.post("/api/me/snippets", json={"name": "Useful helper", "language": "javascript", "code": "const x = 1;"})
        check(saved.status_code == 201 and saved.json()["snippet"]["code"] == "const x = 1;", "learner can save an account-backed snippet")
        snippet_id = saved.json()["snippet"]["id"]
        duplicate = client.post("/api/me/snippets", json={"name": "useful HELPER", "language": "javascript", "code": "different"})
        check(duplicate.status_code == 409, "snippet names are case-insensitively unique within an account")
        updated = client.put(f"/api/me/snippets/{snippet_id}", json={"name": "Useful helper", "language": "javascript", "code": "const greeting = 'नमस्ते';"})
        check(updated.status_code == 200 and updated.json()["snippet"]["byte_size"] == len("const greeting = 'नमस्ते';".encode("utf-8")), "snippet update counts actual UTF-8 bytes")
        saved_count = client.get("/api/me/snippets").json()["usage"]["used"]
        storage_used = client.get("/api/me/snippets").json()["usage"]["storage_used_bytes"]
        check(saved_count == 1 and storage_used == len("const greeting = 'नमस्ते';".encode("utf-8")), "saved snippet bytes count toward the account storage quota")
        for index in range(9):
            extra = client.post("/api/me/snippets", json={"name": f"Helper {index}", "language": "javascript", "code": f"const helper{index} = true;"})
            check(extra.status_code == 201, f"Free account can save snippet {index + 2}")
        over_snippet_limit = client.post("/api/me/snippets", json={"name": "One too many", "language": "javascript", "code": "const tooMany = true;"})
        check(over_snippet_limit.status_code == 409 and over_snippet_limit.json()["detail"]["code"] == "SNIPPET_LIMIT_REACHED", "saved-snippet count is enforced server-side at the Free limit")
        foreign = make_user("remaining_foreign")
        client.cookies.clear()
        authenticate(client, foreign.id)
        check(client.get(f"/api/me/snippets").status_code == 200 and all(row["id"] != snippet_id for row in client.get("/api/me/snippets").json()["items"]), "saved snippets are private to their owner")
        check(client.delete(f"/api/me/snippets/{snippet_id}").status_code == 404, "another account cannot delete a private snippet")

        free_support_user = make_user("remaining_support_free")
        authenticate(client, free_support_user.id)
        ticket = client.post("/api/me/support-requests", json={"subject": "Cannot save my work", "category": "project", "message": "Please help me understand why saving is failing."})
        check(ticket.status_code == 201 and ticket.json()["request"]["priority"] == "standard", "Free support request is stored with standard queue priority")
        check(client.get("/api/leaderboard?period=week").status_code == 403, "Free cannot access the Pro-only leaderboard API directly")
        max_user = make_user("remaining_support_max")
        grant(max_user.id, "max")
        authenticate(client, max_user.id)
        priority_ticket = client.post("/api/me/support-requests", json={"subject": "Project upload issue", "category": "project", "message": "My project upload is not completing on the project page."})
        check(priority_ticket.status_code == 201 and priority_ticket.json()["request"]["priority"] == "priority", "verified Max plan receives priority support triage")
        support_admin = make_user("remaining_support_admin", role="support_admin")
        authenticate(client, support_admin.id)
        queue = client.get("/api/admin/support-requests?status_filter=open")
        check(queue.status_code == 200 and queue.json()["items"] and queue.json()["items"][0]["priority"] == "priority", "support queue orders priority requests ahead of standard requests")
        request_id = priority_ticket.json()["request"]["id"]
        replied = client.patch(f"/api/admin/support-requests/{request_id}", json={"status": "resolved", "staff_reply": "Please retry the upload after refreshing your workspace."})
        check(replied.status_code == 200 and replied.json()["request"]["staff_reply"], "authorized support staff can persist a resolution reply")

        # Project milestones persist for Pro+ and are explicitly denied to Free users.
        authenticate(client, free_user.id)
        denied_milestone = client.put("/api/me/project-milestones/html/todo-app/1", json={"completed": True})
        check(denied_milestone.status_code == 403, "Free cannot update plan-restricted project-planning checklist")
        pro_user = make_user("remaining_project_pro")
        grant(pro_user.id, "pro")
        authenticate(client, pro_user.id)
        check(client.get("/api/leaderboard?period=week").status_code == 200, "Pro can access the weekly leaderboard")
        milestone = client.put("/api/me/project-milestones/html/todo-app/1", json={"completed": True})
        check(milestone.status_code == 200 and milestone.json()["item"]["completed"], "Pro checklist completion is persisted server-side")
        check(client.get("/api/me/project-milestones?course_slug=html&project_slug=todo-app").json()["items"][0]["completed"] is True, "project checklist state survives a separate read")

        # Mock the published bank loader only; scoring and all user/plan paths remain real.
        course = Course(slug="mock-test-course", title="Mock Test Course", description="Test course", published=True)
        with SessionLocal() as db:
            db.add(course)
            db.commit()
            db.refresh(course)
        content_root = Path(_TEMP.name) / "content"
        course_dir = content_root / course.slug
        projects_dir = course_dir / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        capstone_doc = {"id": "capstone-1", "slug": "capstone-project", "title": "Capstone Project", "sequence": 1, "tier": "capstone", "status": "published", "objective": "Build and validate a capstone.", "milestones": []}
        standard_doc = {"id": "standard-1", "slug": "standard-project", "title": "Standard Project", "sequence": 2, "tier": "beginner", "status": "published", "objective": "Build a standard project.", "milestones": []}
        (course_dir / "course.json").write_text(json.dumps({"project_files": ["projects/capstone.json", "projects/standard.json"]}), encoding="utf-8")
        (projects_dir / "capstone.json").write_text(json.dumps(capstone_doc), encoding="utf-8")
        (projects_dir / "standard.json").write_text(json.dumps(standard_doc), encoding="utf-8")
        main_module.COURSE_CONTENT_ROOT = content_root
        authenticate(client, free_user.id)
        listed_projects = client.get("/api/courses/mock-test-course/projects")
        listed_by_slug = {item["slug"]: item for item in listed_projects.json()["items"]}
        check(listed_projects.status_code == 200 and listed_by_slug["capstone-project"]["is_locked"] is True and not listed_by_slug["standard-project"].get("is_locked", False), "existing capstone-tier project manifests are treated as Max-gated while standard projects remain visible")
        locked_guide = client.get("/api/courses/mock-test-course/projects/capstone-project")
        check(locked_guide.status_code == 403 and locked_guide.json()["detail"]["required_plan"] == "max", "direct capstone guide requests are enforced server-side")
        authenticate(client, max_user.id)
        unlocked_guide = client.get("/api/courses/mock-test-course/projects/capstone-project")
        check(unlocked_guide.status_code == 200, "verified Max entitlement unlocks capstone guide content")

        questions = []
        for index in range(20):
            correct = f"Correct option {index}"
            questions.append({"id": f"q{index}", "lesson_id": index + 1, "lesson_slug": "intro", "lesson_number": 1, "topic": "Basics" if index < 10 else "Practice", "prompt": f"Distinct mock question {index}?", "options": [correct, f"Wrong A {index}", f"Wrong B {index}", f"Wrong C {index}"], "answer_key": correct, "explanation": "Review the related lesson."})
        main_module._load_exam_blueprint = lambda course_slug, db: (course, Path(_TEMP.name), {"recommended_settings": {"suggested_pass_percent": 70}})
        main_module._load_exam_question_pool = lambda course_dir, blueprint: questions

        authenticate(client, free_user.id)
        free_info = client.get("/api/courses/mock-test-course/mock-exam")
        check(free_info.status_code == 200 and free_info.json()["available"] and not free_info.json()["can_start"], "mock practice is discoverable but gated for Free accounts")
        denied_start = client.post("/api/courses/mock-test-course/mock-exam/start", json={})
        check(denied_start.status_code == 403, "direct API call cannot start a premium mock as Free")

        authenticate(client, pro_user.id)
        started = client.post("/api/courses/mock-test-course/mock-exam/start", json={})
        check(started.status_code == 201 and len(started.json()["questions"]) == 20, "Pro can start a 20-question timed mock from the published bank")
        attempt_id = started.json()["attempt_id"]
        correct_answers = {q["id"]: next(opt for opt in q["options"] if opt.startswith("Correct option")) for q in started.json()["questions"][:10]}
        result = client.post(f"/api/me/mock-exams/{attempt_id}/submit", json={"answers": correct_answers})
        if result.status_code != 200 or "score_percent" not in result.json().get("report", {}):
            print("DEBUG mock submit:", result.status_code, result.text[:2000])
        check(result.status_code == 200 and result.json().get("report", {}).get("score_percent") == 50, "mock exam is graded on the server and returns topic performance")
        check("certificate" not in result.json() and "xp_awarded" not in result.json(), "mock result does not issue a certificate or XP reward")
        check(client.post(f"/api/me/mock-exams/{attempt_id}/submit", json={"answers": {}}).status_code == 409, "duplicate mock submission cannot be graded twice")
        authenticate(client, foreign.id)
        check(client.get(f"/api/me/mock-exams/{attempt_id}").status_code == 404, "mock attempts are private to their owner")

        # Server-side deadline check: moving the stored start time simulates an expired attempt.
        authenticate(client, pro_user.id)
        expired_start = client.post("/api/courses/mock-test-course/mock-exam/start", json={})
        expired_id = expired_start.json()["attempt_id"]
        with SessionLocal() as db:
            attempt = db.scalar(select(MockAssessmentAttempt).where(MockAssessmentAttempt.id == __import__("uuid").UUID(expired_id)))
            attempt.started_at = datetime.now(timezone.utc) - timedelta(minutes=25)
            db.commit()
        all_correct = {q["id"]: next(opt for opt in q["options"] if opt.startswith("Correct option")) for q in expired_start.json()["questions"]}
        expired_result = client.post(f"/api/me/mock-exams/{expired_id}/submit", json={"answers": all_correct})
        check(expired_result.status_code == 200 and expired_result.json()["report"]["timed_out"] and expired_result.json()["report"]["score_percent"] == 0, "expired mock submission receives no late-answer credit")

        print("Remaining subscription feature checks passed; isolated SQLite and mocked question bank only.")
    finally:
        main_module._load_exam_blueprint = old_blueprint_loader
        main_module._load_exam_question_pool = old_question_loader
        main_module.COURSE_CONTENT_ROOT = old_content_root
        client.close()
        engine.dispose()
        _TEMP.cleanup()


if __name__ == "__main__":
    main()
