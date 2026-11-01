"""Temporary, token-protected production diagnostic routes.

Remove this router and its registration after the Catalyst production check.
"""
from __future__ import annotations

import hmac

from fastapi import APIRouter, HTTPException, Request

from .config import settings
from .storage import get_catalyst_storage
from .storage.catalyst_smoke_test import run_stratus_smoke_test

router = APIRouter(prefix="/api/diagnostics", tags=["temporary diagnostics"])

EXPECTED_BUCKET = "codeleaf-project-archives-prod-8392"
EXPECTED_ACCOUNTS_URL = "https://accounts.zoho.in"
EXPECTED_API_URL = "https://api.catalyst.zoho.in"
EXPECTED_STRATUS_SUFFIX = ".zohostratus.in"
TOKEN_HEADER = "X-Catalyst-Diagnostic-Token"


def _token_matches(provided_token: str | None) -> bool:
    configured = settings.catalyst_diagnostic_token
    expected_token = configured.get_secret_value() if configured else ""
    if not provided_token or len(expected_token) < 32:
        return False
    try:
        return hmac.compare_digest(
            provided_token.encode("utf-8"), expected_token.encode("utf-8")
        )
    except (TypeError, UnicodeError):
        return False


def _is_production_configuration() -> bool:
    return (
        settings.catalyst_environment.strip().casefold() == "production"
        and (settings.catalyst_stratus_bucket or "").strip() == EXPECTED_BUCKET
        and settings.catalyst_accounts_url.strip().rstrip("/").casefold()
        == EXPECTED_ACCOUNTS_URL
        and settings.catalyst_project_domain.strip().rstrip("/").casefold()
        == EXPECTED_API_URL
        and settings.catalyst_stratus_resource_suffix.strip().casefold()
        == EXPECTED_STRATUS_SUFFIX
    )


def _portfolio_storage_is_safe() -> bool:
    return (
        settings.portfolio_storage_provider.strip().casefold() == "database"
        and settings.catalyst_stratus_enabled is False
    )


@router.post("/catalyst-stratus")
def run_catalyst_production_diagnostic(request: Request) -> dict:
    """Test one isolated object in the configured Production Stratus bucket."""
    provided_token = request.headers.get(TOKEN_HEADER)
    if not _token_matches(provided_token):
        # Deliberately indistinguishable from a missing route; never echo or log the token.
        raise HTTPException(status_code=404, detail="Not found.")

    checks: dict[str, str] = {
        "production_configuration": (
            "PASS" if _is_production_configuration() else "FAIL"
        ),
        "portfolio_storage_safety": (
            "PASS" if _portfolio_storage_is_safe() else "FAIL"
        ),
    }

    # Fail closed. The direct adapter getter is intentional: get_active_storage()
    # must continue returning None while PostgreSQL remains the portfolio provider.
    if all(value == "PASS" for value in checks.values()):
        storage = get_catalyst_storage()
        if storage is None:
            checks["catalyst_adapter_configured"] = "FAIL"
        else:
            checks["catalyst_adapter_configured"] = "PASS"
            smoke_result = run_stratus_smoke_test(
                storage, key_prefix="smoke-tests/render"
            )
            checks.update(smoke_result["checks"])

    overall = (
        "PASS"
        if checks and all(value == "PASS" for value in checks.values())
        else "FAIL"
    )
    return {"status": overall, "checks": checks}
