"""Compressed, versioned course lesson bundles stored in Catalyst Stratus.

Neon remains the source of relational course/lesson metadata. This module stores
full lesson JSON documents in one immutable gzip bundle per course and keeps a
small pointer/checksum record in PostgreSQL.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Course, CourseContentBundle, Lesson, Module
from . import StorageError, get_catalyst_storage

logger = logging.getLogger(__name__)
BUNDLE_SCHEMA_VERSION = 1
MAX_COMPRESSED_BUNDLE_BYTES = 64 * 1024 * 1024
_MAX_CACHE_BYTES = 16 * 1024 * 1024
_BUNDLE_CACHE: OrderedDict[tuple[str, str, str], tuple[dict[str, Any], int]] = OrderedDict()
_BUNDLE_CACHE_BYTES = 0


class LessonContentUnavailable(StorageError):
    """Raised when a lesson was externalized but its verified bundle is unavailable."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def lesson_metadata_only(document: dict[str, Any]) -> dict[str, Any]:
    """Keep query/outline metadata in Neon while removing the large lesson body."""
    metadata = {key: value for key, value in document.items() if key != "content"}
    metadata["_lesson_content_externalized"] = True
    return metadata


def _json_bytes(course_id: str, course_slug: str, lessons: dict[str, dict[str, Any]]) -> bytes:
    document = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "course_id": course_id,
        "course_slug": course_slug,
        "lessons": lessons,
    }
    try:
        raw = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StorageError("Course lesson bundle contains non-JSON data.") from exc
    return raw


def build_course_bundle(
    course_id: str,
    course_slug: str,
    lessons: dict[str, dict[str, Any]],
) -> tuple[bytes, int, str, str]:
    """Return compressed bytes, raw byte count, SHA-256, and immutable object key."""
    raw = _json_bytes(course_id, course_slug, lessons)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    digest = hashlib.sha256(compressed).hexdigest()
    key = f"lesson-bundles/courses/{course_id}/{digest}.json.gz"
    return compressed, len(raw), digest, key


def decode_course_bundle(
    payload: bytes,
    *,
    expected_course_id: str | None = None,
    expected_checksum: str | None = None,
) -> dict[str, Any]:
    if len(payload) > MAX_COMPRESSED_BUNDLE_BYTES:
        raise StorageError("Course lesson bundle exceeds the configured safety limit.")
    actual = hashlib.sha256(payload).hexdigest()
    if expected_checksum and actual.lower() != expected_checksum.lower():
        raise StorageError("Course lesson bundle checksum mismatch.")
    try:
        document = json.loads(gzip.decompress(payload).decode("utf-8"))
    except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StorageError("Course lesson bundle is corrupt or unreadable.") from exc
    if not isinstance(document, dict) or document.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise StorageError("Course lesson bundle schema version is unsupported.")
    if expected_course_id and document.get("course_id") != expected_course_id:
        raise StorageError("Course lesson bundle belongs to a different course.")
    lessons = document.get("lessons")
    if not isinstance(lessons, dict) or not all(
        isinstance(key, str) and isinstance(value, dict) for key, value in lessons.items()
    ):
        raise StorageError("Course lesson bundle has an invalid lesson map.")
    return document


def _download_bundle(storage, record: CourseContentBundle) -> dict[str, Any]:
    global _BUNDLE_CACHE_BYTES
    cache_key = (record.storage_bucket, record.storage_key, record.checksum_sha256)
    cached = _BUNDLE_CACHE.get(cache_key)
    if cached is not None:
        _BUNDLE_CACHE.move_to_end(cache_key)
        return cached[0]

    parts: list[bytes] = []
    total = 0
    for chunk in storage.iter_download(record.storage_key):
        total += len(chunk)
        if total > MAX_COMPRESSED_BUNDLE_BYTES:
            raise StorageError("Course lesson bundle exceeds the configured safety limit.")
        parts.append(chunk)
    payload = b"".join(parts)
    if len(payload) != int(record.compressed_size_bytes):
        raise StorageError("Downloaded course bundle size does not match its database record.")
    document = decode_course_bundle(
        payload,
        expected_course_id=str(record.course_id),
        expected_checksum=record.checksum_sha256,
    )
    raw_size = int(record.raw_size_bytes)
    if raw_size <= _MAX_CACHE_BYTES:
        _BUNDLE_CACHE[cache_key] = (document, raw_size)
        _BUNDLE_CACHE_BYTES += raw_size
        _BUNDLE_CACHE.move_to_end(cache_key)
        while _BUNDLE_CACHE_BYTES > _MAX_CACHE_BYTES and _BUNDLE_CACHE:
            _old_key, (_old_document, old_size) = _BUNDLE_CACHE.popitem(last=False)
            _BUNDLE_CACHE_BYTES -= old_size
    return document


