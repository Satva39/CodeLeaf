"""Validate all local CodeLeaf course files without a database connection."""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.course_content_validation import validate_course_tree  # noqa: E402

CONTENT_ROOT = BACKEND / "content" / "courses"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--course-slug", required=True, help="Course folder name, e.g. html"
    )
    args = parser.parse_args()
    if not args.course_slug or any(
        ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in args.course_slug
    ):
        parser.error(
            "course slug must contain lowercase letters, digits, and hyphens only"
        )
    course_dir = (CONTENT_ROOT / args.course_slug).resolve()
    if CONTENT_ROOT.resolve() not in course_dir.parents:
        parser.error("Invalid course slug/path")
    try:
        result = validate_course_tree(course_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
