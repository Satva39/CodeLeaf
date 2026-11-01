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
    create_portfolio_upload_session, upload_portfolio_submission_chunk,
    finalize_portfolio_upload_session, cancel_portfolio_upload_session,
    upload_portfolio_submission, delete_portfolio_submission,
    PortfolioUploadSessionInput,
)  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from starlette.datastructures import UploadFile  # noqa: E402
from app.storage.base import StoredObject, StorageError  # noqa: E402
from app.plan_entitlements import total_storage_used  # noqa: E402


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


class FakeCatalystStorage:
    bucket_name = "codeleaf-test-bucket"
    def __init__(self, *, corrupt_final_checksum: bool = False, fail_upload: bool = False, fail_delete: bool = False, ignore_delete: bool = False):
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self.corrupt_final_checksum = corrupt_final_checksum
        self.fail_upload = fail_upload
        self.fail_delete = fail_delete
        self.ignore_delete = ignore_delete
    def upload_stream(self, key, stream, *, expected_size=None):
        if self.fail_upload: raise StorageError("simulated Catalyst outage")
        stream.seek(0); payload = stream.read(); stream.seek(0)
        if expected_size is not None and len(payload) != expected_size:
            raise StorageError("size mismatch")
        self.objects[key] = payload
        return StoredObject(key, len(payload), __import__("hashlib").sha256(payload).hexdigest(), self.bucket_name)
    def object_exists(self, key): return key in self.objects
    def object_metadata(self, key):
        if key not in self.objects: raise StorageError("missing")
        return {"size": len(self.objects[key])}
    def checksum_object(self, key):
        if key not in self.objects: raise StorageError("missing")
        digest = __import__("hashlib").sha256(self.objects[key]).hexdigest()
        if self.corrupt_final_checksum and key.endswith("/archive.zip"):
            return "0" * 64
        return digest
    def iter_download(self, key, *, part_size_mb=20):
        if key not in self.objects: raise StorageError("missing")
        yield self.objects[key]
    def delete_object(self, key):
        if self.fail_delete: raise StorageError("simulated delete outage")
        if not self.ignore_delete: self.objects.pop(key, None)
        self.deleted.append(key); return True


class FakeRequest:
    def __init__(self, payload: bytes): self.payload = payload
    async def stream(self): yield self.payload


