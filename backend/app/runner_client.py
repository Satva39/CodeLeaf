"""Authenticated server-to-server client for the separate CodeLeaf Runner.

The shared service token is used only by this backend module. No frontend code
or API response receives the token or Runner base URL.
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class RunnerServiceError(RuntimeError):
    """A safe-to-handle Runner transport, status, or payload failure."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def runner_service_configured() -> bool:
    return bool(
        (settings.runner_service_url or "").strip()
        and (settings.runner_service_token or "").strip()
    )


def jdoodle_fallback_configured() -> bool:
    return bool(
        settings.runner_jdoodle_fallback_enabled
        and (settings.jdoodle_client_id or "").strip()
        and (settings.jdoodle_client_secret or "").strip()
    )


async def runner_request_json(
    method: str,
    path: str,
    *,
    user_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call the private Runner API and return a validated JSON object.

    Redirects are deliberately disabled so the service token cannot be forwarded
    to an unexpected host. Error messages never include request headers, URLs,
    response bodies, or secrets.
    """
    base_url = (settings.runner_service_url or "").strip().rstrip("/")
    token = (settings.runner_service_token or "").strip()
    if not base_url or not token:
        raise RunnerServiceError("The isolated Runner is not configured.")
    if not path.startswith("/v1/") or ".." in path or "?" in path or "#" in path:
        raise RunnerServiceError("The requested Runner endpoint is invalid.")

    headers = {"X-Runner-Key": token}
    if user_id is not None:
        headers["X-CodeLeaf-User"] = str(user_id)

    try:
        timeout = float(settings.runner_service_timeout_seconds)
        request_options: dict[str, Any] = {}
        if payload is not None:
            request_options["json"] = payload
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.request(
                method.upper(),
                f"{base_url}{path}",
                headers=headers,
                **request_options,
            )
    except httpx.HTTPError as exc:
        raise RunnerServiceError("The isolated Runner could not be reached.") from exc

    if response.status_code < 200 or response.status_code >= 300:
        raise RunnerServiceError(
            "The isolated Runner returned an unsuccessful response.",
            status_code=response.status_code,
        )

    try:
        data = response.json()
    except (ValueError, TypeError) as exc:
        raise RunnerServiceError("The isolated Runner returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise RunnerServiceError("The isolated Runner returned an invalid response shape.")
    return data
