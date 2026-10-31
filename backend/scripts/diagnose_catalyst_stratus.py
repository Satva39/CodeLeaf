"""Safe diagnostic for CodeLeaf's Catalyst Stratus SDK initialization.

Run from backend/: python scripts\\diagnose_catalyst_stratus.py
This prints configuration presence and a redacted SDK error only. It does not
upload, download, list, or delete any Stratus objects.
"""
from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.storage.factory import get_catalyst_storage  # noqa: E402


def redact(message: str) -> str:
    secrets = (
        settings.catalyst_client_id,
        settings.catalyst_client_secret,
        settings.catalyst_refresh_token,
        settings.catalyst_project_id,
        settings.catalyst_project_zaid,
        settings.catalyst_stratus_bucket,
    )
    for value in secrets:
        if value:
            message = message.replace(str(value), "[REDACTED]")
    return message[:700]


def main() -> int:
    print("=== CodeLeaf Catalyst Stratus diagnostic ===")

    required = {
        "CATALYST_PROJECT_ID": settings.catalyst_project_id,
        "CATALYST_PROJECT_ZAID": settings.catalyst_project_zaid,
        "CATALYST_CLIENT_ID": settings.catalyst_client_id,
        "CATALYST_CLIENT_SECRET": settings.catalyst_client_secret,
        "CATALYST_REFRESH_TOKEN": settings.catalyst_refresh_token,
        "CATALYST_STRATUS_BUCKET": settings.catalyst_stratus_bucket,
    }
    missing = []
    for name, value in required.items():
        present = bool(value and str(value).strip())
        print(f"{name}: {'SET' if present else 'MISSING'}")
        if not present:
            missing.append(name)

    print(f"CATALYST_ENVIRONMENT: {settings.catalyst_environment}")
    print(f"CATALYST_PROJECT_DOMAIN: {settings.catalyst_project_domain}")
    print(f"PORTFOLIO_STORAGE_PROVIDER: {settings.portfolio_storage_provider}")
    print(f"CATALYST_STRATUS_ENABLED: {settings.catalyst_stratus_enabled}")

    try:
        sdk_version = importlib.metadata.version("zcatalyst-sdk")
        print(f"zcatalyst-sdk version: {sdk_version}")
    except importlib.metadata.PackageNotFoundError:
        print("zcatalyst-sdk: NOT INSTALLED")
        return 2

    if missing:
        print("\nMissing required values. Check backend/.env (do not paste it into chat).")
        return 2

    storage = get_catalyst_storage()
    if storage is None:
        print("\nThe app settings did not produce a configured Catalyst adapter.")
        return 2

    try:
        storage._get_bucket()  # Initialization only; no object operation is performed.
        print("\nCatalyst SDK initialization: PASS")
        print("No objects were uploaded, downloaded, listed, or deleted.")
        return 0
    except Exception as exc:
        cause = exc.__cause__ or exc
        print("\nCatalyst SDK initialization: FAIL")
        print(f"Underlying exception type: {type(cause).__name__}")
        print(f"Redacted detail: {redact(str(cause)) or '(no detail returned)'}")
        print("No objects were uploaded, downloaded, listed, or deleted.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
