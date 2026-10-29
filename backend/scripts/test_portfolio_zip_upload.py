"""Regression checks for safe portfolio ZIP validation and archive limits."""
from __future__ import annotations

import asyncio
import io
import sys
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import phase5_routes  # noqa: E402
from app.db import Base  # noqa: E402
from app.models import ProjectSubmission, ProjectSubmissionZipChunk, User  # noqa: E402
from app.phase5_routes import (
    MAX_PROJECT_ZIP_BYTES, PROJECT_ZIP_CHUNK_BYTES,
    _download_project_zip, _normalize_portfolio_slug, _store_project_zip_chunks,
    validate_project_zip, validate_project_zip_file, validate_project_zip_size,
)  # noqa: E402
from fastapi import HTTPException  # noqa: E402


def make_zip(entries: dict[str, bytes | str]) -> bytes:
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return target.getvalue()


def expect_http_error(operation, expected_status: int) -> None:
    try:
        operation()
    except HTTPException as exc:
        assert exc.status_code == expected_status, (exc.status_code, exc.detail)
    else:
        raise AssertionError(f"Expected HTTP {expected_status}")


def main() -> None:
    valid_archive = make_zip({"index.html": "<h1>Hello</h1>", "assets/site.css": "body {}"})
    files = validate_project_zip(valid_archive)
    assert files == ["index.html", "assets/site.css"]
    with io.BytesIO(valid_archive) as file_obj:
        assert validate_project_zip_file(file_obj) == files

    expect_http_error(lambda: validate_project_zip(b"not a zip"), 400)
    expect_http_error(lambda: validate_project_zip(make_zip({"../escape.txt": "no"})), 400)
    expect_http_error(lambda: validate_project_zip(make_zip({"C:/escape.txt": "no"})), 400)
    expect_http_error(lambda: validate_project_zip(make_zip({})), 400)
    assert MAX_PROJECT_ZIP_BYTES == 500 * 1024 * 1024
    validate_project_zip_size(MAX_PROJECT_ZIP_BYTES)
    expect_http_error(lambda: validate_project_zip_size(MAX_PROJECT_ZIP_BYTES + 1), 413)
    assert _normalize_portfolio_slug("My New Project", fallback="unused") == "my-new-project"
    assert _normalize_portfolio_slug("HTML", fallback="unused", max_length=100) == "html"

    # Chunk writing must not materialize the full uploaded archive in one database value.
    class FakeChunkDB:
        def __init__(self):
            self.pending = []
            self.persisted = []
            self.commits = 0
        def add_all(self, rows):
            self.pending.extend(rows)
        def commit(self):
            self.persisted.extend(self.pending)
            self.pending = []
            self.commits += 1

    large_payload = b"z" * (PROJECT_ZIP_CHUNK_BYTES * 2 + 17)
    fake_db = FakeChunkDB()
    chunk_count = _store_project_zip_chunks(fake_db, "test-submission", io.BytesIO(large_payload))
    assert chunk_count == 3
    assert [chunk.sequence for chunk in fake_db.persisted] == [0, 1, 2]
    assert b"".join(chunk.payload for chunk in fake_db.persisted) == large_payload
    assert all(isinstance(chunk, ProjectSubmissionZipChunk) for chunk in fake_db.persisted)

    # Chunk-backed downloads stream from the database in bounded batches.
    # Use a platform-managed temporary directory; /tmp does not exist on many
    # Windows installations, and SQLite must receive a correctly formatted URL.
    with tempfile.TemporaryDirectory(prefix="codeleaf-portfolio-test-") as temp_dir:
        test_db_path = Path(temp_dir) / "portfolio-chunks-test.sqlite"
        sqlite_url = "sqlite:///" + test_db_path.resolve().as_posix()
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        TestSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        session = TestSessionLocal()
        old_session_factory = phase5_routes.SessionLocal
        try:
            owner = User(email="zip-test@example.test", display_name="ZIP Test", password_hash="test-hash", username="zip-test")
            session.add(owner)
            session.commit()
            submission = ProjectSubmission(
                user_id=owner.id, project_slug="stream-test", title="Stream Test", code_bundle={},
                zip_bundle=None, zip_filename="stream-test.zip", visibility="public",
                portfolio_metadata={"custom_project": True, "archive_upload_complete": True},
            )
            session.add(submission)
            session.commit()
            session.add_all([
                ProjectSubmissionZipChunk(submission_id=submission.id, sequence=0, payload=b"chunk-a"),
                ProjectSubmissionZipChunk(submission_id=submission.id, sequence=1, payload=b"chunk-b"),
            ])
            session.commit()
            phase5_routes.SessionLocal = TestSessionLocal
            response = _download_project_zip(submission, is_public=True, db=session)
            async def collect_stream():
                parts = []
                async for part in response.body_iterator:
                    parts.append(part)
                return b"".join(parts)
            assert asyncio.run(collect_stream()) == b"chunk-achunk-b"
        finally:
            phase5_routes.SessionLocal = old_session_factory
            session.close()
            engine.dispose()

    # Old JSON-bundle submissions must remain downloadable as a generated ZIP.
    class LegacySubmission:
        project_slug = "legacy-html"
        zip_bundle = None
        zip_filename = None
        code_bundle = {"index.html": "<h1>Saved before ZIP uploads</h1>"}

    response = _download_project_zip(LegacySubmission(), is_public=True)
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        assert archive.read("index.html").decode("utf-8") == "<h1>Saved before ZIP uploads</h1>"
    assert response.headers["content-type"] == "application/zip"

    print("Portfolio ZIP validation and legacy archive download checks passed.")


if __name__ == "__main__":
    main()
