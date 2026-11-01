"""Server-side JDoodle Compiler API adapter for CodeLeaf.

JDoodle runs one isolated program per request and returns its output.  The
adapter deliberately keeps provider credentials on the backend and maps the
CodeLeaf language keys to pinned JDoodle API language/version pairs.
"""
from __future__ import annotations

from typing import Any
import re

import httpx
from fastapi import HTTPException

from .config import settings


JDOODLE_EXECUTE_URL = "https://api.jdoodle.com/v1/execute"

# JDoodle's versionIndex is a zero-based index in its API version list.
# Pin the index rather than silently changing compiler/runtime versions.
JDOODLE_LANGUAGES: dict[str, dict[str, str]] = {
    "ada": {"language": "ada", "versionIndex": "6"},
    "awk": {"language": "awk", "versionIndex": "2"},
    "bash": {"language": "bash", "versionIndex": "6"},
    "bc": {"language": "bc", "versionIndex": "1"},
    "bun": {"language": "bun", "versionIndex": "0"},
    "c": {"language": "c", "versionIndex": "7"},
    "c99": {"language": "c99", "versionIndex": "6"},
    "clisp": {"language": "clisp", "versionIndex": "11"},
    "clojure": {"language": "clojure", "versionIndex": "5"},
    "cobol": {"language": "cobol", "versionIndex": "4"},
    "cpp": {"language": "cpp", "versionIndex": "7"},
    "cpp14": {"language": "cpp14", "versionIndex": "6"},
    "cpp17": {"language": "cpp17", "versionIndex": "3"},
    "cpp20": {"language": "cpp20", "versionIndex": "0"},
    "cpp23": {"language": "cpp23", "versionIndex": "0"},
    "crystal": {"language": "crystal", "versionIndex": "1"},
    "csharp": {"language": "csharp", "versionIndex": "6"},
    "d": {"language": "d", "versionIndex": "4"},
    "dart": {"language": "dart", "versionIndex": "6"},
    "deno": {"language": "deno", "versionIndex": "1"},
    "elixir": {"language": "elixir", "versionIndex": "6"},
    "erlang": {"language": "erlang", "versionIndex": "3"},
    "expressjs": {"language": "expressjs", "versionIndex": "0"},
    "fortran": {"language": "fortran", "versionIndex": "6"},
    "fsharp": {"language": "fsharp", "versionIndex": "3"},
    "go": {"language": "go", "versionIndex": "6"},
    "groovy": {"language": "groovy", "versionIndex": "6"},
    "haskell": {"language": "haskell", "versionIndex": "6"},
    "java": {"language": "java", "versionIndex": "6"},
    "julia": {"language": "julia", "versionIndex": "1"},
    "kotlin": {"language": "kotlin", "versionIndex": "5"},
    "lua": {"language": "lua", "versionIndex": "5"},
    "mongodb": {"language": "mongo", "versionIndex": "0"},
    "mysql": {"language": "mysql", "versionIndex": "0"},
    "nim": {"language": "nim", "versionIndex": "5"},
    "javascript": {"language": "nodejs", "versionIndex": "7"},
    "objectivec": {"language": "objc", "versionIndex": "6"},
    "ocaml": {"language": "ocaml", "versionIndex": "4"},
    "pascal": {"language": "pascal", "versionIndex": "3"},
    "perl": {"language": "perl", "versionIndex": "6"},
    "php": {"language": "php", "versionIndex": "6"},
    "postgresql": {"language": "psql", "versionIndex": "0"},
    "prolog": {"language": "prolog", "versionIndex": "2"},
    "python": {"language": "python3", "versionIndex": "6"},
    "python2": {"language": "python2", "versionIndex": "3"},
    "r": {"language": "r", "versionIndex": "6"},
    "racket": {"language": "racket", "versionIndex": "4"},
    "ruby": {"language": "ruby", "versionIndex": "6"},
    "rust": {"language": "rust", "versionIndex": "6"},
    "scala": {"language": "scala", "versionIndex": "6"},
    "scheme": {"language": "scheme", "versionIndex": "5"},
    "solidity": {"language": "solidity", "versionIndex": "0"},
    "sql": {"language": "sql", "versionIndex": "6"},
    "swift": {"language": "swift", "versionIndex": "6"},
    "tcl": {"language": "tcl", "versionIndex": "6"},
    "typescript": {"language": "typescript", "versionIndex": "1"},
    "vbnet": {"language": "vbn", "versionIndex": "6"},
    "verilog": {"language": "verilog", "versionIndex": "5"},
    "zig": {"language": "zig", "versionIndex": "0"},
    # Additional language adapters available from the same Compiler API.
    "algol": {"language": "algol", "versionIndex": "2"},
    "apl": {"language": "apl", "versionIndex": "1"},
    "assembler-gcc": {"language": "gccasm", "versionIndex": "5"},
    "assembler-nasm": {"language": "nasm", "versionIndex": "6"},
    "assembler-turbo": {"language": "tasm", "versionIndex": "1"},
    "brainfuck": {"language": "brainfuck", "versionIndex": "0"},
    "befunge": {"language": "befunge", "versionIndex": "1"},
    "bhailang": {"language": "bhailang", "versionIndex": "0"},
    "blockly": {"language": "blockly", "versionIndex": "3"},
    "c3": {"language": "c3", "versionIndex": "0"},
    "chicken": {"language": "chicken", "versionIndex": "0"},
    "coffeescript": {"language": "coffeescript", "versionIndex": "5"},
    "cow": {"language": "cow", "versionIndex": "0"},
    "factor": {"language": "factor", "versionIndex": "5"},
    "falcon": {"language": "falcon", "versionIndex": "0"},
    "fantom": {"language": "fantom", "versionIndex": "0"},
    "fasm": {"language": "fasm", "versionIndex": "2"},
    "flex": {"language": "flex", "versionIndex": "0"},
    "forth": {"language": "forth", "versionIndex": "1"},
    "freebasic": {"language": "freebasic", "versionIndex": "4"},
    "guile": {"language": "guile", "versionIndex": "0"},
    "hack": {"language": "hack", "versionIndex": "0"},
    "haxe": {"language": "haxe", "versionIndex": "2"},
    "icon": {"language": "icon", "versionIndex": "2"},
    "intercal": {"language": "intercal", "versionIndex": "0"},
    "jlang": {"language": "jlang", "versionIndex": "0"},
    "jbang": {"language": "jbang", "versionIndex": "0"},
    "jelly": {"language": "jelly", "versionIndex": "0"},
    "jython": {"language": "jython", "versionIndex": "0"},
    "laravel": {"language": "laravel", "versionIndex": "0"},
    "lolcode": {"language": "lolcode", "versionIndex": "0"},
    "micropython": {"language": "micropython", "versionIndex": "0"},
    "moonscript": {"language": "moonscript", "versionIndex": "0"},
    "nemerle": {"language": "nemerle", "versionIndex": "0"},
    "octave": {"language": "octave", "versionIndex": "6"},
    "odin": {"language": "odin", "versionIndex": "0"},
    "mozart": {"language": "mozart", "versionIndex": "0"},
    "pari": {"language": "pari", "versionIndex": "0"},
    "picolisp": {"language": "picolisp", "versionIndex": "6"},
    "pike": {"language": "pike", "versionIndex": "1"},
    "pypy3": {"language": "pypy3", "versionIndex": "0"},
    "raku": {"language": "raku", "versionIndex": "1"},
    "rhino": {"language": "rhino", "versionIndex": "4"},
    "smalltalk": {"language": "smalltalk", "versionIndex": "0"},
    "spidermonkey": {"language": "spidermonkey", "versionIndex": "3"},
    "spring": {"language": "spring", "versionIndex": "0"},
    "unlambda": {"language": "unlambda", "versionIndex": "1"},
    "vlang": {"language": "vlang", "versionIndex": "0"},
    "vala": {"language": "vala", "versionIndex": "0"},
    "whitespace": {"language": "whitespace", "versionIndex": "1"},
    "yabasic": {"language": "yabasic", "versionIndex": "3"},
    "flask": {"language": "flask", "versionIndex": "0"},
    "vue": {"language": "vuejs", "versionIndex": "0"},
    "reactjs": {"language": "reactjs", "versionIndex": "0"},
}

