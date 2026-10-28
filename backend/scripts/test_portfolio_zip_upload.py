"""Regression checks for safe portfolio ZIP validation and archive limits."""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.phase5_routes import _download_project_zip, validate_project_zip  # noqa: E402
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
    files = validate_project_zip(make_zip({"index.html": "<h1>Hello</h1>", "assets/site.css": "body {}"}))
    assert files == ["index.html", "assets/site.css"]

    expect_http_error(lambda: validate_project_zip(b"not a zip"), 400)
    expect_http_error(lambda: validate_project_zip(make_zip({"../escape.txt": "no"})), 400)
    expect_http_error(lambda: validate_project_zip(make_zip({"C:/escape.txt": "no"})), 400)
    expect_http_error(lambda: validate_project_zip(make_zip({})), 400)
    expect_http_error(lambda: validate_project_zip(b"x" * (10 * 1024 * 1024 + 1)), 413)

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
