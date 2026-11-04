"""Verify CodeLeaf's configured connection to the separate CodeLeaf Runner.

Run from the backend directory after configuring RUNNER_SERVICE_URL and
RUNNER_SERVICE_TOKEN. The default mode is read-only. --execute-smoke submits
one harmless Python print job and polls the result through the authenticated
Runner API. The service token is never printed.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Make `app` importable when this file is launched as `python scripts/...`
# from the backend directory on Windows or Linux.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.runner_client import (
    RunnerServiceError,
    runner_request_json,
    runner_service_configured,
)

SMOKE_OWNER_ID = "codeleaf-integration-smoke"
SMOKE_SOURCE = 'print("CodeLeaf Runner integration OK")'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute-smoke",
        action="store_true",
        help="submit and poll one harmless Python print job",
    )
    parser.add_argument(
        "--language",
        default="python",
        help="installed language key for the smoke job (default: python)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        choices=range(10, 181),
        metavar="10..180",
        help="maximum time to poll the smoke job (default: 60)",
    )
    return parser.parse_args()


def _available_language(payload: dict[str, Any], requested: str) -> str | None:
    languages = payload.get("languages")
    if not isinstance(languages, list):
        return None
    wanted = requested.strip().lower()
    for item in languages:
        if not isinstance(item, dict) or item.get("available") is not True:
            continue
        aliases = item.get("aliases") if isinstance(item.get("aliases"), list) else []
        names = [item.get("key"), *aliases]
        if any(str(name or "").strip().lower() == wanted for name in names):
            key = str(item.get("key") or "").strip().lower()
            return key or None
    return None


async def _check(args: argparse.Namespace) -> int:
    if not runner_service_configured():
        print("FAIL: RUNNER_SERVICE_URL and RUNNER_SERVICE_TOKEN must both be configured.")
        return 2

    try:
        languages_payload = await runner_request_json("GET", "/v1/languages")
        database_payload = await runner_request_json("GET", "/v1/database/engines")
    except RunnerServiceError as exc:
        print(f"FAIL: Could not query the authenticated Runner API: {exc}")
        if exc.status_code:
            print(f"HTTP status: {exc.status_code}")
        return 2

    languages = languages_payload.get("languages")
    if not isinstance(languages, list):
        print("FAIL: Runner returned an invalid language catalogue.")
        return 2
    available = [
        item for item in languages
        if isinstance(item, dict) and item.get("available") is True
    ]
    engines = database_payload.get("engines")
    if not isinstance(engines, list):
        print("FAIL: Runner returned an invalid database-engine catalogue.")
        return 2
    available_engines = [
        item.get("key") for item in engines
        if isinstance(item, dict) and item.get("available") is True
    ]

    print("PASS: Authenticated CodeLeaf-to-Runner connection")
    print(f"Available runtimes: {len(available)} / {len(languages)}")
    print("Runtime keys: " + (", ".join(str(item.get("key")) for item in available) or "none installed"))
    print("Available database engines: " + (", ".join(str(key) for key in available_engines) or "none"))

    if not args.execute_smoke:
        print("Read-only check complete. No code was submitted.")
        return 0

    language_key = _available_language(languages_payload, args.language)
    if not language_key:
        print(f"FAIL: Requested smoke-test language '{args.language}' is not installed and available.")
        return 3

    try:
        created = await runner_request_json(
            "POST",
            "/v1/jobs",
            user_id=SMOKE_OWNER_ID,
            payload={
                "language": language_key,
                "version": "*",
                "source": SMOKE_SOURCE,
                "stdin": "",
                "args": [],
            },
        )
    except RunnerServiceError as exc:
        print(f"FAIL: Runner rejected the smoke job: {exc}")
        if exc.status_code:
            print(f"HTTP status: {exc.status_code}")
        return 4

    job_id = created.get("job_id")
    if not isinstance(job_id, str) or not job_id:
        print("FAIL: Runner did not return a job_id.")
        return 4
    print(f"Smoke job accepted: {job_id}")

    deadline = asyncio.get_running_loop().time() + args.timeout_seconds
    terminal = {"completed", "failed", "cancelled", "expired"}
    while asyncio.get_running_loop().time() < deadline:
        try:
            job = await runner_request_json(
                "GET",
                f"/v1/jobs/{job_id}",
                user_id=SMOKE_OWNER_ID,
            )
        except RunnerServiceError as exc:
            print(f"FAIL: Could not poll smoke job: {exc}")
            return 5

        state = str(job.get("status") or "unknown")
        if state in terminal:
            result = job.get("result") if isinstance(job.get("result"), dict) else {}
            stdout = str(result.get("stdout") or "")
            stderr = str(result.get("stderr") or "")
            exit_code = result.get("exit_code")
            outcome = str(result.get("outcome") or "")
            print(f"Smoke job status: {state}")
            if stdout:
                print("stdout:")
                print(stdout[:4000])
            if stderr:
                print("stderr:")
                print(stderr[:4000])
            success = (
                state == "completed"
                and (exit_code == 0 or outcome == "success")
                and "CodeLeaf Runner integration OK" in stdout
            )
            if success:
                print("PASS: Python execution, result retrieval, and owner-scoped polling")
                return 0
            print("FAIL: Smoke job reached a terminal state but did not return the expected successful output.")
            return 6
        await asyncio.sleep(1)

    print(f"FAIL: Smoke job did not finish within {args.timeout_seconds} seconds. Job ID: {job_id}")
    print("The job may still be running; use the CodeLeaf API/Playground to check its status.")
    return 7


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(_check(args))
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
