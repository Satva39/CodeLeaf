"""Isolated SQLite integration test for review queue ownership and review ratings.

Run from backend/: python scripts/test_review_queue_api.py
This uses an in-memory database and never contacts Neon or the configured database.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_security import require_user
from app.db import get_db
from app.models import Base, Course, Lesson, Module, ReviewSchedule, User
from app.phase5_routes import router


class ReviewQueueApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session() as db:
            self.user = User(email="review-api@example.com", display_name="Review Test", password_hash="hash", username="reviewapitest")
            self.other_user = User(email="review-other@example.com", display_name="Other Test", password_hash="hash", username="reviewother")
            course = Course(slug="html", title="HTML", description="", category="Web", level="Beginner", published=True)
            db.add_all([self.user, self.other_user, course]); db.flush()
            module = Module(course_id=course.id, slug="intro", title="Introduction", sort_order=1, level="Core")
            db.add(module); db.flush()
            lesson = Lesson(module_id=module.id, slug="intro-html", title="Introduction to HTML", content={}, sort_order=1, estimated_minutes=5, is_published=True)
            db.add(lesson); db.flush()
            schedule = ReviewSchedule(
                user_id=self.user.id, course_slug="html", item_type="lesson", item_slug="intro-html",
                interval_days=1, ease_factor=2.3, repetitions=1, last_result="correct",
                due_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
            db.add(schedule); db.commit()
            self.user_id, self.other_user_id, self.review_id = self.user.id, self.other_user.id, schedule.id
        self.current_user = [self.user]
        self.app = FastAPI()
        self.app.include_router(router)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[get_db] = override_db
        self.app.dependency_overrides[require_user] = lambda: self.current_user[0]
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_queue_contains_due_published_items_and_preferences(self):
        response = self.client.get("/api/me/reviews")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(len(payload["due"]), 1)
        self.assertEqual(payload["due"][0]["title"], "Introduction to HTML")
        self.assertEqual(payload["due"][0]["lesson_slug"], "intro-html")
        self.assertEqual(payload["preferences"]["daily_review_limit"], 10)

    def test_self_rating_reschedules_without_xp_or_mastery_claim(self):
        response = self.client.post(f"/api/me/reviews/{self.review_id}/rate", json={
            "rating": "good", "course_slug": "html", "lesson_slug": "intro-html",
            "item_type": "lesson", "item_slug": "intro-html",
        })
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["xp_awarded"], 0)
        self.assertFalse(payload["mastery_inferred"])
        self.assertEqual(payload["review"]["interval_days"], 2)
        self.assertEqual(payload["review"]["last_result"], "good")

    def test_rating_cannot_target_another_lesson(self):
        response = self.client.post(f"/api/me/reviews/{self.review_id}/rate", json={
            "rating": "easy", "course_slug": "html", "lesson_slug": "different-lesson",
            "item_type": "lesson", "item_slug": "intro-html",
        })
        self.assertEqual(response.status_code, 400)

    def test_review_item_is_account_scoped(self):
        self.current_user[0] = self.other_user
        response = self.client.post(f"/api/me/reviews/{self.review_id}/rate", json={
            "rating": "easy", "course_slug": "html", "lesson_slug": "intro-html",
            "item_type": "lesson", "item_slug": "intro-html",
        })
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
