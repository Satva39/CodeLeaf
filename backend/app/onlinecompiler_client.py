"""Private OnlineCompiler.io API adapter.

All credentials and provider HTTP traffic remain inside the backend. Error messages
are intentionally generic: neither request bodies nor credentials are logged or
returned to callers.
"""
from __future__ import annotations

import base64
import binascii
import re
from typing import Any
from urllib.parse import urlsplit

import httpx

from .config import settings


# Verified against OnlineCompiler's live compiler catalogue (GET /api/compilers/)
# and https://onlinecompiler.io/docs/compilers. These keys are CodeLeaf language
# keys, not user-controlled provider identifiers. Frameworks without an actual
# OnlineCompiler runtime remain on their existing provider.
COMPILER_BY_LANGUAGE = {
    "python": "python-3.14",
    "javascript": "nodejs-24",
    "typescript": "typescript-deno",
    "c": "gcc-15",
    "cpp": "g++-15",
    "cpp14": "g++-15",  # g++-15 uses GNU C++17 by default (C++14-compatible)
    "cpp17": "g++-15",
    "cpp20": "g++-15-cpp20",
    "java": "openjdk-25",
    "csharp": "dotnet-csharp-10",
    "fsharp": "dotnet-fsharp-10",
    "go": "go-1.26",
    "rust": "rust-1.93",
    "php": "php-8.5",
    "ruby": "ruby-4.0",
    "haskell": "haskell-9.12",
    "bash": "bash-5.2",
    "fortran": "gfortran-15",
    "vbnet": "dotnet-vbnet-10",
    "kotlin": "kotlin-2.4",
    "r": "r-4.6",
    "swift": "swift-6.4",
    "cobol": "gnucobol-3.2",
    "perl": "perl-5.44",
    "julia": "julia-1.13",
    "pascal": "fpc-3.2",
    "octave": "octave-11",
    "nasm": "nasm-3",
    "assembler-nasm": "nasm-3",
    "lua": "lua-5.5",
    "ocaml": "ocaml-5.4",
    "clisp": "sbcl-2.6",
    "erlang": "erlang-29",
    "elixir": "elixir-1.20",
    "prolog": "swipl-10",
    "d": "ldc-1.43",
    "freebasic": "fbc-1.10",
    "dart": "dart-3.13",
    "clojure": "clojure-1.12",
    "groovy": "groovy-6.0",
    "scala": "scala-3.10",
    "zig": "zig-0.17",
    "nim": "nim-2.2",
    "crystal": "crystal-1.22",
    "ada": "gnat-15",
    "powershell": "powershell-7.6",
    "racket": "racket-9.3",
    "objectivec": "clang-objc-21",
    # Generic SQL workspaces use the provider SQLite 3 runtime. DuckDB is explicit.
    # MySQL and PostgreSQL remain dedicated database-engine workflows.
    "sql": "sqlite-3",
    "sqlite": "sqlite-3",
    "duckdb": "duckdb-1.5",
}

# CodeLeaf course aliases or compiler variants which should use an OnlineCompiler
# runtime. Kept separate so course-facing labels can be reported accurately while
# resolving to a pinned compiler id.
COMPILER_LANGUAGE_ALIASES = {
    "py": "python-3.14",
    "python3": "python-3.14",
    "js": "nodejs-24",
    "node": "nodejs-24",
    "nodejs": "nodejs-24",
    "node.js": "nodejs-24",
    "ts": "typescript-deno",
    "deno": "typescript-deno",
    "c++": "g++-15",
    "c++14": "g++-15",
    "c++17": "g++-15",
    "c++20": "g++-15-cpp20",
    "c#": "dotnet-csharp-10",
    "cs": "dotnet-csharp-10",
    "f#": "dotnet-fsharp-10",
    "vb.net": "dotnet-vbnet-10",
    "vb": "dotnet-vbnet-10",
    "visualbasic": "dotnet-vbnet-10",
    "visual-basic": "dotnet-vbnet-10",
    "objective-c": "clang-objc-21",
    "free-basic": "fbc-1.10",
    "sqlite3": "sqlite-3",
    "c99": "gcc-15",
    "nasm-asm": "nasm-3",
    # Data/algorithm course labels execute as Python. pandas uses the provider's
    # dedicated pandas-2 image to retain compatibility with existing lessons.
    "data": "python-3.14",
    "datascience": "python-3.14",
    "data-science": "python-3.14",
    "dsa": "python-3.14",
    "pandas": "python-3.14-pandas2",
    # Data-science course aliases use the base Python 3.14 image, where these
    # exact packages are preinstalled by OnlineCompiler.
    "numpy": "python-3.14",
    "scipy": "python-3.14",
    "scikit-learn": "python-3.14",
    "scikitlearn": "python-3.14",
}

