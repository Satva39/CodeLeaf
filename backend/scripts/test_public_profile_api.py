"""In-memory integration checks for opt-in public profiles and atomic dog saves."""
from __future__ import annotations

from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_security import require_user
from app.db import Base, get_db
from app.main import app
from app.models import (
    Certificate,
    Course,
    Lesson,
    LessonProgress,
    Module,
    User,
    UserAchievement,
    UserAvatarInventory,
    XPTransaction,
)


def check_migration() -> None:
    migration_path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0014_public_profile_visibility.py"
    spec = spec_from_file_location("public_profile_migration_test", migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the public-profile migration for testing.")
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE users (id VARCHAR(36) PRIMARY KEY, username VARCHAR(40) NOT NULL UNIQUE)"
        )
        # The baseline metadata migration creates this expression index before
        # revision 0014. SQLite Inspector.get_indexes() skips expression indexes,
        # so revision 0014 must detect it through sqlite_master instead.
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX uq_users_username_lower ON users (lower(username))"
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("users")}
        assert set(migration.PUBLIC_COLUMNS).issubset(columns)
        indexes = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "uq_users_username_lower" in indexes
        migration.upgrade()
        assert "uq_users_username_lower" in {
            row[0] for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
    engine.dispose()
    print("PASS additive public-profile migration adds opt-in fields and case-insensitive username index")


def main() -> None:
    check_migration()

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = session_factory()
    learner = User(
        email="learner@example.test",
        display_name="Test Learner",
        username="testlearner",
        password_hash="not-a-real-password-hash",
        theme="dark",
        is_active=True,
        is_email_verified=True,
    )
    db.add(learner)
    db.flush()
    db.add(UserAvatarInventory(user_id=learner.id, item_id="starter-cap", acquired_via="test"))

    course = Course(slug="python", title="Python", published=True)
    db.add(course)
    db.flush()
    module = Module(course_id=course.id, slug="basics", title="Basics")
    db.add(module)
    db.flush()
    lesson = Lesson(module_id=module.id, slug="first-lesson", title="First lesson", is_published=True)
    db.add(lesson)
    db.flush()
    db.add(LessonProgress(user_id=learner.id, lesson_id=lesson.id, completed=True))
    db.add(
        XPTransaction(
            user_id=learner.id,
            source_type="lesson",
            source_id="test-lesson",
            base_points=10,
            awarded_points=Decimal("10.00"),
            boost_applied=False,
        )
    )
    db.add(UserAchievement(user_id=learner.id, achievement_id="first-task", reward_item_id="starter-cap"))
    db.add(Certificate(user_id=learner.id, course_id=course.id, public_id="TESTPUBLICCERTIFICATE"))
    db.commit()

    def override_db():
        yield db

    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_user] = lambda: learner

    try:
        with TestClient(app) as client:
            account = client.get("/api/me")
            assert account.status_code == 200, account.text
            assert account.json()["user"]["username"] == "testlearner"
            assert "no-store" in account.headers.get("cache-control", "")
            print("PASS current-account endpoint returns the expected user envelope with private no-store cache headers")

            settings = client.get("/api/me/public-profile")
            assert settings.status_code == 200, settings.text
            assert settings.json()["settings"]["is_public"] is False
            assert settings.json()["profile_path"] == "/u/testlearner"
            print("PASS authenticated settings endpoint exposes a link while the profile is private")

            private = client.get("/api/public-profiles/TESTLEARNER")
            assert private.status_code == 404
            print("PASS private profiles return 404 for case-insensitive username lookups")

            learner.is_email_verified = False
            db.commit()
            blocked = client.patch("/api/me/public-profile", json={"is_public": True})
            assert blocked.status_code == 403 and "Verify your email" in blocked.json()["detail"]
            learner.is_email_verified = True
            db.commit()
            print("PASS unverified accounts receive a clear publication requirement")

            published = client.patch(
                "/api/me/public-profile",
                json={
                    "is_public": True,
                    "show_xp": True,
                    "show_streak": True,
                    "show_certificates": True,
                    "show_achievements": True,
                    "show_progress": True,
                },
            )
            assert published.status_code == 200, published.text
            public = client.get("/api/public-profiles/TESTLEARNER")
            assert public.status_code == 200, public.text
            payload = public.json()
            assert payload["username"] == "testlearner"
            assert payload["stats"]["total_xp"] == 10
            assert payload["progress"][0]["course_slug"] == "python"
            assert payload["achievements"][0]["id"] == "first-task"
            assert payload["certificates"][0]["public_id"] == "TESTPUBLICCERTIFICATE"
            for private_field in ("email", "password_hash", "id", "role", "token"):
                assert private_field not in payload
            print("PASS published profile returns only enabled sections and no private account fields")

            # The username index is case-insensitive and does not silently rename accounts.
            duplicate = User(
                email="second@example.test",
                display_name="Second Learner",
                username="TESTLEARNER",
                password_hash="not-a-real-password-hash",
                theme="dark",
            )
            db.add(duplicate)
            try:
                db.commit()
                raise AssertionError("Case-only duplicate username was unexpectedly accepted.")
            except IntegrityError:
                db.rollback()
            print("PASS case-only duplicate usernames are rejected by the database index")

            avatar_save = client.put(
                "/api/me/avatar",
                json={
                    "appearance": {"breed": "shiba", "fur_color": "copper", "eye_color": "green"},
                    "equipment": {"headwear": "starter-cap"},
                },
            )
            assert avatar_save.status_code == 200, avatar_save.text
            assert avatar_save.json()["appearance"]["breed"] == "shiba"
            assert avatar_save.json()["equipment"]["headwear"] == "starter-cap"
            print("PASS owned dog cosmetics and appearance save atomically")

            locked = client.put(
                "/api/me/avatar",
                json={
                    "appearance": {"breed": "classic", "fur_color": "golden", "eye_color": "brown"},
                    "equipment": {"glasses": "developer-glasses"},
                },
            )
            assert locked.status_code == 403
            conflict = client.put(
                "/api/me/avatar",
                json={
                    "appearance": {"breed": "classic", "fur_color": "golden", "eye_color": "brown"},
                    "equipment": {"shirt": "blue-hoodie", "outfit": "warrior-outfit"},
                },
            )
            assert conflict.status_code == 422
            print("PASS locked items and conflicting shirt/outfit slots are rejected")

            hidden = client.patch("/api/me/public-profile", json={"is_public": False})
            assert hidden.status_code == 200
            assert client.get("/api/public-profiles/testlearner").status_code == 404
            print("PASS unpublishing immediately hides the public profile")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        db.close()
        engine.dispose()

    print("Public-profile and dog-avatar integration checks passed.")


if __name__ == "__main__":
    main()
