"""Read-only scoped analytics summary integration test using temporary SQLite."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_security import require_user
from app.db import get_db
from app.models import Base, ProductAnalyticsEvent, User
from app.phase5_routes import router


class AnalyticsSummaryApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session() as db:
            self.editor = User(email=f"editor-{uuid4()}@example.invalid", display_name="Editor", password_hash="test", username=f"editor-{uuid4().hex[:12]}", role="admin")
            db.add(self.editor)
            db.flush()
            now = datetime.now(timezone.utc)
            for _ in range(6):
                db.add(ProductAnalyticsEvent(event_type="lesson_completion", course_slug="html", lesson_slug="intro", item_key="intro-example", outcome="success", occurred_at=now - timedelta(minutes=1)))
            db.commit()
        self.current_user = [self.editor]
        app = FastAPI()
        app.include_router(router)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[require_user] = lambda: self.current_user[0]
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_editor_summary_includes_item_key_and_privacy_note(self):
        response = self.client.get("/api/editor/analytics/summary?days=7")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["events_by_dimension"][0]["item_key"], "intro-example")
        self.assertEqual(payload["events_by_dimension"][0]["count"], 6)
        self.assertEqual(len(payload["daily_counts"]), 1)
        self.assertIn("no user ID", payload["privacy"])

    def test_learner_cannot_access_editor_summary(self):
        with self.Session() as db:
            learner = User(email=f"learner-{uuid4()}@example.invalid", display_name="Learner", password_hash="test", username=f"learner-{uuid4().hex[:12]}")
            db.add(learner); db.commit()
            self.current_user[0] = learner
        response = self.client.get("/api/editor/analytics/summary")
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