ONLINECOMPILER_LANGUAGE_TO_ID = {**COMPILER_BY_LANGUAGE, **COMPILER_LANGUAGE_ALIASES}

# These names normalize to Python or JavaScript in CodeLeaf's legacy provider
# aliases, but the OnlineCompiler images do not include the framework/runtime
# dependencies needed to execute them faithfully. Keep them on their existing
# configured provider instead of claiming that a plain language image supports
# the framework.
ONLINECOMPILER_UNSUPPORTED_FRAMEWORK_KEYS = {
    "django", "fastapi", "flask", "express", "expressjs", "react", "reactjs",
    "vue", "vuejs", "nextjs", "angular", "angularjs", "pytorch",
    # PyTorch is not included in OnlineCompiler's published Python package set.
    "micropython", "python2", "pypy3", "jython", "bun", "laravel", "spring",
}



class OnlineCompilerError(RuntimeError):
    """Safe provider error with an optional HTTP status for API translation."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def onlinecompiler_configured() -> bool:
    return bool(
        settings.onlinecompiler_enabled
        and (settings.onlinecompiler_api_key or "").strip()
    )


def compiler_for_language(language: str) -> str | None:
    """Resolve a CodeLeaf language key to a fixed, documented compiler id."""
    key = str(language or "").strip().lower().replace("_", "-")
    if key in ONLINECOMPILER_UNSUPPORTED_FRAMEWORK_KEYS:
        return None
    direct = ONLINECOMPILER_LANGUAGE_TO_ID.get(key)
    if direct:
        return direct
    # Reuse CodeLeaf's existing alias canonicalizer for names such as C++, C#,
    # PostgreSQL, and course slugs. Only mapped compiler ids can be returned.
    from .jdoodle_runner import normalize_language_key
    canonical = normalize_language_key(key)
    return ONLINECOMPILER_LANGUAGE_TO_ID.get(canonical)


def _base_url() -> str:
    value = (settings.onlinecompiler_base_url or "https://api.onlinecompiler.io").strip().rstrip("/")
    parsed = urlsplit(value)
    local_development = settings.app_env.strip().lower() not in {"production", "prod"} and parsed.hostname in {
        "localhost", "127.0.0.1", "::1"
    }
    if parsed.scheme != "https" and not (local_development and parsed.scheme == "http"):
        raise OnlineCompilerError("OnlineCompiler is not configured with a secure API URL.")
    if not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OnlineCompilerError("OnlineCompiler is not configured with a valid API URL.")
    return value


def _auth_headers() -> dict[str, str]:
    key = (settings.onlinecompiler_api_key or "").strip()
    if not settings.onlinecompiler_enabled or not key:
        raise OnlineCompilerError("OnlineCompiler is not enabled or configured.")
    return {"Authorization": key, "Content-Type": "application/json"}


def _request_timeout() -> float:
    return float(settings.onlinecompiler_timeout_seconds)


def _compiler_ids(payload: Any) -> set[str]:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("compilers") or payload.get("items") or payload.get("languages") or []
    else:
        return set()
    result: set[str] = set()
    if not isinstance(items, list):
        return result
    for item in items:
        if isinstance(item, str):
            candidate = item
        elif isinstance(item, dict):
            candidate = item.get("id") or item.get("compiler") or item.get("key")
        else:
            candidate = None
        if isinstance(candidate, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._+-]{0,79}", candidate):
            result.add(candidate)
    return result


async def _get_json(client: httpx.AsyncClient, path: str, *, auth: bool = False) -> Any:
    headers = _auth_headers() if auth else {}
    try:
        response = await client.get(f"{_base_url()}{path}", headers=headers)
    except httpx.TimeoutException as exc:
        raise OnlineCompilerError("OnlineCompiler did not respond before the timeout.") from exc
    except httpx.HTTPError as exc:
        raise OnlineCompilerError("OnlineCompiler could not be reached.") from exc
    if response.status_code < 200 or response.status_code >= 300:
        raise OnlineCompilerError(
            "OnlineCompiler returned an unsuccessful response.",
            status_code=response.status_code,
        )
    try:
        return response.json()
    except (ValueError, TypeError) as exc:
        raise OnlineCompilerError("OnlineCompiler returned invalid JSON.") from exc


async def check_onlinecompiler_capabilities() -> dict[str, Any]:
    """Check live compiler registry and service health without revealing account data."""
    configured = onlinecompiler_configured()
    if not configured:
        return {
            "configured": False,
            "reachable": False,
            "available": False,
            "supported_languages": [],
            "compilers": [],
        }

    try:
        timeout = httpx.Timeout(5.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            compilers_payload = await _get_json(client, "/api/compilers/")
            compiler_ids = _compiler_ids(compilers_payload)
            try:
                await _get_json(client, "/api/health/")
                healthy = True
            except OnlineCompilerError as exc:
                healthy = False
                health_status = exc.status_code
            else:
                health_status = 200
            # The registry and health endpoints are public. Validate the private
            # key separately so a stale/invalid key is never reported as usable.
            usage_payload = await _get_json(client, "/api/usage/", auth=True)
            if not isinstance(usage_payload, dict):
                raise OnlineCompilerError("OnlineCompiler returned invalid account usage data.")
    except OnlineCompilerError:
        return {
            "configured": True,
            "reachable": False,
            "available": False,
            "supported_languages": [],
            "compilers": [],
        }

    supported = [
        language for language, compiler in ONLINECOMPILER_LANGUAGE_TO_ID.items()
        if compiler in compiler_ids
    ]
    # A valid key and healthy service are not enough when the account or this
    # particular key has no monthly runs remaining. A null per-key remainder
    # means that the key has no separate cap, per the provider contract.
    monthly_remaining = usage_payload.get("remaining")
    key_usage = usage_payload.get("key")
    key_remaining = key_usage.get("remaining") if isinstance(key_usage, dict) else None
    def has_capacity(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, bool):
            return False
        try:
            return int(value) > 0
        except (TypeError, ValueError):
            return False
    usage_available = has_capacity(monthly_remaining) and has_capacity(key_remaining)
    available = healthy and usage_available and bool(supported)
    return {
        "configured": True,
        "reachable": True,
        "available": available,
        "supported_languages": supported if available else [],
        "compilers": sorted(compiler_ids.intersection(ONLINECOMPILER_LANGUAGE_TO_ID.values())),
        "health_status": health_status,
        "usage_available": usage_available,
    }


def _normalize_output_files(value: Any) -> tuple[list[dict[str, Any]], bool]:
    """Keep output files bounded and safe to return to the learner's browser."""
    if not isinstance(value, list):
        return [], False
    files: list[dict[str, Any]] = []
    total_bytes = 0
    truncated = len(value) > 8
    allowed_mimes = {"image/png", "image/svg+xml", "text/csv", "application/json", "text/plain"}
    for item in value[:8]:
        if not isinstance(item, dict):
            truncated = True
            continue
        name = item.get("name")
        encoded = item.get("content_base64")
        mime = item.get("mime")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", name):
            truncated = True
            continue
        if not isinstance(encoded, str) or len(encoded) > 2_800_000:
            truncated = True
            continue
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            truncated = True
            continue
        declared_size = item.get("size")
        size = len(decoded)
        if isinstance(declared_size, int) and (declared_size < 0 or declared_size != size):
            truncated = True
            continue
        if total_bytes + size > 2_000_000:
            truncated = True
            continue
        total_bytes += size
        files.append({
            "name": name,
            "mime": mime if isinstance(mime, str) and mime in allowed_mimes else "application/octet-stream",
            "size": size,
            "content_base64": encoded,
        })
    return files, truncated