# Course/framework names that are source-language aliases.  These are
# canonicalized before they reach the provider so Python courses such as
# Django/FastAPI and data-science courses use the actual Python runtime.
JDOODLE_LANGUAGE_ALIASES: dict[str, str] = {
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "nodejs": "javascript",
    "node": "javascript",
    "node.js": "javascript",
    "ts": "typescript",
    "c++": "cpp",
    "c#": "csharp",
    "cs": "csharp",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mongo": "mongodb",
    "express": "expressjs",
    "f#": "fsharp",
    "vb.net": "vbnet",
    "data": "python",
    "datascience": "python",
    "data-science": "python",
    "dsa": "python",
    "django": "python",
    "fastapi": "python",
    "numpy": "python",
    "pandas": "python",
    "scipy": "python",
    "pytorch": "python",
    "scikit-learn": "python",
    "scikitlearn": "python",
    "sqlite": "sql",
    "sqlite3": "sql",
    "react": "reactjs",
    "vuejs": "vue",
    "octave-language": "octave",
    "free-basic": "freebasic",
    "objective-c": "objectivec",
    "vb.net": "vbnet",
    "visual-basic": "vbnet",
    "assembler": "assembler-gcc",
    "nasm": "assembler-nasm",
}


def normalize_language_key(language: str) -> str:
    """Return a stable canonical CodeLeaf execution key."""
    key = str(language or "").strip().lower().replace("_", "-")
    return JDOODLE_LANGUAGE_ALIASES.get(key, key)


