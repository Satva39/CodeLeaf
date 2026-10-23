"""Verify generated CodeLeaf native diagram JSON files exist at backend/content paths.
Run from backend/: python scripts/verify_dynamic_diagrams.py
Optional: --course html --asset assets/diagrams/module-01-overview.diagram.json
"""

from __future__ import annotations
import argparse, json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
COURSES_ROOT = BACKEND_ROOT / "content" / "courses"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", help="Limit checking to one course slug")
    parser.add_argument(
        "--asset",
        default="",
        help="Check one relative path under a course assets folder",
    )
    args = parser.parse_args()
    courses = (
        [p for p in sorted(COURSES_ROOT.iterdir()) if p.is_dir()]
        if COURSES_ROOT.is_dir()
        else []
    )
    if args.course:
        courses = [p for p in courses if p.name == args.course]
    checked = found = invalid = 0
    missing = []
    for course in courses:
        if args.asset:
            paths = [course / "assets" / args.asset]
        else:
            paths = (
                sorted((course / "assets").rglob("*.diagram.json"))
                if (course / "assets").exists()
                else []
            )
        if args.asset:
            checked += 1
            if paths[0].is_file():
                found += 1
                try:
                    obj = json.loads(paths[0].read_text(encoding="utf-8"))
                    if (
                        not isinstance(obj, dict)
                        or not isinstance(obj.get("nodes"), list)
                        or not isinstance(obj.get("edges"), list)
                    ):
                        invalid += 1
                        print(f"INVALID model schema: {paths[0]}")
                    else:
                        print(f"OK: {paths[0]}")
                except Exception as exc:
                    invalid += 1
                    print(f"INVALID JSON: {paths[0]} ({exc})")
            else:
                missing.append(str(paths[0]))
        else:
            checked += len(paths)
            for path in paths:
                found += 1
                try:
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    if (
                        not isinstance(obj, dict)
                        or not isinstance(obj.get("nodes"), list)
                        or not isinstance(obj.get("edges"), list)
                    ):
                        invalid += 1
                        print(f"INVALID model schema: {path}")
                except Exception as exc:
                    invalid += 1
                    print(f"INVALID JSON: {path} ({exc})")
    print(f"Diagram models found: {found}; invalid: {invalid}")
    if missing:
        print(f"Missing expected diagrams: {len(missing)}")
        for path in missing[:30]:
            print("  " + path)
    elif args.asset:
        print("Requested diagram asset is present.")
    return 1 if missing or invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
