"""Small, self-cleaning Stratus smoke test shared by CLI and temporary API diagnostics."""
from __future__ import annotations

import hashlib
import io
import logging
import time
from uuid import uuid4


logger = logging.getLogger(__name__)

_PAYLOAD = (
    b"CodeLeaf temporary Catalyst Stratus connectivity diagnostic. "
    b"This object contains no student or portfolio data.\n"
)
CLEANUP_CONFIRMATION_TIMEOUT_SECONDS = 15.0
CLEANUP_POLL_INTERVAL_SECONDS = 0.5

_CHECK_NAMES = (
    "upload",
    "object_exists",
    "metadata",
    "range_download",
    "sha256",
    "cleanup",
)


def run_stratus_smoke_test(storage, *, key_prefix: str = "smoke-tests/local") -> dict:
    """Exercise one temporary object and always try to remove it.

    No listing or portfolio lookup is performed. ``key_prefix`` is supplied only
    by trusted callers (the Render API uses ``smoke-tests/render``).
    """
    safe_prefix = key_prefix.strip("/")
    allowed_prefix_characters = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-/"
    )
    if (
        not safe_prefix
        or any(part in {"", ".", ".."} for part in safe_prefix.split("/"))
        or any(char not in allowed_prefix_characters for char in safe_prefix)
    ):
        raise ValueError("Invalid smoke-test key prefix.")

    key = f"{safe_prefix}/{uuid4().hex}.txt"
    expected_checksum = hashlib.sha256(_PAYLOAD).hexdigest()
    checks = {name: "FAIL" for name in _CHECK_NAMES}
    upload_attempted = False
    stored = None

    try:
        upload_attempted = True
        try:
            stored = storage.upload_stream(
                key,
                io.BytesIO(_PAYLOAD),
                expected_size=len(_PAYLOAD),
            )
            checks["upload"] = "PASS"
        except Exception:
            # Keep the response deliberately free of SDK messages and credentials.
            stored = None

        if stored is not None:
            try:
                checks["object_exists"] = (
                    "PASS" if storage.object_exists(key) else "FAIL"
                )
            except Exception:
                checks["object_exists"] = "FAIL"

            try:
                metadata = storage.object_metadata(key)
                checks["metadata"] = (
                    "PASS"
                    if isinstance(metadata, dict)
                    and int(metadata.get("size") or -1) == len(_PAYLOAD)
                    else "FAIL"
                )
            except Exception:
                checks["metadata"] = "FAIL"

            range_start = 4
            range_end = min(len(_PAYLOAD) - 1, 27)
            try:
                ranged = storage.download_range(key, range_start, range_end)
                expected_range = _PAYLOAD[range_start : range_end + 1]
                checks["range_download"] = (
                    "PASS" if bytes(ranged) == expected_range else "FAIL"
                )
            except Exception:
                checks["range_download"] = "FAIL"

            try:
                remote_checksum = storage.checksum_object(key)
                checks["sha256"] = (
                    "PASS"
                    if remote_checksum == expected_checksum
                    and getattr(stored, "checksum_sha256", None) == expected_checksum
                    else "FAIL"
                )
            except Exception:
                checks["sha256"] = "FAIL"
    finally:
        # Check first because Catalyst may reject deletion of a non-existent key.
        # If an upload partially created an object before failing, it is deleted here.
        # Stratus deletion can take a short time to become visible to HEAD checks, so
        # confirm absence with bounded polling instead of checking immediately once.
        if upload_attempted:
            try:
                if storage.object_exists(key):
                    delete_result = storage.delete_object(key)
                    if delete_result is False:
                        raise RuntimeError("Storage adapter did not confirm deletion.")

                deadline = time.monotonic() + CLEANUP_CONFIRMATION_TIMEOUT_SECONDS
                while True:
                    if not storage.object_exists(key):
                        checks["cleanup"] = "PASS"
                        break

                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        checks["cleanup"] = "FAIL"
                        logger.warning(
                            "Catalyst temporary smoke-test deletion was not confirmed "
                            "within %.1f seconds.",
                            CLEANUP_CONFIRMATION_TIMEOUT_SECONDS,
                        )
                        break
                    time.sleep(min(CLEANUP_POLL_INTERVAL_SECONDS, remaining))
            except Exception as exc:
                checks["cleanup"] = "FAIL"
                # Do not log exception text: SDK errors can contain URLs or request data.
                logger.warning(
                    "Catalyst temporary smoke-test cleanup failed (%s).",
                    type(exc).__name__,
                )

    return {
        "status": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL",
        "checks": checks,
    }