def normalize_run_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize the documented sync response without claiming false success."""
    required = {"output", "error", "status", "exit_code"}
    if not required.issubset(payload):
        raise OnlineCompilerError("OnlineCompiler returned an incomplete execution result.")
    output = payload.get("output")
    error = payload.get("error")
    status_value = payload.get("status")
    exit_code = payload.get("exit_code")
    if not isinstance(output, str) or not isinstance(error, str) or not isinstance(status_value, str):
        raise OnlineCompilerError("OnlineCompiler returned an invalid execution result.")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise OnlineCompilerError("OnlineCompiler returned an invalid exit code.")

    try:
        elapsed_ms = round(float(payload.get("time") or 0) * 1000)
    except (TypeError, ValueError):
        elapsed_ms = None
    output_files, output_files_truncated = _normalize_output_files(payload.get("files"))
    return {
        "provider": "onlinecompiler",
        "stdout": output[:65536],
        "stderr": error[:65536],
        "error": error[:8000] or None,
        "execution_status": status_value[:40],
        "success": status_value.lower() == "success" and exit_code == 0,
        "exit_code": exit_code,
        "signal": payload.get("signal"),
        "truncated": payload.get("truncated") is True,
        "cpu_time": str(payload.get("time"))[:40] if payload.get("time") is not None else None,
        "total_time": str(payload.get("total"))[:40] if payload.get("total") is not None else None,
        "execution_ms": elapsed_ms,
        "memory": str(payload.get("memory"))[:40] if payload.get("memory") is not None else None,
        "files": output_files,
        "files_truncated": payload.get("files_truncated") is True or output_files_truncated,
        "status": "completed",
    }


async def run_code_sync(
    *, language: str, code: str, stdin: str = "", files: list[dict[str, str]] | None = None,
    time_limit: int = 10,
) -> dict[str, Any]:
    compiler = compiler_for_language(language)
    if not compiler:
        raise OnlineCompilerError("OnlineCompiler does not support this language.")
    if not isinstance(code, str) or not code or len(code.encode("utf-8")) > 100_000 or "\x00" in code:
        raise OnlineCompilerError("The source code is invalid or exceeds the provider size limit.")
    if not isinstance(stdin, str) or len(stdin.encode("utf-8")) > 100_000 or "\x00" in stdin:
        raise OnlineCompilerError("Standard input is invalid or exceeds the provider size limit.")
    if not isinstance(time_limit, int) or time_limit < 1 or time_limit > 30:
        raise OnlineCompilerError("The execution time limit must be between 1 and 30 seconds.")

    safe_files: list[dict[str, str]] = []
    total_bytes = 0
    for item in files or []:
        name = item.get("name", "")
        content = item.get("content", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", name):
            raise OnlineCompilerError("An input file name is invalid for OnlineCompiler.")
        lowered_name = name.lower() if isinstance(name, str) else ""
        reserved = {"input", "run.sh", "build", "build.tar", "go-trim.txt"}
        if lowered_name in reserved or lowered_name.split(".", 1)[0] == "code":
            raise OnlineCompilerError("An input file name is reserved by OnlineCompiler.")
        if not isinstance(content, str) or "\x00" in content:
            raise OnlineCompilerError("An input file contains invalid text.")
        total_bytes += len(content.encode("utf-8"))
        safe_files.append({"name": name, "content": content, "encoding": "utf8"})
    if len(safe_files) > 8 or total_bytes > 1_000_000:
        raise OnlineCompilerError("The execution files exceed OnlineCompiler's file limits.")

    request_body: dict[str, Any] = {
        "compiler": compiler,
        "code": code,
        "input": stdin,
        "time_limit": time_limit,
    }
    if safe_files:
        request_body["files"] = safe_files
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_request_timeout(), connect=5.0),
            follow_redirects=False,
        ) as client:
            response = await client.post(
                f"{_base_url()}/api/run-code-sync/",
                headers=_auth_headers(),
                json=request_body,
            )
    except httpx.TimeoutException as exc:
        raise OnlineCompilerError("OnlineCompiler execution timed out. The run was not retried.") from exc
    except httpx.HTTPError as exc:
        raise OnlineCompilerError("OnlineCompiler could not be reached. The run was not retried.") from exc

    if response.status_code < 200 or response.status_code >= 300:
        raise OnlineCompilerError(
            "OnlineCompiler could not accept the execution request.",
            status_code=response.status_code,
        )
    try:
        payload = response.json()
    except (ValueError, TypeError) as exc:
        raise OnlineCompilerError("OnlineCompiler returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise OnlineCompilerError("OnlineCompiler returned an invalid execution result.")
    return normalize_run_result(payload)


async def run_tests(
    *, language: str, code: str, tests: list[dict[str, Any]], checker: str = "trim",
    time_limit: int = 2, stop_on_failure: bool = False, files: list[dict[str, str]] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    compiler = compiler_for_language(language)
    if not compiler:
        raise OnlineCompilerError("OnlineCompiler does not support this language.")
    if not isinstance(code, str) or not code or len(code.encode("utf-8")) > 100_000 or "\x00" in code:
        raise OnlineCompilerError("The source code is invalid or exceeds the provider size limit.")
    if not isinstance(tests, list) or not 1 <= len(tests) <= 8:
        raise OnlineCompilerError("The battle evaluation must contain between one and eight tests.")
    if checker not in {"trim", "exact", "tokens", "float", "rows"}:
        raise OnlineCompilerError("The selected output checker is not supported.")
    if not isinstance(time_limit, int) or time_limit < 1 or time_limit > 30:
        raise OnlineCompilerError("The evaluation time limit must be between 1 and 30 seconds.")

    safe_tests: list[dict[str, Any]] = []
    for test in tests:
        if not isinstance(test, dict):
            raise OnlineCompilerError("A battle test case is invalid.")
        stdin = test.get("input", "")
        expected = test.get("expected_output")
        hidden = test.get("hidden", False)
        if not isinstance(stdin, str) or len(stdin.encode("utf-8")) > 100_000 or "\x00" in stdin:
            raise OnlineCompilerError("A battle test input is invalid.")
        if not isinstance(expected, str) or len(expected.encode("utf-8")) > 65_536 or "\x00" in expected:
            raise OnlineCompilerError("A battle expected output is invalid.")
        if not isinstance(hidden, bool):
            raise OnlineCompilerError("A battle test visibility flag is invalid.")
        safe_tests.append({"input": stdin, "expected_output": expected, "hidden": hidden})

    body: dict[str, Any] = {
        "compiler": compiler,
        "code": code,
        "tests": safe_tests,
        "checker": checker,
        "scoring": "all_or_nothing",
        "time_limit": time_limit,
        "stop_on_failure": stop_on_failure,
    }
    if idempotency_key:
        body["external_ref"] = re.sub(r"[^A-Za-z0-9_.:-]", "-", idempotency_key)[:200]

    headers = _auth_headers()
    if idempotency_key:
        headers["Idempotency-Key"] = re.sub(r"[^\x20-\x7E]", "-", idempotency_key)[:100]
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_request_timeout(), connect=5.0),
            follow_redirects=False,
        ) as client:
            response = await client.post(
                f"{_base_url()}/api/run-tests/",
                headers=headers,
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise OnlineCompilerError("OnlineCompiler battle evaluation timed out. The submission was not retried.") from exc
    except httpx.HTTPError as exc:
        raise OnlineCompilerError("OnlineCompiler could not be reached. The submission was not retried.") from exc
    if response.status_code < 200 or response.status_code >= 300:
        raise OnlineCompilerError(
            "OnlineCompiler could not accept the battle evaluation.",
            status_code=response.status_code,
        )
    try:
        payload = response.json()
    except (ValueError, TypeError) as exc:
        raise OnlineCompilerError("OnlineCompiler returned invalid battle evaluation data.") from exc
    if not isinstance(payload, dict):
        raise OnlineCompilerError("OnlineCompiler returned an invalid battle evaluation result.")
    return payload


async def fetch_usage() -> dict[str, Any]:
    """Return provider usage to backend callers only; do not expose it to learners."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0), follow_redirects=False) as client:
        payload = await _get_json(client, "/api/usage/", auth=True)
    if not isinstance(payload, dict):
        raise OnlineCompilerError("OnlineCompiler returned invalid usage information.")
    return payload
