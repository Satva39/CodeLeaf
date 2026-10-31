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

from app.storage import StorageError, get_catalyst_storage  # noqa: E402


def main() -> int:
    storage = get_catalyst_storage()
    if storage is None:
        print("Catalyst is not configured. Fill the CATALYST_* values in backend/.env.", file=sys.stderr)
        return 2

    key = f"smoke-tests/codeleaf-{uuid4().hex}.txt"
    payload = b"CodeLeaf Catalyst Stratus smoke test. This is a temporary object.\n"
    exit_code = 0
    try:
        stored = storage.upload_stream(key, io.BytesIO(payload), expected_size=len(payload))
        if not storage.object_exists(key):
            raise StorageError("Smoke-test object was not visible after upload.")
        details = storage.object_metadata(key)
        if int(details.get("size") or 0) != len(payload):
            raise StorageError("Smoke-test object size did not match.")
        if storage.download_range(key, 0, len(payload) - 1) != payload:
            raise StorageError("Smoke-test range download did not match.")
        if storage.checksum_object(key) != stored.checksum_sha256:
            raise StorageError("Smoke-test streamed checksum did not match.")
        print("Catalyst Stratus connectivity, upload, metadata, range read and checksum: PASS")
        print(f"Temporary test key: {key}")
    except Exception as exc:
        print(f"Catalyst Stratus smoke test failed: {str(exc)[:300]}", file=sys.stderr)
        exit_code = 1
    finally:
        try:
            storage.delete_object(key)
            print("Temporary smoke-test object cleanup: PASS (delete request accepted)")
        except Exception as exc:
            print(
                "WARNING: temporary smoke-test object could not be deleted; remove this exact test key in Catalyst Console. "
                f"Key: {key}. Reason: {str(exc)[:180]}",
                file=sys.stderr,
            )
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
