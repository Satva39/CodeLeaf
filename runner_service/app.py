"""Minimal isolated code-runner control plane.

This service must run on a dedicated runner node, never in the same security
boundary as the main API. It requires immutable pre-approved runtime images and
uses the Docker CLI with fixed arguments only (no learner-provided commands or
image names). Job data is in-memory and expires on service restart by design.
"""
from __future__ import annotations

import asyncio
import hmac
import os
import re
import shutil
import time
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI(title="CodeLeaf Isolated Runner", version="0.1.0")
SERVICE_KEY = os.getenv("RUNNER_SERVICE_TOKEN", "")
JOB_TIMEOUT_SECONDS = min(8, max(1, int(os.getenv("RUNNER_JOB_TIMEOUT_SECONDS", "4"))))
MAX_OUTPUT_BYTES = 16_000
MAX_CONCURRENT = min(8, max(1, int(os.getenv("RUNNER_MAX_CONCURRENT", "2"))))
MAX_JOBS_PER_MINUTE = min(20, max(1, int(os.getenv("RUNNER_MAX_JOBS_PER_MINUTE", "8"))))
PYTHON_IMAGE = os.getenv("RUNNER_PYTHON_IMAGE", "").strip()
NODE_IMAGE = os.getenv("RUNNER_NODE_IMAGE", "").strip()
IMAGE_REF_RE = re.compile(r"^(?:[A-Za-z0-9._:/-]+@)?sha256:[a-f0-9]{64}$")
JOBS: dict[str, dict] = {}
OWNER_RECENT: dict[str, list[float]] = {}
SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateJob(StrictModel):
    owner_id: str = Field(min_length=8, max_length=80)
    language: Literal["python", "javascript"]
    source: str = Field(min_length=1, max_length=16_000)
    stdin: str = Field(default="", max_length=8_000)

    @field_validator("source", "stdin")
    @classmethod
    def no_null_bytes(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("NUL bytes are not supported")
        return value


def _authorize(runner_key: str, owner_id: str | None = None) -> str | None:
    if not SERVICE_KEY or len(SERVICE_KEY) < 32 or not runner_key or not hmac.compare_digest(runner_key, SERVICE_KEY):
        raise HTTPException(status_code=401, detail="Runner service authentication failed.")
    if owner_id is not None and (not owner_id or len(owner_id) > 80):
        raise HTTPException(status_code=401, detail="Runner owner scope is required.")
    return owner_id


def _image_for(language: str) -> str:
    image = PYTHON_IMAGE if language == "python" else NODE_IMAGE
    if not image or not IMAGE_REF_RE.fullmatch(image):
        raise HTTPException(status_code=503, detail=f"The approved {language} runtime image is not configured as an immutable SHA-256 reference.")
    return image


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public(job: dict) -> dict:
    return {"job_id": job["job_id"], "status": job["status"], "created_at": job["created_at"],
            "updated_at": job["updated_at"], "result": dict(job.get("result") or {})}


async def _docker_remove(container_name: str) -> None:
    if not shutil.which("docker"):
        return
    try:
        proc = await asyncio.create_subprocess_exec("docker", "rm", "-f", container_name,
            stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL)
        await asyncio.wait_for(proc.wait(), timeout=2)
    except (OSError, asyncio.TimeoutError):
        pass


async def _read_limited(stream: asyncio.StreamReader, maximum: int, overflow: asyncio.Event, container_name: str) -> bytes:
    result = bytearray()
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            break
        if len(result) + len(chunk) > maximum:
            result.extend(chunk[: max(0, maximum - len(result))])
            overflow.set()
            await _docker_remove(container_name)
            break
        result.extend(chunk)
    return bytes(result)


def _docker_command(language: str, container_name: str) -> list[str]:
    """Build a fixed execution command; learner source is passed through container stdin."""
    image = _image_for(language)
    command = [
        "docker", "run", "--rm", "--name", container_name, "-i",
        "--network=none", "--read-only", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=64",
        "--memory=128m", "--memory-swap=128m", "--cpus=0.50",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "--user=10001:10001", "--workdir=/tmp", "--ipc=none",
        "--hostname=codeleaf-job", "--pull=never", image,
    ]
    if language == "python":
        wrapper = "import sys,struct; n=struct.unpack('!I',sys.stdin.buffer.read(4))[0]; source=sys.stdin.buffer.read(n).decode('utf-8'); exec(compile(source,'<learner>','exec'))"
        interpreter = ["python", "-I", "-c", wrapper]
    else:
        wrapper = "const fs=require('node:fs');const readExact=(n)=>{const b=Buffer.alloc(n);let o=0;while(o<n){const r=fs.readSync(0,b,o,n-o,null);if(r===0)throw new Error('Truncated runner input');o+=r;}return b;};const n=readExact(4).readUInt32BE(0);const source=readExact(n).toString('utf8');(function(){eval(source);})();"
        interpreter = ["node", "--disable-proto=throw", "--input-type=commonjs", "-e", wrapper]
    return command + interpreter


async def _execute(job: dict, source: str, user_input: str) -> None:
    container_name = f"codeleaf-run-{job['job_id']}"
    job["container_name"] = container_name
    try:
        async with SEMAPHORE:
            if job["status"] == "cancelled":
                return
            _image_for(job["language"])
            if not shutil.which("docker"):
                job["status"] = "failed"
                job["result"] = {"error": "Docker CLI is unavailable on the runner node."}
                job["updated_at"] = _now()
                return
            command = _docker_command(job["language"], container_name)
            job["status"] = "running"
            job["updated_at"] = _now()
            proc = await asyncio.create_subprocess_exec(*command,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            job["process"] = proc
            if proc.stdin is None or proc.stdout is None or proc.stderr is None:
                raise RuntimeError("Runner process streams could not be opened")
            overflow = asyncio.Event()
            stdout_task = asyncio.create_task(_read_limited(proc.stdout, MAX_OUTPUT_BYTES, overflow, container_name))
            stderr_task = asyncio.create_task(_read_limited(proc.stderr, MAX_OUTPUT_BYTES, overflow, container_name))
            job["stdout_task"] = stdout_task
            job["stderr_task"] = stderr_task
            try:
                import struct
                source_bytes = source.encode("utf-8")
                payload = struct.pack("!I", len(source_bytes)) + source_bytes + user_input.encode("utf-8")
                proc.stdin.write(payload)
                await proc.stdin.drain()
                proc.stdin.close()
                await asyncio.wait_for(proc.wait(), timeout=JOB_TIMEOUT_SECONDS)
                stdout, stderr = await asyncio.gather(stdout_task, stderr_task)
            except asyncio.TimeoutError:
                overflow.set()
                # Stop the Docker CLI wait process, then ask the daemon to kill the job container.
                if proc.returncode is None:
                    proc.kill()
                    await proc.wait()
                await _docker_remove(container_name)
                job["status"] = "timeout"
                job["result"] = {"error": f"Execution exceeded the {JOB_TIMEOUT_SECONDS}-second limit."}
                job["updated_at"] = _now()
                return
            if overflow.is_set():
                await _docker_remove(container_name)
                job["status"] = "output_limit"
                job["result"] = {"error": "Output exceeded the per-job limit.", "stdout": stdout.decode("utf-8", "replace"), "stderr": stderr.decode("utf-8", "replace")}
            else:
                code = proc.returncode
                job["status"] = "completed" if code == 0 else "failed"
                job["result"] = {"exit_code": code, "stdout": stdout.decode("utf-8", "replace"), "stderr": stderr.decode("utf-8", "replace")}
            job["updated_at"] = _now()
    except asyncio.CancelledError:
        process = job.get("process")
        if process is not None and process.returncode is None:
            process.kill()
            try:
                await process.wait()
            except (OSError, RuntimeError):
                pass
        await _docker_remove(container_name)
        job["status"] = "cancelled"
        job["result"] = {"message": "Job was cancelled."}
        job["updated_at"] = _now()
        raise
    except HTTPException as exc:
        job["status"] = "failed"
        job["result"] = {"error": str(exc.detail)}
        job["updated_at"] = _now()
    except (OSError, RuntimeError) as exc:
        # Never return host command lines, environment variables, or stack traces.
        await _docker_remove(container_name)
        job["status"] = "failed"
        job["result"] = {"error": f"Runner execution failed ({type(exc).__name__})."}
        job["updated_at"] = _now()
    finally:
        process = job.get("process")
        if process is not None and process.returncode is None:
            process.kill()
            try:
                await process.wait()
            except (OSError, RuntimeError):
                pass
        # Readers must never outlive a completed/cancelled job.
        for key in ("stdout_task", "stderr_task"):
            task = job.pop(key, None)
            if task is not None and not task.done():
                task.cancel()
        readers = [task for task in (locals().get("stdout_task"), locals().get("stderr_task")) if task is not None]
        if readers:
            await asyncio.gather(*readers, return_exceptions=True)
        job.pop("process", None)
        # Keep result/status available for a short polling window; no code is stored.
        job["expires_at"] = time.time() + 900


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "codeleaf-isolated-runner", "runtime_images_configured": bool(PYTHON_IMAGE and NODE_IMAGE)}


@app.post("/v1/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_job(body: CreateJob, x_runner_key: str = Header(default="", alias="X-Runner-Key")) -> dict:
    _authorize(x_runner_key, body.owner_id)
    now = time.time()
    for expired_id, expired in list(JOBS.items()):
        if expired.get("expires_at", 0) < now and expired.get("status") not in {"queued", "running"}:
            JOBS.pop(expired_id, None)
    for owner, stamps in list(OWNER_RECENT.items()):
        active_stamps = [stamp for stamp in stamps if stamp >= now - 60]
        if active_stamps:
            OWNER_RECENT[owner] = active_stamps
        else:
            OWNER_RECENT.pop(owner, None)
    recent = [stamp for stamp in OWNER_RECENT.get(body.owner_id, []) if stamp >= now - 60]
    if len(recent) >= MAX_JOBS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Per-owner runner quota reached.")
    active = sum(1 for row in JOBS.values() if row["owner_id"] == body.owner_id and row["status"] in {"queued", "running"})
    if active >= 2:
        raise HTTPException(status_code=429, detail="Maximum concurrent jobs per owner reached.")
    # Validate image configuration before allocating a job or queue slot.
    _image_for(body.language)
    recent.append(now)
    OWNER_RECENT[body.owner_id] = recent
    job_id = str(uuid4())
    job = {"job_id": job_id, "owner_id": body.owner_id, "language": body.language,
           "status": "queued", "created_at": _now(), "updated_at": _now(), "result": {},
           "expires_at": now + 900}
    JOBS[job_id] = job
    job["task"] = asyncio.create_task(_execute(job, body.source, body.stdin))
    # Source is passed to the running task, never retained in the status record.
    return {"job_id": job_id, "status": "queued", "created_at": job["created_at"]}


@app.get("/v1/jobs/{job_id}")
async def get_job(job_id: str, x_runner_key: str = Header(default="", alias="X-Runner-Key"),
                  x_codeleaf_user: str = Header(default="", alias="X-CodeLeaf-User")) -> dict:
    _authorize(x_runner_key, x_codeleaf_user)
    job = JOBS.get(job_id)
    if job is None or job.get("expires_at", 0) < time.time():
        JOBS.pop(job_id, None)
        raise HTTPException(status_code=404, detail="Job was not found or has expired.")
    if not hmac.compare_digest(job["owner_id"], x_codeleaf_user):
        raise HTTPException(status_code=404, detail="Job was not found.")
    return _public(job)


@app.delete("/v1/jobs/{job_id}")
async def cancel_job(job_id: str, x_runner_key: str = Header(default="", alias="X-Runner-Key"),
                     x_codeleaf_user: str = Header(default="", alias="X-CodeLeaf-User")) -> dict:
    _authorize(x_runner_key, x_codeleaf_user)
    job = JOBS.get(job_id)
    if job is None or not hmac.compare_digest(job["owner_id"], x_codeleaf_user):
        raise HTTPException(status_code=404, detail="Job was not found.")
    if job["status"] in {"queued", "running"}:
        task = job.get("task")
        if task and not task.done():
            task.cancel()
        await _docker_remove(job.get("container_name", f"codeleaf-run-{job_id}"))
        job["status"] = "cancelled"
        job["result"] = {"message": "Job was cancelled."}
        job["updated_at"] = _now()
    return {"job_id": job_id, "status": job["status"]}


@app.on_event("shutdown")
async def cleanup_runner_jobs() -> None:
    for job_id, job in list(JOBS.items()):
        task = job.get("task")
        if task and not task.done():
            task.cancel()
        await _docker_remove(job.get("container_name", f"codeleaf-run-{job_id}"))