def _test_catalyst_upload_routes(session, owner, archive_payload: bytes, *, corrupt=False):
    storage = FakeCatalystStorage(corrupt_final_checksum=corrupt)
    old_provider = phase5_routes.settings.portfolio_storage_provider
    old_enabled = phase5_routes.settings.catalyst_stratus_enabled
    old_get_storage = phase5_routes.get_catalyst_storage
    try:
        phase5_routes.settings.portfolio_storage_provider = "catalyst_stratus"
        phase5_routes.settings.catalyst_stratus_enabled = True
        phase5_routes.get_catalyst_storage = lambda: storage
        body = PortfolioUploadSessionInput(filename="route-test.zip", total_bytes=len(archive_payload), project_slug="route-test")
        created = create_portfolio_upload_session(body, owner, session)
        submission_id = __import__("uuid").UUID(created["upload_id"])
        reservation = session.get(ProjectSubmission, submission_id)
        assert reservation.storage_provider == "catalyst_stratus"
        assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=submission_id).count() == 0
        chunk_response = asyncio.run(upload_portfolio_submission_chunk(submission_id, 0, FakeRequest(archive_payload), owner, session))
        assert chunk_response["stored"] and not chunk_response["duplicate"]
        # Identical retries are idempotent; a different body at the same sequence conflicts.
        duplicate = asyncio.run(upload_portfolio_submission_chunk(submission_id, 0, FakeRequest(archive_payload), owner, session))
        assert duplicate["duplicate"]
        expect_http_error(lambda: asyncio.run(upload_portfolio_submission_chunk(submission_id, 0, FakeRequest(b"x" * len(archive_payload)), owner, session)), 409)
        assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=submission_id).count() == 0
        if corrupt:
            expect_http_error(lambda: finalize_portfolio_upload_session(submission_id, owner, session), 503)
            pending = session.get(ProjectSubmission, submission_id)
            assert pending.portfolio_metadata["upload_state"] == "uploading"
            assert not pending.portfolio_metadata.get("archive_upload_complete")
            assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=submission_id).count() == 0
            return storage, submission_id
        finalized = finalize_portfolio_upload_session(submission_id, owner, session)
        completed = session.get(ProjectSubmission, submission_id)
        assert finalized["submission"]
        assert completed.storage_provider == "catalyst_stratus" and completed.object_status == "verified"
        assert completed.storage_key == f"projects/{submission_id}/archive.zip"
        assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=submission_id).count() == 0
        assert completed.storage_key in storage.objects
        assert all("/staging/" not in key for key in storage.objects)
        # Private submissions must not be reachable through the public endpoint.
        expect_http_error(lambda: phase5_routes.download_public_project_submission(owner.username, submission_id, session), 404)
        # Catalyst download must use the object, not the retained Neon payload.
        response = _download_project_zip(completed, is_public=False, db=session)
        async def collect():
            return b"".join([part async for part in response.body_iterator])
        assert asyncio.run(collect()) == archive_payload
        completed.visibility = "public"; session.commit()
        public_response = phase5_routes.download_public_project_submission(owner.username, submission_id, session)
        assert public_response.status_code == 200 or hasattr(public_response, "body_iterator")
        # The archive's quota reservation is removed only after verified remote deletion.
        usage_before_delete = total_storage_used(session, owner.id)
        assert usage_before_delete >= int(completed.stored_bytes or 0)
        # A remote deletion failure must retain the submission and retry marker.
        storage.fail_delete = True
        expect_http_error(lambda: delete_portfolio_submission(submission_id, owner, session), 503)
        retained = session.get(ProjectSubmission, submission_id)
        assert retained is not None and retained.object_status == "delete_pending"
        storage.fail_delete = False
        delete_result = delete_portfolio_submission(submission_id, owner, session)
        assert delete_result["deleted"] and not storage.objects
        assert total_storage_used(session, owner.id) == usage_before_delete - int(completed.stored_bytes or 0)

        ignored_storage = FakeCatalystStorage(ignore_delete=True)
        remote_key = f"projects/{submission_id}/stuck.zip"
        ignored_storage.objects[remote_key] = b"still here"
        stuck = ProjectSubmission(
            user_id=owner.id, project_slug="stuck-delete", title="Stuck deletion", code_bundle={},
            storage_provider="catalyst_stratus", storage_key=remote_key, object_status="verified",
            portfolio_metadata={"archive_upload_complete": True},
        )
        session.add(stuck); session.commit()
        phase5_routes.get_catalyst_storage = lambda: ignored_storage
        expect_http_error(lambda: delete_portfolio_submission(stuck.id, owner, session), 503)
        retained_stuck = session.get(ProjectSubmission, stuck.id)
        assert retained_stuck is not None and remote_key in retained_stuck.portfolio_metadata.get("delete_cleanup_pending", [])
        assert remote_key in ignored_storage.objects
        return storage, submission_id
    finally:
        phase5_routes.settings.portfolio_storage_provider = old_provider
        phase5_routes.settings.catalyst_stratus_enabled = old_enabled
        phase5_routes.get_catalyst_storage = old_get_storage


