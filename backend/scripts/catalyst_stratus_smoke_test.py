"""Real Catalyst development-bucket smoke test using one temporary test object only.

This script is intentionally separate from mocked tests and never reads learner rows.
Run it only against a dedicated Catalyst test bucket/environment.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage import get_catalyst_storage  # noqa: E402
from app.storage.catalyst_smoke_test import run_stratus_smoke_test  # noqa: E402


def main() -> int:
    storage = get_catalyst_storage()
    if storage is None:
        print("Catalyst is not configured. Check the server-only CATALYST_* settings.", file=sys.stderr)
        return 2

    report = run_stratus_smoke_test(storage, key_prefix="smoke-tests/local")
    for name, result in report["checks"].items():
        print(f"{name}: {result}")
    print(f"Catalyst Stratus smoke test: {report['status']}")
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
