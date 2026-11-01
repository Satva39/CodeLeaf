"""Focused regression tests for the authenticated learner portfolio listing."""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
_TEST_DB = tempfile.TemporaryDirectory(prefix="codeleaf-portfolio-list-import-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEST_DB.name) / 'app-import.db'}"
os.environ["APP_ENV"] = "development"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import Base  # noqa: E402
from app.models import Course, Certificate, ProjectSubmission, User  # noqa: E402
from app.phase5_routes import get_my_portfolio  # noqa: E402


def main() -> None:
    temp = tempfile.TemporaryDirectory(prefix="codeleaf-portfolio-list-")
    engine = create_engine(f"sqlite:///{Path(temp.name) / 'portfolio.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as db:
        owner = User(email="owner@example.invalid", username="owner", display_name="Owner", password_hash="test")
        other = User(email="other@example.invalid", username="other", display_name="Other", password_hash="test")
        course = Course(slug="portfolio-test-course", title="Portfolio Test Course", published=True)
        db.add_all([owner, other, course]); db.flush()
        complete = ProjectSubmission(
            user_id=owner.id, project_slug="catalyst-project", title="Catalyst Project",
            code_bundle={}, zip_bundle=None, zip_filename="project.zip", visibility="private",
            storage_provider="catalyst_stratus", storage_bucket="test-bucket",
            storage_key=f"projects/{uuid4()}/archive.zip", file_size_bytes=123,
            checksum_sha256="a" * 64, object_status="verified", stored_bytes=123,
            portfolio_metadata={"archive_upload_complete": True, "upload_state": "completed"},
        )
        pending = ProjectSubmission(
            user_id=owner.id, project_slug="pending-project", title="Pending Project",
            code_bundle={}, zip_bundle=None, zip_filename="pending.zip", visibility="private",
            storage_provider="catalyst_stratus", object_status="uploading", stored_bytes=10,
            portfolio_metadata={"upload_state": "uploading", "archive_upload_complete": False},
        )
        foreign = ProjectSubmission(
            user_id=other.id, project_slug="other-project", title="Other Project",
            code_bundle={}, visibility="private", portfolio_metadata={},
        )
        db.add_all([complete, pending, foreign]); db.flush()
        db.add(Certificate(public_id="CERTPORTFOLIO001", user_id=owner.id, course_id=course.id))
        db.commit()

        result = get_my_portfolio(owner, db)
        assert result["username"] == "owner"
        assert result["display_name"] == "Owner"
        assert [item["id"] for item in result["items"]] == [str(complete.id)]
        assert result["items"][0]["has_downloadable_zip"] is True
        assert len(result["certificates"]) == 1
        assert result["certificates"][0]["public_id"] == "CERTPORTFOLIO001"
        other_result = get_my_portfolio(other, db)
        assert all(item["id"] != str(complete.id) for item in other_result["items"])
        assert all(item["id"] != str(foreign.id) for item in result["items"])
    engine.dispose(); temp.cleanup()
    print("Authenticated portfolio listing checks passed: owner scoping, pending upload exclusion, Catalyst metadata, and certificates.")


if __name__ == "__main__":
    main()
