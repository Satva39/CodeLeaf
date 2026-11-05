"""Safe tools for Playground data/configuration files and Redis command practice.

The adapters validate, format, or inspect non-executable file formats. Redis
commands run in a bounded, request-local in-memory simulator. Nothing here
launches operating-system processes, builds images, deploys resources, or
contacts external services.
"""
from __future__ import annotations

import csv
import fnmatch
import io
import json
import re
import shlex
import time
import tomllib
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .auth_security import require_user

router = APIRouter()
MAX_SOURCE_BYTES = 65_536
MAX_OUTPUT_CHARS = 65_536
MAX_XML_NODES = 20_000
MAX_XML_DEPTH = 128
MAX_CSV_ROWS = 300
MAX_CSV_COLUMNS = 40

SUPPORTED_TOOLS = {
    "xml", "json", "yaml", "excel", "markdown", "plain", "docker",
    "aws", "githubactions", "git", "toml", "redis",
}


class PlaygroundToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str = Field(min_length=1, max_length=40)
    source: str = Field(min_length=1, max_length=65_536)
    query: str = Field(default="", max_length=256)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.strip().lower().replace("_", "-")

    @field_validator("source", "query")
    @classmethod
    def reject_null_bytes(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Input cannot contain NUL bytes.")
        if len(value.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError("Input exceeds the 64 KB Playground tool limit.")
        return value


class _BoundedSafeLoader(yaml.SafeLoader):
    """Safe YAML loader with an explicit alias budget to avoid expansion bombs."""

    def __init__(self, stream: Any):
        super().__init__(stream)
        self._codeleaf_alias_count = 0
        self._codeleaf_depth = 0

    def compose_node(self, parent: Any, index: Any) -> Any:
        from yaml.events import AliasEvent

        if self.check_event(AliasEvent):
            self._codeleaf_alias_count += 1
            if self._codeleaf_alias_count > 40:
                raise yaml.YAMLError("YAML contains too many aliases (maximum 40).")
        self._codeleaf_depth += 1
        if self._codeleaf_depth > 80:
            raise yaml.YAMLError("YAML nesting is too deep (maximum 80 levels).")
        try:
            return super().compose_node(parent, index)
        finally:
            self._codeleaf_depth -= 1


def _base_result(language: str, started: float, *, success: bool, stdout: str = "", stderr: str = "") -> dict[str, Any]:
    stdout = str(stdout or "")[:MAX_OUTPUT_CHARS]
    stderr = str(stderr or "")[:8_000]
    return {
        "provider": "CodeLeaf Format Tools",
        "language": language,
        "execution_status": "validated" if success else "validation_error",
        "success": bool(success),
        "exit_code": 0 if success else 1,
        "stdout": stdout,
        "stderr": stderr,
        "execution_ms": max(0, int((time.perf_counter() - started) * 1000)),
        "truncated": len(stdout) >= MAX_OUTPUT_CHARS,
    }


def _format_xml(source: str, query: str) -> tuple[bool, str, str]:
    import xml.etree.ElementTree as ET

    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", source, re.IGNORECASE):
        return False, "", "XML document types and entity declarations are disabled for safety."
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        line, column = getattr(exc, "position", (None, None))
        location = f" at line {line}, column {column + 1}" if line is not None and column is not None else ""
        return False, "", f"XML syntax error{location}: {exc}"

    stack = [(root, 1)]
    nodes = 0
    max_depth = 0
    attributes = 0
    text_nodes = 0
    for element, depth in stack:
        nodes += 1
        max_depth = max(max_depth, depth)
        attributes += len(element.attrib)
        if (element.text or "").strip():
            text_nodes += 1
        if nodes > MAX_XML_NODES:
            return False, "", f"XML document exceeds the {MAX_XML_NODES:,}-element safety limit."
        if depth > MAX_XML_DEPTH:
            return False, "", f"XML document exceeds the {MAX_XML_DEPTH}-level nesting limit."
        stack.extend((child, depth + 1) for child in list(element))

    try:
        ET.indent(root, space="  ")
        formatted = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    except (TypeError, ValueError) as exc:
        return False, "", f"XML formatting failed: {exc}"

    lines = [
        "XML validation: PASSED",
        f"Root element: <{root.tag}>",
        f"Elements: {nodes:,} · Attributes: {attributes:,} · Text nodes: {text_nodes:,} · Maximum depth: {max_depth}",
    ]
    if query.strip():
        expression = query.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.*:/@\[\]\(\)=\'\" \-]+", expression):
            return False, "", "XPath contains unsupported characters. Use a simple ElementTree path such as .//product or .//product[@sku='P-101']."
        if expression.startswith("//"):
            expression = "." + expression
        try:
            matches = root.findall(expression)
        except (SyntaxError, TypeError, KeyError) as exc:
            return False, "", f"XPath query is invalid: {exc}"
        lines.extend(["", f"XPath query: {query}", f"Matches: {len(matches)}"])
        for index, item in enumerate(matches[:50], start=1):
            ET.indent(item, space="  ")
            snippet = ET.tostring(item, encoding="unicode", short_empty_elements=True)
            lines.append(f"\nMatch {index}:\n{snippet}")
        if len(matches) > 50:
            lines.append(f"\nOnly the first 50 matches are displayed.")
        if not matches:
            lines.append("No elements matched this query.")
    lines.extend(["", "FORMATTED XML", formatted])
    return True, "\n".join(lines), ""


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"JSON constant {value} is not valid standard JSON.")


def _format_json(source: str) -> tuple[bool, str, str]:
    try:
        value = json.loads(source, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, json.JSONDecodeError):
            return False, "", f"JSON syntax error at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        return False, "", str(exc)
    pretty = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    if isinstance(value, dict):
        details = f"Object with {len(value)} top-level key(s): {', '.join(list(value.keys())[:20])}"
    elif isinstance(value, list):
        details = f"Array with {len(value)} item(s)"
    else:
        details = f"Valid JSON {type(value).__name__} value"
    return True, f"JSON validation: PASSED\n{details}\n\nFORMATTED JSON\n{pretty}", ""


def _format_yaml(source: str, *, language: str) -> tuple[bool, str, str]:
    try:
        value = yaml.load(source, Loader=_BoundedSafeLoader)
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem_mark", None)
        location = f" at line {problem.line + 1}, column {problem.column + 1}" if problem else ""
        return False, "", f"YAML syntax/safety error{location}: {str(exc).splitlines()[0][:500]}"
    except Exception as exc:
        return False, "", f"YAML could not be parsed: {type(exc).__name__}"
    try:
        formatted = yaml.safe_dump(value, allow_unicode=True, sort_keys=False, default_flow_style=False)
    except yaml.YAMLError as exc:
        return False, "", f"YAML formatting failed: {str(exc)[:500]}"

    messages = ["YAML validation: PASSED"]
    if language == "aws":
        if not isinstance(value, dict):
            return False, "", "CloudFormation template must be a YAML or JSON object."
        resources = value.get("Resources")
        if not isinstance(resources, dict):
            messages.append("Warning: CloudFormation templates normally define a Resources mapping.")
        else:
            messages.append(f"CloudFormation resources: {len(resources)}")
        if "AWSTemplateFormatVersion" not in value:
            messages.append("Info: AWSTemplateFormatVersion is optional.")
    elif language == "githubactions":
        if not isinstance(value, dict):
            return False, "", "GitHub Actions workflow must be a YAML object."
        trigger = value.get("on", value.get(True))
        jobs = value.get("jobs")
        if trigger is None:
            return False, "", "GitHub Actions workflow is missing the required 'on' trigger."
        if not isinstance(jobs, dict) or not jobs:
            return False, "", "GitHub Actions workflow must contain a non-empty 'jobs' mapping."
        messages.append(f"Workflow jobs: {len(jobs)}")
    else:
        if isinstance(value, dict):
            messages.append(f"Top-level mapping entries: {len(value)}")
        elif isinstance(value, list):
            messages.append(f"Top-level sequence items: {len(value)}")
        else:
            messages.append(f"Top-level YAML value: {type(value).__name__}")
    return True, "\n".join(messages) + "\n\nFORMATTED YAML\n" + formatted, ""


def _format_csv(source: str) -> tuple[bool, str, str]:
    try:
        sample = source[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(io.StringIO(source), dialect))
    except csv.Error as exc:
        return False, "", f"CSV parsing error: {exc}"
    if not rows:
        return True, "CSV validation: PASSED\nThe file is empty.", ""
    total_data_rows = max(0, len(rows) - 1)
    width = len(rows[0])
    if width > MAX_CSV_COLUMNS:
        return False, "", f"CSV contains {width} columns; the maximum is {MAX_CSV_COLUMNS}."
    inconsistent = [index + 1 for index, row in enumerate(rows) if len(row) != width]
    if inconsistent:
        preview = ", ".join(str(value) for value in inconsistent[:20])
        return False, "", f"CSV rows have inconsistent column counts. Check row(s): {preview}."
    if len(rows) > MAX_CSV_ROWS:
        rows = rows[:MAX_CSV_ROWS]
        truncated_note = f"\nPreview limited to the first {MAX_CSV_ROWS} rows."
    else:
        truncated_note = ""
    headers = rows[0]
    body = rows[1:]
    preview = "\n".join(" | ".join(cell.replace("\n", "\\n") for cell in row) for row in rows[:31])
    return True, (
        f"CSV validation: PASSED\nColumns: {width} · Data rows: {max(0, len(rows) - 1)}"
        f"\nHeaders: {', '.join(headers[:MAX_CSV_COLUMNS])}\n\nTABLE PREVIEW\n{preview}{truncated_note}"
    ), ""


def _format_dockerfile(source: str) -> tuple[bool, str, str]:
    instructions = {
        "ADD", "ARG", "CMD", "COPY", "ENTRYPOINT", "ENV", "EXPOSE", "FROM",
        "HEALTHCHECK", "LABEL", "MAINTAINER", "ONBUILD", "RUN", "SHELL",
        "STOPSIGNAL", "USER", "VOLUME", "WORKDIR",
    }
    logical: list[tuple[int, str]] = []
    pending = ""
    pending_line = 0
    for line_no, raw in enumerate(source.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not pending:
            pending_line = line_no
        pending += (" " if pending else "") + stripped.rstrip("\\").strip()
        if not stripped.endswith("\\"):
            logical.append((pending_line, pending))
            pending = ""
    if pending:
        logical.append((pending_line, pending))
    if not logical:
        return False, "", "Dockerfile is empty."
    errors: list[str] = []
    warnings: list[str] = []
    saw_from = False
    for line_no, instruction in logical:
        parts = instruction.split(None, 1)
        command = parts[0].upper()
        argument = parts[1].strip() if len(parts) > 1 else ""
        if command not in instructions:
            errors.append(f"Line {line_no}: unknown Dockerfile instruction '{parts[0]}'.")
            continue
        if command == "FROM":
            saw_from = True
        if command in {"FROM", "COPY", "ADD", "RUN", "CMD", "ENTRYPOINT"} and not argument:
            errors.append(f"Line {line_no}: {command} requires an argument.")
        if command == "ADD":
            warnings.append(f"Line {line_no}: review ADD carefully; COPY is usually preferable for local files.")
    if not saw_from:
        errors.append("A Dockerfile needs at least one FROM instruction.")
    if errors:
        return False, "", "\n".join(errors + warnings)
    result = ["Dockerfile static validation: PASSED", f"Instructions: {len(logical)}"]
    result.extend(warnings or ["No basic instruction issues found."])
    result.extend(["", "Note: CodeLeaf validates Dockerfile syntax; it does not build images or execute RUN instructions from the Playground."])
    return True, "\n".join(result), ""


def _render_markdown_summary(source: str) -> str:
    headings = []
    in_code = False
    for line in source.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if match:
                headings.append(f"{len(match.group(1))}. {match.group(2)}")
    result = [f"Markdown preview: PASSED · {len(source.splitlines())} line(s)"]
    if headings:
        result.append("Headings:\n" + "\n".join(headings[:50]))
    else:
        result.append("No Markdown headings found.")
    result.extend(["", "DOCUMENT SOURCE", source])
    return "\n".join(result)


def _run_redis_commands(source: str) -> tuple[bool, str, str]:
    """Run a bounded educational Redis-command subset in an ephemeral in-memory store.

    This is deliberately not exposed as a network Redis server. Each request gets
    a fresh store, and commands such as CONFIG, EVAL, MODULE, SHUTDOWN and raw
    networking are not implemented.
    """
    store: dict[str, dict[str, Any]] = {}
    expiries: dict[str, float] = {}
    started = time.monotonic()
    output: list[str] = []
    errors: list[str] = []
    command_count = 0

    def exists(key: str) -> bool:
        expires_at = expiries.get(key)
        if expires_at is not None and expires_at <= time.monotonic():
            store.pop(key, None)
            expiries.pop(key, None)
        return key in store

    def item(key: str, kind: str | None = None) -> dict[str, Any] | None:
        if not exists(key):
            return None
        record = store[key]
        if kind and record["kind"] != kind:
            raise ValueError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return record

    def ensure(key: str, kind: str, initial: Any) -> dict[str, Any]:
        record = item(key)
        if record is None:
            if len(store) >= 1_000:
                raise ValueError("The temporary Redis database has reached its 1,000-key limit.")
            record = {"kind": kind, "value": initial}
            store[key] = record
        elif record["kind"] != kind:
            raise ValueError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return record

    def need(args: list[str], minimum: int, maximum: int | None = None) -> None:
        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            range_text = str(minimum) if maximum == minimum else f"{minimum}..{maximum or 'many'}"
            raise ValueError(f"Wrong number of arguments (expected {range_text}).")

    def integer(value: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError("ERR value is not an integer or out of range") from None

    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        command_count += 1
        if command_count > 400:
            return False, "\n".join(output), "Redis simulator accepts at most 400 commands per run."
        try:
            tokens = shlex.split(line, comments=False, posix=True)
            if not tokens:
                continue
            command, *args = tokens
            command = command.upper()
            result: Any = "OK"

            if command == "PING":
                need(args, 0, 1)
                result = args[0] if args else "PONG"
            elif command == "ECHO":
                need(args, 1, 1)
                result = args[0]
            elif command == "SET":
                need(args, 2)
                key, value, *options = args
                if len(key) > 256:
                    raise ValueError("ERR key name is too long (maximum 256 characters).")
                option_words = [word.upper() for word in options]
                if "NX" in option_words and "XX" in option_words:
                    raise ValueError("ERR NX and XX cannot be used together.")
                if "NX" in option_words and exists(key):
                    result = "(nil)"
                elif "XX" in option_words and not exists(key):
                    result = "(nil)"
                else:
                    expiry = None
                    index = 0
                    while index < len(options):
                        option = option_words[index]
                        if option in {"NX", "XX"}:
                            index += 1
                            continue
                        if option in {"EX", "PX"}:
                            if index + 1 >= len(options):
                                raise ValueError(f"ERR {option} requires a duration.")
                            duration = integer(options[index + 1])
                            if duration <= 0:
                                raise ValueError("ERR expiry must be greater than zero.")
                            expiry = time.monotonic() + (duration if option == "EX" else duration / 1000)
                            index += 2
                            continue
                        raise ValueError(f"ERR unsupported SET option '{options[index]}'.")
                    if key not in store and len(store) >= 1_000:
                        raise ValueError("The temporary Redis database has reached its 1,000-key limit.")
                    store[key] = {"kind": "string", "value": value}
                    if expiry is not None:
                        expiries[key] = expiry
                    else:
                        expiries.pop(key, None)
                    result = "OK"
            elif command in {"GET", "STRLEN"}:
                need(args, 1, 1)
                record = item(args[0], "string")
                if command == "GET":
                    result = record["value"] if record else "(nil)"
                else:
                    result = f"(integer) {len(record['value']) if record else 0}"
            elif command in {"MSET", "MGET"}:
                need(args, 2)
                if command == "MSET":
                    if len(args) % 2:
                        raise ValueError("ERR MSET requires key/value pairs.")
                    new_keys = {args[index] for index in range(0, len(args), 2)} - set(store)
                    if len(store) + len(new_keys) > 1_000:
                        raise ValueError("The temporary Redis database has reached its 1,000-key limit.")
                    if any(len(args[index]) > 256 for index in range(0, len(args), 2)):
                        raise ValueError("ERR key name is too long (maximum 256 characters).")
                    for index in range(0, len(args), 2):
                        store[args[index]] = {"kind": "string", "value": args[index + 1]}
                        expiries.pop(args[index], None)
                    result = "OK"
                else:
                    values = []
                    for key in args:
                        record = item(key, "string")
                        values.append(record["value"] if record else None)
                    result = json.dumps(values, ensure_ascii=False)
            elif command in {"INCR", "DECR", "INCRBY", "DECRBY"}:
                need(args, 1, 2 if command.endswith("BY") else 1)
                key = args[0]
                delta = integer(args[1]) if len(args) > 1 else 1
                if command in {"DECR", "DECRBY"}:
                    delta = -delta
                record = ensure(key, "string", "0")
                value = integer(record["value"]) + delta
                record["value"] = str(value)
                result = f"(integer) {value}"
            elif command == "APPEND":
                need(args, 2, 2)
                record = ensure(args[0], "string", "")
                record["value"] += args[1]
                result = f"(integer) {len(record['value'])}"
            elif command in {"DEL", "UNLINK"}:
                need(args, 1)
                count = 0
                for key in args:
                    if exists(key):
                        store.pop(key, None)
                        expiries.pop(key, None)
                        count += 1
                result = f"(integer) {count}"
            elif command == "EXISTS":
                need(args, 1)
                result = f"(integer) {sum(1 for key in args if exists(key))}"
            elif command == "TYPE":
                need(args, 1, 1)
                record = item(args[0])
                result = record["kind"] if record else "none"
            elif command == "KEYS":
                need(args, 1, 1)
                keys = sorted(key for key in list(store) if exists(key) and fnmatch.fnmatchcase(key, args[0]))
                result = json.dumps(keys[:100], ensure_ascii=False)
            elif command in {"FLUSHDB", "FLUSHALL"}:
                need(args, 0, 0)
                store.clear()
                expiries.clear()
                result = "OK"
            elif command == "EXPIRE":
                need(args, 2, 2)
                duration = integer(args[1])
                if duration < 0:
                    raise ValueError("ERR invalid expire time")
                if exists(args[0]):
                    if duration == 0:
                        store.pop(args[0], None)
                        expiries.pop(args[0], None)
                    else:
                        expiries[args[0]] = time.monotonic() + duration
                    result = "(integer) 1"
                else:
                    result = "(integer) 0"
            elif command in {"TTL", "PTTL"}:
                need(args, 1, 1)
                key = args[0]
                if not exists(key):
                    result = "(integer) -2"
                elif key not in expiries:
                    result = "(integer) -1"
                else:
                    remaining = max(0, expiries[key] - time.monotonic())
                    value = int(remaining * 1000) if command == "PTTL" else int(remaining)
                    result = f"(integer) {value}"
            elif command == "PERSIST":
                need(args, 1, 1)
                if exists(args[0]) and args[0] in expiries:
                    expiries.pop(args[0], None)
                    result = "(integer) 1"
                else:
                    result = "(integer) 0"
            elif command in {"HSET", "HMSET"}:
                need(args, 3)
                if (len(args) - 1) % 2:
                    raise ValueError("ERR HSET requires field/value pairs.")
                record = ensure(args[0], "hash", {})
                added = 0
                for index in range(1, len(args), 2):
                    if args[index] not in record["value"]:
                        added += 1
                    record["value"][args[index]] = args[index + 1]
                result = f"(integer) {added}" if command == "HSET" else "OK"
            elif command in {"HGET", "HEXISTS"}:
                need(args, 2, 2)
                record = item(args[0], "hash")
                present = bool(record and args[1] in record["value"])
                result = (record["value"].get(args[1], "(nil)") if record else "(nil)") if command == "HGET" else f"(integer) {int(present)}"
            elif command in {"HGETALL", "HKEYS", "HVALS", "HLEN"}:
                need(args, 1, 1)
                record = item(args[0], "hash")
                values = record["value"] if record else {}
                if command == "HGETALL":
                    result = json.dumps(values, ensure_ascii=False)
                elif command == "HKEYS":
                    result = json.dumps(list(values), ensure_ascii=False)
                elif command == "HVALS":
                    result = json.dumps(list(values.values()), ensure_ascii=False)
                else:
                    result = f"(integer) {len(values)}"
            elif command == "HDEL":
                need(args, 2)
                record = item(args[0], "hash")
                removed = 0
                if record:
                    for field in args[1:]:
                        if field in record["value"]:
                            del record["value"][field]
                            removed += 1
                    if not record["value"]:
                        store.pop(args[0], None)
                result = f"(integer) {removed}"
            elif command in {"LPUSH", "RPUSH"}:
                need(args, 2)
                record = ensure(args[0], "list", [])
                if command == "LPUSH":
                    for value in args[1:]:
                        record["value"].insert(0, value)
                else:
                    record["value"].extend(args[1:])
                result = f"(integer) {len(record['value'])}"
            elif command in {"LPOP", "RPOP"}:
                need(args, 1, 2)
                record = item(args[0], "list")
                count = integer(args[1]) if len(args) == 2 else 1
                if count < 1:
                    raise ValueError("ERR count must be positive.")
                if not record:
                    result = "(nil)"
                else:
                    values = record["value"]
                    removed = []
                    for _ in range(min(count, len(values))):
                        removed.append(values.pop(0 if command == "LPOP" else -1))
                    if not values:
                        store.pop(args[0], None)
                    result = removed[0] if len(removed) == 1 else json.dumps(removed, ensure_ascii=False)
            elif command in {"LLEN", "LRANGE"}:
                need(args, 1, 3 if command == "LRANGE" else 1)
                record = item(args[0], "list")
                values = record["value"] if record else []
                if command == "LLEN":
                    result = f"(integer) {len(values)}"
                else:
                    start, stop = integer(args[1]), integer(args[2])
                    if start < 0:
                        start = max(0, len(values) + start)
                    if stop < 0:
                        stop = len(values) + stop
                    result = json.dumps(values[start:stop + 1], ensure_ascii=False)
            elif command in {"SADD", "SREM"}:
                need(args, 2)
                record = ensure(args[0], "set", set())
                values = record["value"]
                before = len(values)
                if command == "SADD":
                    values.update(args[1:])
                else:
                    values.difference_update(args[1:])
                result = f"(integer) {abs(len(values) - before)}"
                if not values:
                    store.pop(args[0], None)
            elif command in {"SMEMBERS", "SCARD"}:
                need(args, 1, 1)
                record = item(args[0], "set")
                values = sorted(record["value"]) if record else []
                result = json.dumps(values, ensure_ascii=False) if command == "SMEMBERS" else f"(integer) {len(values)}"
            elif command == "SISMEMBER":
                need(args, 2, 2)
                record = item(args[0], "set")
                result = f"(integer) {int(bool(record and args[1] in record['value']))}"
            else:
                raise ValueError(f"ERR unsupported command '{command}'. The educational runner supports common string, hash, list, set, key and expiry commands.")

            output.append(f"{line_number}> {result}")
        except (ValueError, KeyError, IndexError) as exc:
            errors.append(f"Line {line_number}: {str(exc)}")
    summary = f"Redis command run: {command_count} command(s) · {len(store)} key(s) remaining · ephemeral store"
    stdout = summary + ("\n\n" + "\n".join(output) if output else "")
    stderr = "\n".join(errors)
    return not errors, stdout, stderr


def run_structured_tool(language: str, source: str, query: str = "") -> dict[str, Any]:
    """Validate/inspect a supported non-executable Playground file safely."""
    started = time.perf_counter()
    key = str(language or "").strip().lower().replace("_", "-")
    if key not in SUPPORTED_TOOLS:
        return _base_result(key, started, success=False, stderr="No structured tool is registered for this file type.")
    if not isinstance(source, str) or not source.strip():
        return _base_result(key, started, success=False, stderr="Add content before running this file.")
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES or "\x00" in source:
        return _base_result(key, started, success=False, stderr="Source exceeds the 64 KB structured-tool limit or contains invalid bytes.")

    if key == "redis":
        success, stdout, stderr = _run_redis_commands(source)
        result = _base_result(key, started, success=success, stdout=stdout, stderr=stderr)
        result["provider"] = "CodeLeaf Redis Simulator (ephemeral)"
        result["execution_status"] = "completed" if success else "failed"
        return result
    if key == "xml":
        success, stdout, stderr = _format_xml(source, query)
    elif key == "json":
        success, stdout, stderr = _format_json(source)
    elif key in {"yaml", "aws", "githubactions"}:
        success, stdout, stderr = _format_yaml(source, language=key)
    elif key == "excel":
        success, stdout, stderr = _format_csv(source)
    elif key == "docker":
        success, stdout, stderr = _format_dockerfile(source)
    elif key in {"markdown", "git"}:
        success, stdout, stderr = True, _render_markdown_summary(source), ""
    elif key == "toml":
        try:
            value = tomllib.loads(source)
            stdout = "TOML validation: PASSED\n\nPARSED DATA\n" + json.dumps(value, ensure_ascii=False, indent=2, default=str)
            success, stderr = True, ""
        except tomllib.TOMLDecodeError as exc:
            success, stdout, stderr = False, "", f"TOML syntax error: {exc}"
    else:  # plain text
        success, stdout, stderr = True, source, ""

    return _base_result(key, started, success=success, stdout=stdout, stderr=stderr)


@router.post("/api/playground/tools/run")
async def run_playground_tool(
    body: PlaygroundToolInput,
    _user=Depends(require_user),
) -> dict[str, Any]:
    """Process a data/configuration file without executing arbitrary code."""
    if body.language not in SUPPORTED_TOOLS:
        raise HTTPException(status_code=422, detail="Unsupported Playground tool language.")
    return {"result": run_structured_tool(body.language, body.source, body.query)}
