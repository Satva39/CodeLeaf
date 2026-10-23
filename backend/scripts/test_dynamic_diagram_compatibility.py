"""Regression tests for safe native diagram resolution and public API serving.

Run from backend/: python scripts/test_dynamic_diagram_compatibility.py
All fixtures and the API database are created under a temporary directory. No
production database or course publication state is read or modified.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(BACKEND_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))

from app.diagram_assets import resolve_dynamic_diagram, validate_dynamic_diagram_model
from app.course_content_validation import _asset_or_dynamic_model
from publish_all_courses import make_plan, validate_lesson_diagram_assets
from validate_course_manifests import resolve_dynamic_diagram as manifest_resolver


def valid_model() -> dict:
    return {
        "renderer": "codeleaf-native-dynamic-diagram",
        "schema_version": 1,
        "title": "HTML introduction",
        "layout": {"kind": "flow", "columns": 2, "rows": 1},
        "nodes": [
            {"id": "browser", "title": "Browser", "sourceTextIndices": [0]},
            {"id": "html", "title": "HTML document", "sourceTextIndices": [1]},
        ],
        "edges": [{"id": "edge-1", "from": "browser", "to": "html", "label": "renders"}],
        "source_text": [
            {"index": 0, "text": "Browser"},
            {"index": 1, "text": "HTML document"},
        ],
        "source_text_count": 2,
        "header_labels": [],
        "annotations": [],
        "metadata_text_indices": [],
        "text_mapping_complete": True,
    }


def expect_value_error(callback, label: str) -> None:
    try:
        callback()
    except ValueError:
        print(f"PASS {label}")
    else:
        raise AssertionError(f"Expected rejection: {label}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="codeleaf-diagram-compat-") as tmp:
        temporary_root = Path(tmp)
        course_dir = temporary_root / "html"
        diagrams_dir = course_dir / "assets" / "diagrams"
        diagrams_dir.mkdir(parents=True)
        model_path = diagrams_dir / "module-01-overview.diagram.json"
        model_path.write_text(json.dumps(valid_model()), encoding="utf-8")

        # The legacy SVG is deliberately absent. Its native paired model is sufficient.
        assert not (diagrams_dir / "module-01-overview.svg").exists()
        legacy = resolve_dynamic_diagram(course_dir, "diagrams/module-01-overview.svg", "test")
        assert legacy == model_path.resolve()
        validate_dynamic_diagram_model(legacy, "test")
        assert manifest_resolver(course_dir, "diagrams/module-01-overview.svg", "test") == legacy
        print("PASS legacy .svg logical path resolves when physical SVG is absent")

        direct = resolve_dynamic_diagram(course_dir, "diagrams/module-01-overview.diagram.json", "test")
        assert direct == model_path.resolve()
        validate_dynamic_diagram_model(direct, "test")
        print("PASS direct .diagram.json path resolves and validates")

        assert _asset_or_dynamic_model(
            course_dir / "assets", "diagrams/module-01-overview.svg",
            course_dir / "assets", "test diagram",
        ) == model_path.resolve()
        assert validate_lesson_diagram_assets(
            course_dir,
            course_dir / "modules" / "lesson.json",
            {"content": {"content_blocks": [{"type": "diagram", "asset_path": "diagrams/module-01-overview.svg"}]}},
        ) == 1
        print("PASS course-content validation and publisher preflight use shared contract")

        for unsafe in (
            "../outside.svg", "/outside.svg", "diagrams\\outside.svg",
            "C:/outside.svg", "diagrams/./outside.svg", "diagrams//outside.svg",
        ):
            expect_value_error(
                lambda unsafe=unsafe: resolve_dynamic_diagram(course_dir, unsafe, "unsafe-test"),
                f"unsafe path rejected: {unsafe!r}",
            )
        expect_value_error(
            lambda: resolve_dynamic_diagram(course_dir, "diagrams/exam-answer-key.json", "extension-test"),
            "unsupported JSON asset extension is rejected",
        )

        expect_value_error(
            lambda: resolve_dynamic_diagram(course_dir, "diagrams/missing.svg", "missing-test"),
            "missing native model is rejected",
        )
        malformed_path = diagrams_dir / "malformed.diagram.json"
        malformed_path.write_text('{"renderer":', encoding="utf-8")
        expect_value_error(
            lambda: validate_dynamic_diagram_model(malformed_path, "malformed-test"),
            "malformed model JSON is rejected",
        )
        invalid_model_path = diagrams_dir / "invalid.diagram.json"
        cases = []
        duplicate = valid_model()
        duplicate["nodes"][1]["id"] = duplicate["nodes"][0]["id"]
        cases.append((duplicate, "duplicate node IDs are rejected"))
        missing_endpoint = valid_model()
        missing_endpoint["edges"][0]["to"] = "not-present"
        cases.append((missing_endpoint, "missing edge endpoints are rejected"))
        incomplete_mapping = valid_model()
        incomplete_mapping["nodes"][1]["sourceTextIndices"] = []
        cases.append((incomplete_mapping, "incomplete original-text mapping is rejected"))
        protected_field = valid_model()
        protected_field["answer_key"] = "must-not-be-public"
        cases.append((protected_field, "valid-looking diagrams with protected extra fields are rejected"))
        object_title = valid_model()
        object_title["title"] = {"answer_key": "must-not-be-public"}
        cases.append((object_title, "non-text titles cannot carry arbitrary nested JSON"))
        for case, label in cases:
            invalid_model_path.write_text(json.dumps(case), encoding="utf-8")
            expect_value_error(
                lambda: validate_dynamic_diagram_model(invalid_model_path, label), label
            )

        # Publisher's plan is a read-only preflight and must not require an SVG file.
        plan_dir = temporary_root / "publisher-course"
        (plan_dir / "assets" / "diagrams").mkdir(parents=True)
        (plan_dir / "modules" / "lessons").mkdir(parents=True)
        (plan_dir / "assets" / "diagrams" / "only-model.diagram.json").write_text(
            json.dumps(valid_model()), encoding="utf-8"
        )
        (plan_dir / "course.json").write_text(json.dumps({
            "course": {"slug": "publisher-course", "title": "Publisher test", "status": "draft"},
            "module_files": ["modules/module.json"],
            "project_files": [], "assessment_files": [],
        }), encoding="utf-8")
        (plan_dir / "modules" / "module.json").write_text(json.dumps({
            "slug": "intro", "title": "Introduction", "status": "draft",
            "lesson_files": ["lessons/lesson.json"],
        }), encoding="utf-8")
        (plan_dir / "modules" / "lessons" / "lesson.json").write_text(json.dumps({
            "slug": "first", "title": "First lesson", "status": "draft",
            "content": {"content_blocks": [{
                "type": "diagram", "asset_path": "diagrams/only-model.svg",
            }]},
        }), encoding="utf-8")
        lesson_bytes = (plan_dir / "modules" / "lessons" / "lesson.json").read_bytes()
        plan = make_plan(plan_dir)
        assert plan.lessons == 1
        assert not (plan_dir / "assets" / "diagrams" / "only-model.svg").exists()
        assert (plan_dir / "modules" / "lessons" / "lesson.json").read_bytes() == lesson_bytes
        print("PASS publisher dry-run preflight accepts model-only asset and performs no writes")

        # API checks use an isolated SQLite database and a separate temporary content root.
        database_path = temporary_root / "diagram-api-test.sqlite"
        os.environ["APP_ENV"] = "test"
        os.environ["JWT_SECRET"] = "diagram-api-test-only-secret-not-for-deployment"
        os.environ["COOKIE_SECURE"] = "false"
        os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
        os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
        from fastapi.testclient import TestClient
        from sqlalchemy import select
        import app.main as main_module
        from app.db import Base, SessionLocal, engine
        from app.models import Course

        api_content_root = temporary_root / "api-content" / "courses"
        api_course = api_content_root / "diagram-test"
        api_diagrams = api_course / "assets" / "diagrams"
        api_diagrams.mkdir(parents=True)
        (api_diagrams / "visible.diagram.json").write_text(json.dumps(valid_model()), encoding="utf-8")
        (api_diagrams / "private-data.json").write_text(
            json.dumps({"answer_key": "must-not-be-public"}), encoding="utf-8"
        )
        protected_model = valid_model()
        protected_model["answer_key"] = "must-not-be-public"
        (api_diagrams / "invalid.diagram.json").write_text(
            json.dumps(protected_model), encoding="utf-8"
        )
        main_module.COURSE_CONTENT_ROOT = api_content_root
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            db.add(Course(
                slug="diagram-test", title="Diagram API test", description="",
                category="Test", level="Beginner", published=True, sort_order=1,
            ))
            db.commit()
        with TestClient(main_module.app) as client:
            response = client.get(
                "/api/courses/diagram-test/assets/diagrams/visible.diagram.json"
            )
            assert response.status_code == 200, response.status_code
            assert response.headers.get("content-type", "").startswith("application/json")
            assert response.json().get("renderer") == "codeleaf-native-dynamic-diagram"
            print("PASS diagram API returns valid model as application/json")
            for path in (
                "/api/courses/diagram-test/assets/diagrams/private-data.json",
                "/api/courses/diagram-test/assets/diagrams/invalid.diagram.json",
            ):
                denied = client.get(path)
                assert denied.status_code == 404, (path, denied.status_code)
            print("PASS diagram API blocks arbitrary JSON and invalid diagram-model files")
        engine.dispose()

    print("All dynamic diagram compatibility tests passed; no production DB/files were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