def _existing_bundle_documents(db: Session, course: Course, storage) -> dict[str, dict[str, Any]]:
    record = db.get(CourseContentBundle, course.id)
    if record is None or record.object_status not in {"verified", "restored"}:
        return {}
    try:
        return _download_bundle(storage, record)["lessons"]
    except StorageError:
        # The importer must not overwrite a previous externalized bundle with a
        # partial set of files when the existing copy cannot be read.
        raise


def publish_course_bundle(
    db: Session,
    course: Course,
    storage=None,
    *,
    externalize: bool = False,
) -> CourseContentBundle:
    """Publish a complete course bundle; optionally replace Neon lesson bodies with metadata.

    Existing externalized lesson documents are merged from the previous bundle so an
    import that updates only a subset of lessons cannot silently drop other lessons.
    The object is uploaded and checksum-verified before any DB pointers are changed.
    """
    storage = storage or get_catalyst_storage()
    if storage is None:
        raise StorageError("Catalyst Stratus is not configured for course content.")

    existing_documents = _existing_bundle_documents(db, course, storage)
    lesson_rows = db.scalars(
        select(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course.id)
        .order_by(Module.sort_order.asc(), Lesson.sort_order.asc(), Lesson.id.asc())
    ).all()
    if not lesson_rows:
        raise StorageError(f"Course {course.slug} has no lesson rows to bundle.")

    lesson_documents: dict[str, dict[str, Any]] = {}
    for lesson in lesson_rows:
        lesson_id = str(lesson.id)
        current = lesson.content if isinstance(lesson.content, dict) else {}
        previous = existing_documents.get(lesson_id)
        if "content" in current and not current.get("_lesson_content_externalized"):
            document = dict(current)
        elif previous is not None:
            document = dict(previous)
            # Preserve the current small metadata fields (stable ID, preview marker,
            # outline metadata) while retaining the full content body from Stratus.
            for key, value in current.items():
                if key not in {"_lesson_content_externalized"}:
                    document[key] = value
        elif "_lesson_content_externalized" in current:
            raise StorageError(
                f"Lesson {lesson_id} is marked externalized but its previous course bundle is unavailable."
            )
        else:
            document = dict(current)
        lesson_documents[lesson_id] = document

    compressed, raw_size, digest, key = build_course_bundle(
        str(course.id), course.slug, lesson_documents
    )
    if storage.object_exists(key):
        remote_digest = storage.checksum_object(key)
        if remote_digest.lower() != digest.lower():
            raise StorageError("An existing versioned course bundle has an unexpected checksum.")
    else:
        stored = storage.upload_stream(key, io.BytesIO(compressed), expected_size=len(compressed))
        if stored.checksum_sha256.lower() != digest.lower():
            raise StorageError("Catalyst upload checksum differs from the generated course bundle.")
    if not storage.object_exists(key):
        raise StorageError("Catalyst course bundle upload was not visible after upload.")
    metadata = storage.object_metadata(key)
    if int(metadata.get("size") or 0) != len(compressed):
        raise StorageError("Catalyst course bundle object size does not match the upload.")
    remote_digest = storage.checksum_object(key)
    if remote_digest.lower() != digest.lower():
        raise StorageError("Catalyst course bundle remote checksum verification failed.")

    record = db.get(CourseContentBundle, course.id)
    if record is None:
        record = CourseContentBundle(course_id=course.id)
        db.add(record)
    record.storage_provider = "catalyst_stratus"
    record.storage_bucket = storage.bucket_name
    record.storage_key = key
    record.checksum_sha256 = digest
    record.compressed_size_bytes = len(compressed)
    record.raw_size_bytes = raw_size
    record.lesson_count = len(lesson_documents)
    record.schema_version = BUNDLE_SCHEMA_VERSION
    record.object_status = "verified"
    record.updated_at = utc_now()

    if externalize:
        for lesson in lesson_rows:
            lesson.content = lesson_metadata_only(lesson_documents[str(lesson.id)])
    return record


