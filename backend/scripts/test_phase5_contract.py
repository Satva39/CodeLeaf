"""Focused Phase 5 service tests using an isolated in-memory SQLite database.
Run from backend/: python scripts/test_phase5_contract.py
"""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.db import Base
from app.models import ProductAnalyticsEvent, ReviewSchedule, User
from app.phase5_routes import ContentRevisionInput, PortfolioSubmissionInput, _validate_content, get_learning_roadmaps
from app.phase5_service import record_review_result
from app.models import ContentRevision

class Phase5ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.db = Session(bind=self.connection, expire_on_commit=False)
        self.user = User(email=f"learner-{uuid4()}@example.invalid", display_name="Learner", password_hash="test-only", username=f"learner-{uuid4().hex[:12]}")
        self.db.add(self.user)
        self.db.flush()

    def tearDown(self):
        self.db.close()
        self.transaction.rollback()
        self.connection.close()

    def test_review_schedule_uses_server_recorded_result_and_bounded_interval(self):
        row = record_review_result(self.db, self.user.id, "html", "exercise", "html-basics", True)
        self.assertEqual(row.last_result, "correct")
        self.assertEqual(row.repetitions, 1)
        self.assertGreaterEqual(row.interval_days, 1)
        same = record_review_result(self.db, self.user.id, "html", "exercise", "html-basics", True)
        self.assertEqual(same.id, row.id)
        self.assertEqual(same.repetitions, 2)
        reset = record_review_result(self.db, self.user.id, "html", "exercise", "html-basics", False)
        self.assertEqual(reset.repetitions, 0)
        self.assertEqual(reset.interval_days, 1)
        self.assertEqual(reset.last_result, "incorrect")

    def test_portfolio_rejects_path_traversal_and_unknown_fields(self):
        with self.assertRaises(ValidationError):
            PortfolioSubmissionInput(course_slug="html", project_slug="demo", code_bundle={"../secret.txt": "no"})
        with self.assertRaises(ValidationError):
            PortfolioSubmissionInput(course_slug="html", project_slug="demo", role="admin")

    def test_editor_revision_payload_rejects_self_assigned_role(self):
        with self.assertRaises(ValidationError):
            ContentRevisionInput(course_slug="html", content_type="lesson", content_slug="lesson-one", content_json={"title": "Lesson"}, role="admin")

    def test_analytics_schema_has_no_user_id_email_ip_or_raw_payload(self):
        columns = set(ProductAnalyticsEvent.__table__.columns.keys())
        self.assertFalse({"user_id", "email", "ip_address", "payload", "answer", "submitted_code"} & columns)

    def test_editor_validation_flags_missing_identity(self):
        revision = ContentRevision(course_slug="html", content_type="lesson", content_slug="lesson-one", version=1,
            content_json={"body": "content"}, created_by=self.user.id)
        result = _validate_content(revision)
        self.assertFalse(result["valid"])
        self.assertTrue(any("identity" in error.lower() for error in result["errors"]))

    def test_staged_diagram_uses_full_native_text_mapping_validator(self):
        fixture_path = BACKEND_ROOT / "tests" / "fixtures" / "diagrams" / "branching.diagram.json"
        model = json.loads(fixture_path.read_text(encoding="utf-8"))
        valid_revision = ContentRevision(course_slug="html", content_type="diagram", content_slug="branching",
            version=1, content_json=model, created_by=self.user.id)
        valid_report = _validate_content(valid_revision)
        self.assertTrue(valid_report["valid"], valid_report["errors"])

        invalid_model = json.loads(json.dumps(model))
        invalid_model["nodes"][0]["sourceTextIndices"] = []
        invalid_revision = ContentRevision(course_slug="html", content_type="diagram", content_slug="branching",
            version=2, content_json=invalid_model, created_by=self.user.id)
        invalid_report = _validate_content(invalid_revision)
        self.assertFalse(invalid_report["valid"])
        self.assertTrue(any("diagram" in error.lower() or "text" in error.lower() or "mapping" in error.lower()
                            for error in invalid_report["errors"]))

    def test_roadmaps_do_not_invent_progress_for_unavailable_curriculum(self):
        result = get_learning_roadmaps(self.user, self.db)
        self.assertEqual(len(result["tracks"]), 6)
        self.assertTrue(all(track["progress_percent"] == 0 for track in result["tracks"]))
        self.assertTrue(all(stage["status"] == "unavailable"
                            for track in result["tracks"] for stage in track["stages"]))
        self.assertIn("server-recorded", result["progress_basis"])

    def test_review_records_are_owned_by_user(self):
        record_review_result(self.db, self.user.id, "html", "lesson", "html-intro", True)
        rows = self.db.scalars(select(ReviewSchedule).where(ReviewSchedule.user_id == self.user.id)).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].item_slug, "html-intro")

if __name__ == "__main__":
    unittest.main(verbosity=2)
