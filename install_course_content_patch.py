from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def replace_once(path: Path, old: str, new: str, *, label: str) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one source anchor in {path}, found {count}; no project files have been written.")
    path.write_text(content.replace(old, new, 1), encoding="utf-8", newline="")


def replace_count(path: Path, old: str, new: str, *, expected: int, label: str) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} source anchors in {path}, found {count}; no project files have been written.")
    path.write_text(content.replace(old, new), encoding="utf-8", newline="")


def replace_in_function(path: Path, function_name: str, old: str, new: str, *, next_marker: str) -> None:
    content = path.read_text(encoding="utf-8")
    start_marker = f"def {function_name}"
    start = content.find(start_marker)
    if start < 0:
        raise RuntimeError(f"Missing function {function_name} in {path}; no project files have been written.")
    end = content.find(next_marker, start + len(start_marker))
    if end < 0:
        end = len(content)
    segment = content[start:end]
    if segment.count(old) != 1:
        raise RuntimeError(f"Expected exactly one target expression in {function_name}, found {segment.count(old)}; no project files have been written.")
    updated = segment.replace(old, new, 1)
    path.write_text(content[:start] + updated + content[end:], encoding="utf-8", newline="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    backend = root / "backend"
    package = Path(__file__).resolve().parent

    targets = {
        "config": backend / "app/config.py",
        "models": backend / "app/models.py",
        "main": backend / "app/main.py",
        "importer": backend / "scripts/import_course_files.py",
        "migration_test": backend / "scripts/test_migration_repeatability.py",
        "env": backend / ".env.example",
    }
    for label, path in targets.items():
        if not path.is_file():
            raise RuntimeError(f"Missing target {label}: {path}")

    # Preflight all source anchors before making any modifications.
    checks = {
        "config provider field": (targets["config"], '    portfolio_storage_provider: str = "database"\n'),
        "config validation": (targets["config"], '        if self.portfolio_storage_provider.strip().lower() not in {"database", "catalyst_stratus"}:\n            raise ValueError("PORTFOLIO_STORAGE_PROVIDER must be \'database\' or \'catalyst_stratus\'")\n'),
        "model Lesson anchor": (targets["models"], "\n\nclass Lesson(Base):\n"),
        "main FastAPI anchor": (targets["main"], "\napp = FastAPI(\n"),
        "lesson detail function": (targets["main"], "def get_published_lesson_content("),
        "knowledge check function": (targets["main"], "def _load_lesson_knowledge_check("),
        "importer model import": (targets["importer"], "from app.models import Course, Module, Lesson, Exercise\n"),
        "importer course loop": (targets["importer"], "def import_course_records(db, course_data: dict[str, Any], tree, published: bool):\n"),
        "migration test revision": (targets["migration_test"], 'revisions[0] != "0010_catalyst_stratus"'),
        "migration test tables": (targets["migration_test"], '"courses", "course_modules", "lessons"'),
        "env portfolio variable": (targets["env"], "PORTFOLIO_STORAGE_PROVIDER=database\n"),
    }
    for label, (path, anchor) in checks.items():
        if anchor not in path.read_text(encoding="utf-8"):
            raise RuntimeError(f"Missing or changed source anchor: {label} in {path}. No project files were modified.")

    # Check the lesson route and knowledge-check callers with current source before backups.
    main_text = targets["main"].read_text(encoding="utf-8")
    if main_text.count("_load_lesson_knowledge_check(course_slug, lesson)") != 2:
        raise RuntimeError("Expected exactly two knowledge-check helper callers; source differs. No project files were modified.")
    if main_text.count("stored = lesson.content or {}") < 2:
        raise RuntimeError("Expected lesson detail and knowledge-check storage reads. No project files were modified.")

    migration_dir = backend / "alembic/versions"
    if (migration_dir / "0011_course_content_bundles.py").exists():
        raise RuntimeError("Migration 0011_course_content_bundles.py already exists. Inspect the existing migration before applying this package.")

    # Create a timestamped backup of all files that will be edited.
    backup_root = root / ".codeleaf-catalyst-course-storage-backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root.mkdir(parents=True, exist_ok=False)
    edit_paths = list(targets.values())
    for path in edit_paths:
        backup = backup_root / path.relative_to(root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)

    try:
        # Settings: a separate switch for course lesson content, independent of ZIP storage.
        replace_once(
            targets["config"],
            '    portfolio_storage_provider: str = "database"\n',
            '    portfolio_storage_provider: str = "database"\n'
            '    # Full lesson JSON moves to course-level Stratus bundles only when explicitly selected.\n'
            '    lesson_content_storage_provider: str = "database"\n',
            label="config provider field",
        )
        replace_once(
            targets["config"],
            '        if self.portfolio_storage_provider.strip().lower() not in {"database", "catalyst_stratus"}:\n            raise ValueError("PORTFOLIO_STORAGE_PROVIDER must be \'database\' or \'catalyst_stratus\'")\n',
            '        if self.portfolio_storage_provider.strip().lower() not in {"database", "catalyst_stratus"}:\n            raise ValueError("PORTFOLIO_STORAGE_PROVIDER must be \'database\' or \'catalyst_stratus\'")\n'
            '        if self.lesson_content_storage_provider.strip().lower() not in {"database", "catalyst_stratus"}:\n'
            '            raise ValueError("LESSON_CONTENT_STORAGE_PROVIDER must be \'database\' or \'catalyst_stratus\'")\n'
            '        if self.lesson_content_storage_provider.strip().lower() == "catalyst_stratus" and not all((self.catalyst_project_id, self.catalyst_project_zaid, self.catalyst_client_id, self.catalyst_client_secret, self.catalyst_refresh_token, self.catalyst_stratus_bucket)):\n'
            '            raise ValueError("Catalyst credentials and bucket are required when LESSON_CONTENT_STORAGE_PROVIDER=catalyst_stratus")\n',
            label="config validation",
        )

        # SQLAlchemy model for one immutable compressed bundle per course.
        model_class = '''\n\nclass CourseContentBundle(Base):\n    """Verified compressed Stratus bundle containing all full lesson JSON for a course."""\n    __tablename__ = "course_content_bundles"\n    __table_args__ = (Index("ix_course_content_bundles_status", "object_status"),)\n    course_id: Mapped[object] = mapped_column(\n        Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True\n    )\n    storage_provider: Mapped[str] = mapped_column(String(32), default="catalyst_stratus", nullable=False)\n    storage_bucket: Mapped[str] = mapped_column(String(120), nullable=False)\n    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)\n    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)\n    compressed_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)\n    raw_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)\n    lesson_count: Mapped[int] = mapped_column(Integer, nullable=False)\n    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)\n    object_status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)\n    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)\n    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)\n'''
        replace_once(targets["models"], "\n\nclass Lesson(Base):\n", model_class + "\n\nclass Lesson(Base):\n", label="model Lesson anchor")

        # Main API: hydrate full lesson JSON from Stratus for detail and knowledge-check routes.
        replace_once(
            targets["main"],
            "\napp = FastAPI(\n",
            "\nfrom .storage.course_content import LessonContentUnavailable, load_lesson_document\n\napp = FastAPI(\n",
            label="main FastAPI anchor",
        )
        replace_in_function(
            targets["main"],
            "get_published_lesson_content(",
            "    stored = lesson.content or {}\n",
            "    try:\n        stored = load_lesson_document(db, lesson)\n    except LessonContentUnavailable as exc:\n        raise HTTPException(status_code=503, detail=\"Lesson content is temporarily unavailable.\") from exc\n",
            next_marker="\ndef _load_lesson_knowledge_check(",
        )
        replace_once(
            targets["main"],
            "def _load_lesson_knowledge_check(course_slug: str, lesson: Lesson) -> dict[str, Any]:\n",
            "def _load_lesson_knowledge_check(course_slug: str, lesson: Lesson, db: Session) -> dict[str, Any]:\n",
            label="knowledge check function signature",
        )
        replace_in_function(
            targets["main"],
            "_load_lesson_knowledge_check(",
            "    stored = lesson.content or {}\n",
            "    try:\n        stored = load_lesson_document(db, lesson)\n    except LessonContentUnavailable as exc:\n        raise HTTPException(status_code=503, detail=\"Lesson content is temporarily unavailable.\") from exc\n",
            next_marker="\n@app.get(\"/api/courses/{course_slug}/lessons/{lesson_slug}/knowledge-check\")",
        )
        replace_count(
            targets["main"],
            "_load_lesson_knowledge_check(course_slug, lesson)",
            "_load_lesson_knowledge_check(course_slug, lesson, db)",
            expected=2,
            label="knowledge check callers",
        )

        # Importer: when explicitly configured, publish the complete course bundle before commit.
        replace_once(
            targets["importer"],
            "from app.models import Course, Module, Lesson, Exercise\n",
            "from app.models import Course, Module, Lesson, Exercise\n"
            "from app.config import settings\n"
            "from app.storage import get_catalyst_storage\n"
            "from app.storage.course_content import publish_course_bundle\n",
            label="importer model import",
        )
        replace_once(
            targets["importer"],
            "    db.flush()\n    return course\n\n\ndef import_course_transaction",
            "    db.flush()\n    if settings.lesson_content_storage_provider.strip().lower() == \"catalyst_stratus\":\n"
            "        storage = get_catalyst_storage()\n"
            "        if storage is None:\n"
            "            raise RuntimeError(\"LESSON_CONTENT_STORAGE_PROVIDER=catalyst_stratus but Catalyst is not configured.\")\n"
            "        # Upload and verify before commit; all lesson rows in the course are bundled together.\n"
            "        publish_course_bundle(db, course, storage, externalize=True)\n"
            "    return course\n\n\ndef import_course_transaction",
            label="importer course loop",
        )
        replace_once(
            targets["migration_test"],
            '"courses", "course_modules", "lessons",',
            '"courses", "course_content_bundles", "course_modules", "lessons",',
            label="migration required table set",
        )
        replace_once(
            targets["migration_test"],
            'revisions[0] != "0010_catalyst_stratus"',
            'revisions[0] != "0011_course_content_bundles"',
            label="migration head revision assertion",
        )
        replace_once(
            targets["migration_test"],
            'FAIL: unexpected migration state: {revisions!r}',
            'FAIL: unexpected migration state: {revisions!r}',
            label="migration state message anchor",
        )
        replace_once(
            targets["migration_test"],
            'PASS migration state has one 0010 head, Catalyst archive metadata, and all existing auth/review/privacy/practical/plan-usage/snippet/support/mock-assessment tables after repeated upgrades',
            'PASS migration state has one 0011 head, Catalyst archive metadata, course content bundles, and all existing auth/review/privacy/practical/plan-usage/snippet/support/mock-assessment tables after repeated upgrades',
            label="migration repeatability pass message",
        )

        replace_once(
            targets["env"],
            "PORTFOLIO_STORAGE_PROVIDER=database\n",
            "PORTFOLIO_STORAGE_PROVIDER=database\n"
            "# Course lesson JSON is stored in PostgreSQL until the verified Stratus course-bundle migration is complete.\n"
            "LESSON_CONTENT_STORAGE_PROVIDER=database\n",
            label="env portfolio variable",
        )

        # Copy additive files from the package into the backend.
        package_backend = package / "backend"
        for relative in (
            "app/storage/course_content.py",
            "alembic/versions/0011_course_content_bundles.py",
            "scripts/migrate_lesson_content_to_stratus.py",
            "scripts/run_catalyst_full_storage_migration.py",
            "scripts/test_course_content_bundle.py",
            "docs/COURSE_CONTENT_STRATUS.md",
        ):
            source = package_backend / relative
            destination = backend / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    except Exception:
        # Restore patched existing files if any source-edit step fails.
        for path in edit_paths:
            backup = backup_root / path.relative_to(root)
            if backup.exists():
                shutil.copy2(backup, path)
        # Remove files added by this installer to leave a clean retry state.
        for relative in (
            "app/storage/course_content.py",
            "alembic/versions/0011_course_content_bundles.py",
            "scripts/migrate_lesson_content_to_stratus.py",
            "scripts/run_catalyst_full_storage_migration.py",
            "scripts/test_course_content_bundle.py",
            "docs/COURSE_CONTENT_STRATUS.md",
        ):
            target = backend / relative
            if target.exists():
                target.unlink()
        raise

    print(f"Course-content storage patch applied. Backup: {backup_root}")
    print("Changed existing files: app/config.py, app/models.py, app/main.py, scripts/import_course_files.py, scripts/test_migration_repeatability.py, .env.example")
    print("Added: course content bundle service, Alembic 0011, lesson migration, full migration runner, tests and docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