def verify_course_bundle(db: Session, course: Course, storage=None) -> tuple[bool, str]:
    storage = storage or get_catalyst_storage()
    if storage is None:
        return False, "catalyst_not_configured"
    record = db.get(CourseContentBundle, course.id)
    if record is None or record.object_status not in {"verified", "restored"}:
        return False, "bundle_reference_missing"
    try:
        if not storage.object_exists(record.storage_key):
            return False, "object_missing_or_inaccessible"
        metadata = storage.object_metadata(record.storage_key)
        if int(metadata.get("size") or 0) != int(record.compressed_size_bytes):
            return False, "object_size_mismatch"
        if storage.checksum_object(record.storage_key).lower() != record.checksum_sha256.lower():
            return False, "object_checksum_mismatch"
        bundle = _download_bundle(storage, record)
        lessons = db.scalars(
            select(Lesson).join(Module, Lesson.module_id == Module.id).where(Module.course_id == course.id)
        ).all()
        if len(bundle["lessons"]) != len(lessons):
            return False, "lesson_count_mismatch"
        for lesson in lessons:
            if str(lesson.id) not in bundle["lessons"]:
                return False, "lesson_missing_from_bundle"
        return True, "verified"
    except StorageError:
        return False, "storage_or_checksum_error"


def load_lesson_document(db: Session, lesson: Lesson) -> dict[str, Any]:
    """Load a full lesson document, preferring a verified course bundle when present."""
    metadata = lesson.content if isinstance(lesson.content, dict) else {}
    module = db.get(Module, lesson.module_id)
    course = db.get(Course, module.course_id) if module else None
    record = db.get(CourseContentBundle, course.id) if course else None
    if record is not None and record.object_status == "verified":
        storage = get_catalyst_storage()
        if storage is not None:
            try:
                bundle = _download_bundle(storage, record)
                document = bundle["lessons"].get(str(lesson.id))
                if isinstance(document, dict):
                    return document
                raise StorageError("Lesson is not present in its verified course bundle.")
            except StorageError as exc:
                if "content" in metadata and not metadata.get("_lesson_content_externalized"):
                    logger.exception("Course bundle read failed; using retained Neon lesson copy.")
                    return metadata
                raise LessonContentUnavailable(
                    "Lesson content is temporarily unavailable from course storage."
                ) from exc
    if metadata.get("_lesson_content_externalized") or "content" not in metadata:
        raise LessonContentUnavailable(
            "Lesson content has been externalized but no verified course bundle is available."
        )
    return metadata


def externalize_course_content(db: Session, course: Course, storage=None) -> tuple[int, int]:
    """Strip lesson bodies from Neon only after the full course bundle verifies."""
    ok, reason = verify_course_bundle(db, course, storage)
    if not ok:
        raise StorageError(f"Cannot externalize course {course.slug}: {reason}.")
    record = db.get(CourseContentBundle, course.id)
    bundle = _download_bundle(storage or get_catalyst_storage(), record)
    lessons = db.scalars(
        select(Lesson).join(Module, Lesson.module_id == Module.id).where(Module.course_id == course.id)
    ).all()
    removed_bytes = 0
    for lesson in lessons:
        current = lesson.content if isinstance(lesson.content, dict) else {}
        if "content" in current:
            try:
                removed_bytes += len(json.dumps(current["content"], ensure_ascii=False).encode("utf-8"))
            except (TypeError, ValueError):
                pass
        document = bundle["lessons"].get(str(lesson.id))
        if not isinstance(document, dict):
            raise StorageError(f"Course bundle is missing lesson {lesson.id}; Neon cleanup blocked.")
        lesson.content = lesson_metadata_only(document)
    return len(lessons), removed_bytes


def restore_course_content_to_neon(db: Session, course: Course, storage=None) -> tuple[int, int]:
    """Restore complete lesson JSON to Neon while retaining Stratus as a rollback copy."""
    storage = storage or get_catalyst_storage()
    record = db.get(CourseContentBundle, course.id)
    if storage is None or record is None:
        raise StorageError(f"No verified Stratus bundle exists for {course.slug}.")
    bundle = _download_bundle(storage, record)
    lessons = db.scalars(
        select(Lesson).join(Module, Lesson.module_id == Module.id).where(Module.course_id == course.id)
    ).all()
    total_bytes = 0
    for lesson in lessons:
        document = bundle["lessons"].get(str(lesson.id))
        if not isinstance(document, dict):
            raise StorageError(f"Course bundle is missing lesson {lesson.id}; restore aborted.")
        lesson.content = document
        total_bytes += len(json.dumps(document, ensure_ascii=False).encode("utf-8"))
    record.object_status = "restored"
    record.updated_at = utc_now()
    return len(lessons), total_bytes
