"""Regression checks for safe portfolio ZIP validation and archive limits."""
from __future__ import annotations

import asyncio
import io
import sys
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy import create_engine, text
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



def test_chunk_streaming_select_then_metadata_update_same_session() -> None:
    """A streamed chunk SELECT must not leave the Session connection in server-cursor mode."""
    from scripts import migrate_portfolio_archives_to_stratus as archive_migration

    with tempfile.TemporaryDirectory(prefix="codeleaf-stream-update-") as temp_dir:
        db_path = Path(temp_dir) / "stream-update.sqlite"
        engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
        Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        payloads = (b"first-chunk", b"second-chunk")
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE project_submission_zip_chunks "
                    "(submission_id TEXT NOT NULL, sequence INTEGER NOT NULL, payload BLOB NOT NULL)"
                ))
                connection.execute(text(
                    "CREATE TABLE project_submissions (id TEXT PRIMARY KEY, object_status TEXT)"
                ))
                connection.execute(
                    text("INSERT INTO project_submissions (id, object_status) VALUES ('submission-1', 'pending')")
                )
                connection.execute(
                    text("INSERT INTO project_submission_zip_chunks "
                         "(submission_id, sequence, payload) VALUES "
                         "('submission-1', 0, :first), ('submission-1', 1, :second)"),
                    {"first": payloads[0], "second": payloads[1]},
                )

            original_size = archive_migration.archive_source_size

            def sqlite_archive_size(db, submission_id, *, has_inline):
                value = db.execute(
                    text("SELECT COALESCE(SUM(length(payload)), 0) "
                         "FROM project_submission_zip_chunks WHERE submission_id=:id"),
                    {"id": submission_id},
                ).scalar_one()
                return int(value or 0)

            archive_migration.archive_source_size = sqlite_archive_size
            try:
                with Session() as db:
                    staged, total, digest = archive_migration.source_to_temporary_file(
                        db,
                        {
                            "id": "submission-1",
                            "has_inline": False,
                            "chunk_count": 2,
                        },
                    )
                    try:
                        assert staged.read() == b"".join(payloads)
                        assert total == sum(map(len, payloads))
                        import hashlib
                        assert digest == hashlib.sha256(b"".join(payloads)).hexdigest()
                        assert not db.connection().get_execution_options().get("stream_results", False)

                        # This normal UPDATE used to fail on PostgreSQL because
                        # stream_results leaked onto the Session-bound Connection.
                        db.execute(
                            text("UPDATE project_submissions SET object_status='verified' WHERE id=:id"),
                            {"id": "submission-1"},
                        )
                        db.commit()
                        assert db.execute(
                            text("SELECT object_status FROM project_submissions WHERE id='submission-1'")
                        ).scalar_one() == "verified"
                    finally:
                        staged.close()
            finally:
                archive_migration.archive_source_size = original_size
        finally:
            engine.dispose()


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
    # Highly compressible payloads that exceed the per-member ratio are ZIP-bomb-like.
    expect_http_error(lambda: validate_project_zip(make_zip({"repeat.bin": b"0" * (2 * 1024 * 1024)})), 413)
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
        def flush(self):
            # Simulate rows becoming visible to the current transaction after flush.
            self.persisted.extend(self.pending)
            self.pending = []
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

    test_chunk_streaming_select_then_metadata_update_same_session()
    print("Portfolio ZIP validation, legacy archive download, and streamed SELECT-to-UPDATE checks passed.")


if __name__ == "__main__":
    main()