def get_jdoodle_supported_languages() -> list[str]:
    """Return canonical and course-alias keys accepted by the adapter."""
    return sorted(set(JDOODLE_LANGUAGES) | set(JDOODLE_LANGUAGE_ALIASES))


def is_jdoodle_language_supported(language: str) -> bool:
    return normalize_language_key(language) in JDOODLE_LANGUAGES


# Strict allowlist for common course packages. Package names are inferred from
# Python imports; the browser cannot submit arbitrary package names.
PYTHON_IMPORT_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "sklearn": "scikit-learn",
    "torch": "torch",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "PIL": "Pillow",
    "requests": "requests",
    "bs4": "beautifulsoup4",
    "sympy": "sympy",
    "openpyxl": "openpyxl",
}


def detect_jdoodle_libraries(language: str, source: str) -> list[str]:
    """Infer only allowlisted dependencies from import statements."""
    if normalize_language_key(language) != "python":
        return []
    requested: set[str] = set()
    import_pattern = re.compile(
        r"^\s*(?:from\s+([A-Za-z_][A-Za-z0-9_]*)\s+import|import\s+([A-Za-z_][A-Za-z0-9_]*))",
        re.MULTILINE,
    )
    for match in import_pattern.finditer(source or ""):
        module = match.group(1) or match.group(2)
        package = PYTHON_IMPORT_PACKAGES.get(module)
        if package:
            requested.add(package)
    return sorted(requested)


def normalize_jdoodle_output(data: dict[str, Any], provider_status: int) -> dict[str, Any]:
    """Keep compiler/runtime messages visible as terminal stderr when possible."""
    output = data.get("output")
    provider_error = data.get("error")
    compilation_status = data.get("compilationStatus")

    if isinstance(output, str):
        compile_failed = compilation_status not in (None, 0, "0", "success", "SUCCESS")
        stdout = "" if compile_failed else output
        stderr = output if compile_failed else ""
    else:
        stdout = ""
        stderr = provider_error if isinstance(provider_error, str) else ""

    exit_code = data.get("exitCode")
    try:
        exit_code = int(exit_code) if exit_code is not None else None
    except (TypeError, ValueError):
        exit_code = None

    result: dict[str, Any] = {
        "provider": "jdoodle",
        "stdout": stdout,
        "stderr": stderr,
        "memory": data.get("memory"),
        "cpu_time": data.get("cpuTime"),
        "provider_status_code": provider_status,
    }
    if compilation_status is not None:
        result["compilation_status"] = compilation_status
    if exit_code is not None:
        result["exit_code"] = exit_code
    return result


async def execute_jdoodle(
    *,
    language: str,
    source: str,
    stdin: str = "",
) -> dict[str, Any]:
    """Execute one program through JDoodle and normalize its response."""

    client_id = (settings.jdoodle_client_id or "").strip()
    client_secret = (settings.jdoodle_client_secret or "").strip()

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail="The JDoodle execution provider is not configured on the backend.",
        )

    language_key = normalize_language_key(language)
    language_config = JDOODLE_LANGUAGES.get(language_key)
    if language_config is None:
        raise HTTPException(
            status_code=422,
            detail=f"JDoodle does not currently provide a configured runtime for {language_key}.",
        )

    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "script": source,
        "stdin": stdin,
        "language": language_config["language"],
        "versionIndex": language_config["versionIndex"],
    }
    libraries = detect_jdoodle_libraries(language_key, source)
    if libraries:
        payload["libs"] = libraries

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=7.0)
        ) as client:
            response = await client.post(
                JDOODLE_EXECUTE_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="The execution provider timed out. Try again with a smaller program.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="The execution provider could not be reached.",
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="The execution provider returned an invalid response.",
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=502,
            detail="The execution provider returned an unexpected response.",
        )

    try:
        provider_status = int(data.get("statusCode", response.status_code))
    except (TypeError, ValueError):
        provider_status = response.status_code

    if response.status_code == 429 or provider_status == 429:
        raise HTTPException(
            status_code=429,
            detail="The execution provider's daily API allowance has been exhausted. Try again after its reset.",
        )
    if response.status_code == 401 or provider_status == 401:
        raise HTTPException(
            status_code=503,
            detail="Execution-provider authentication failed. Check the backend credentials.",
        )
    if response.status_code >= 400 or provider_status >= 400:
        message = data.get("error")
        detail = message if isinstance(message, str) and message.strip() else "The execution provider rejected the request."
        raise HTTPException(status_code=502, detail=detail[:500])

    if not isinstance(data.get("output"), str) and not isinstance(data.get("error"), str):
        raise HTTPException(
            status_code=502,
            detail="The execution provider did not return a program result.",
        )

    return normalize_jdoodle_output(data, provider_status)
