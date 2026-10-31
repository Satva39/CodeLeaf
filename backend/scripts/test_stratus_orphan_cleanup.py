"""Unit checks for conservative Stratus orphan candidate parsing."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from cleanup_stratus_orphaned_objects import parse_last_modified, valid_project_key  # noqa: E402

def main() -> None:
    assert valid_project_key("projects/123e4567-e89b-12d3-a456-426614174000/archive.zip")
    assert not valid_project_key("projects/not-a-uuid/archive.zip")
    assert not valid_project_key("projects/123e4567-e89b-12d3-a456-426614174000/other.zip")
    assert parse_last_modified("May 21, 2024 01:00 PM") is not None
    assert parse_last_modified("21/05/2024 13:00") is None
    assert parse_last_modified(None) is None
    print("Stratus orphan cleanup parsing checks passed.")

if __name__ == "__main__":
    main()