def _test_catalyst_cancel_and_failed_chunk(session, owner, archive_payload: bytes):
    old_provider = phase5_routes.settings.portfolio_storage_provider
    old_enabled = phase5_routes.settings.catalyst_stratus_enabled
    old_get_storage = phase5_routes.get_catalyst_storage
    try:
        phase5_routes.settings.portfolio_storage_provider = "catalyst_stratus"
        phase5_routes.settings.catalyst_stratus_enabled = True
        storage = FakeCatalystStorage()
        phase5_routes.get_catalyst_storage = lambda: storage
        body = PortfolioUploadSessionInput(filename="cancel-test.zip", total_bytes=len(archive_payload), project_slug="cancel-test")
        created = create_portfolio_upload_session(body, owner, session); sid = __import__("uuid").UUID(created["upload_id"])
        asyncio.run(upload_portfolio_submission_chunk(sid, 0, FakeRequest(archive_payload), owner, session))
        assert storage.objects
        assert cancel_portfolio_upload_session(sid, owner, session)["deleted"]
        assert not storage.objects and session.get(ProjectSubmission, sid) is None

        failed_storage = FakeCatalystStorage(fail_upload=True)
        phase5_routes.get_catalyst_storage = lambda: failed_storage
        created = create_portfolio_upload_session(body, owner, session); failed_id = __import__("uuid").UUID(created["upload_id"])
        expect_http_error(lambda: asyncio.run(upload_portfolio_submission_chunk(failed_id, 0, FakeRequest(archive_payload), owner, session)), 503)
        failed_row = session.get(ProjectSubmission, failed_id)
        assert failed_row is not None and failed_row.portfolio_metadata.get("staging_cleanup_pending")
        assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=failed_id).count() == 0
        # With no remote object, cancellation can safely reconcile the pending deterministic key.
        phase5_routes.get_catalyst_storage = lambda: storage
        assert cancel_portfolio_upload_session(failed_id, owner, session)["deleted"]
    finally:
        phase5_routes.settings.portfolio_storage_provider = old_provider
        phase5_routes.settings.catalyst_stratus_enabled = old_enabled
        phase5_routes.get_catalyst_storage = old_get_storage


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
            other_user = User(email="zip-other@example.test", display_name="Other User", password_hash="test-hash", username="zip-other")
            session.add(other_user)
            session.commit()
            # Owner checks must hide another learner's project and preserve it.
            protected = ProjectSubmission(user_id=other_user.id, project_slug="protected", title="Protected", code_bundle={}, zip_bundle=b"legacy", stored_bytes=6)
            session.add(protected)
            session.commit()
            expect_http_error(lambda: delete_portfolio_submission(protected.id, owner, session), 404)
            assert session.get(ProjectSubmission, protected.id) is not None

            # Legacy Neon ZIP chunks are deleted with the owned parent row and their quota is released.
            legacy_usage_before = total_storage_used(session, owner.id)
            legacy_delete = ProjectSubmission(user_id=owner.id, project_slug="legacy-delete", title="Legacy delete", code_bundle={}, zip_bundle=None, zip_filename="legacy-delete.zip", stored_bytes=14)
            session.add(legacy_delete)
            session.commit()
            session.add_all([
                ProjectSubmissionZipChunk(submission_id=legacy_delete.id, sequence=0, payload=b"legacy-"),
                ProjectSubmissionZipChunk(submission_id=legacy_delete.id, sequence=1, payload=b"archive"),
            ])
            session.commit()
            assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=legacy_delete.id).count() == 2
            assert delete_portfolio_submission(legacy_delete.id, owner, session)["deleted"]
            assert session.get(ProjectSubmission, legacy_delete.id) is None
            assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=legacy_delete.id).count() == 0
            assert total_storage_used(session, owner.id) == legacy_usage_before
            assert session.get(ProjectSubmission, protected.id) is not None

            # Production-mode chunk uploads stage bytes in Catalyst and leave Neon metadata-only.
            _test_catalyst_upload_routes(session, owner, valid_archive)
            # A remote checksum mismatch leaves the upload pending and retryable, never in Neon.
            _test_catalyst_upload_routes(session, owner, valid_archive, corrupt=True)
            _test_catalyst_cancel_and_failed_chunk(session, owner, valid_archive)
            # Catalyst selected but disabled must fail closed instead of using Neon.
            phase5_routes.settings.portfolio_storage_provider = "catalyst_stratus"
            phase5_routes.settings.catalyst_stratus_enabled = False
            expect_http_error(lambda: create_portfolio_upload_session(PortfolioUploadSessionInput(filename="disabled.zip", total_bytes=len(valid_archive)), owner, session), 503)
            # Direct upload uses Catalyst and creates no PostgreSQL ZIP chunk rows.
            storage = FakeCatalystStorage()
            old_provider = phase5_routes.settings.portfolio_storage_provider
            old_enabled = phase5_routes.settings.catalyst_stratus_enabled
            old_get_storage = phase5_routes.get_catalyst_storage
            try:
                phase5_routes.settings.portfolio_storage_provider = "catalyst_stratus"
                phase5_routes.settings.catalyst_stratus_enabled = True
                phase5_routes.get_catalyst_storage = lambda: storage
                direct_file = UploadFile(filename="direct-test.zip", file=io.BytesIO(valid_archive))
                direct = upload_portfolio_submission("", "direct-test", "Direct Test", direct_file, owner, session)
                direct_row = session.get(ProjectSubmission, __import__("uuid").UUID(str(direct["submission"]["id"])))
                assert direct_row.storage_provider == "catalyst_stratus" and direct_row.object_status == "verified"
                assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=direct_row.id).count() == 0
                assert direct_row.storage_key in storage.objects
                delete_portfolio_submission(direct_row.id, owner, session)
                assert not storage.objects
                failing_storage = FakeCatalystStorage(fail_upload=True)
                phase5_routes.get_catalyst_storage = lambda: failing_storage
                failed_file = UploadFile(filename="failed-direct.zip", file=io.BytesIO(valid_archive))
                expect_http_error(lambda: upload_portfolio_submission("", "failed-direct", "Failed Direct", failed_file, owner, session), 503)
                failed_rows = session.query(ProjectSubmission).filter(ProjectSubmission.project_slug == "failed-direct").all()
                assert failed_rows and not failed_rows[0].portfolio_metadata.get("archive_upload_complete")
                assert session.query(ProjectSubmissionZipChunk).filter_by(submission_id=failed_rows[0].id).count() == 0
            finally:
                phase5_routes.settings.portfolio_storage_provider = old_provider
                phase5_routes.settings.catalyst_stratus_enabled = old_enabled
                phase5_routes.get_catalyst_storage = old_get_storage
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

    print("Portfolio ZIP validation, Catalyst direct/chunk uploads, retry safety, checksum rejection, downloads, deletion, and legacy archive checks passed.")


if __name__ == "__main__":
    main()
