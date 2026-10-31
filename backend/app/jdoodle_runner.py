
"""Server-side JDoodle Compiler API adapter for CodeLeaf.

JDoodle uses synchronous execution. The existing CodeLeaf API will
store its completed result in RunnerJob and expose it through the
existing job-status endpoint.
"""
from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from .config import settings


JDOODLE_EXECUTE_URL = "https://api.jdoodle.com/v1/execute"

# Pin the versions deliberately. JDoodle versionIndex is a zero-based
# position in its language-version list, not the actual version number.
JDOODLE_LANGUAGES = {
    "python": {
        "language": "python3",
        "versionIndex": "5",  # Python 3.11.5
    },
    "javascript": {
        "language": "nodejs",
        "versionIndex": "7",  # NodeJS 25.8.1
    },
}


async def execute_jdoodle(
    *,
    language: str,
    source: str,
    stdin: str = "",
) -> dict[str, Any]:
    """Execute one program and normalize JDoodle's response."""

    client_id = (settings.jdoodle_client_id or "").strip()
    client_secret = (settings.jdoodle_client_secret or "").strip()

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail="The JDoodle execution provider is not configured.",
        )

    language_config = JDOODLE_LANGUAGES.get(language)

    if language_config is None:
        raise HTTPException(
            status_code=422,
            detail="This language is not supported by the configured runner.",
        )

    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "script": source,
        "stdin": stdin,
        "language": language_config["language"],
        "versionIndex": language_config["versionIndex"],
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0)
        ) as client:
            response = await client.post(
                JDOODLE_EXECUTE_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="JDoodle execution timed out. Please try again.",
        ) from exc

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="JDoodle could not be reached.",
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="JDoodle returned an invalid response.",
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=502,
            detail="JDoodle returned an unexpected response.",
        )

    try:
        provider_status = int(
            data.get("statusCode", response.status_code)
        )
    except (TypeError, ValueError):
        provider_status = response.status_code

    if response.status_code == 429 or provider_status == 429:
        raise HTTPException(
            status_code=429,
            detail=(
                "JDoodle's daily execution allowance is exhausted. "
                "Please try again after its daily reset."
            ),
        )

    if response.status_code == 401 or provider_status == 401:
        raise HTTPException(
            status_code=503,
            detail="JDoodle authentication failed. Check the backend credentials.",
        )

    if response.status_code >= 400 or provider_status >= 400:
        raise HTTPException(
            status_code=502,
            detail="JDoodle rejected the execution request.",
        )

    output = data.get("output")

    # JDoodle can return an error field instead of output when the
    # API request itself fails. Compiler messages in output are
    # preserved for the learner to inspect.
    if not isinstance(output, str):
        raise HTTPException(
            status_code=502,
            detail="JDoodle did not return program output.",
        )

    return {
        "provider": "jdoodle",
        "stdout": output,
        "stderr": "",
        "memory": data.get("memory"),
        "cpu_time": data.get("cpuTime"),
        "provider_status_code": provider_status,
    }
