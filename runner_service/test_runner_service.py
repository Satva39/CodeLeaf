"""Runner control-plane contract tests; these never launch Docker containers."""
from __future__ import annotations
import asyncio
import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

os.environ.setdefault("RUNNER_SERVICE_TOKEN", "test-runner-secret-key-that-is-long-enough-12345")
os.environ.setdefault("RUNNER_PYTHON_IMAGE", "sha256:" + "a" * 64)
os.environ.setdefault("RUNNER_NODE_IMAGE", "sha256:" + "b" * 64)
MODULE_PATH = Path(__file__).with_name("app.py")
spec = importlib.util.spec_from_file_location("codeleaf_runner_test_module", MODULE_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(runner)

class RunnerContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        runner.JOBS.clear()
        runner.OWNER_RECENT.clear()

    def test_runner_requires_long_shared_secret(self):
        self.assertEqual(runner._authorize(runner.SERVICE_KEY, "owner-123456"), "owner-123456")
        with self.assertRaises(runner.HTTPException) as context:
            runner._authorize("wrong-key-that-does-not-match", "owner-123456")
        self.assertEqual(context.exception.status_code, 401)

    def test_runtime_images_must_be_immutable_digests(self):
        self.assertTrue(runner._image_for("python").startswith("sha256:"))
        original = runner.PYTHON_IMAGE
        try:
            runner.PYTHON_IMAGE = "python:latest"
            with self.assertRaises(runner.HTTPException) as context:
                runner._image_for("python")
            self.assertEqual(context.exception.status_code, 503)
        finally:
            runner.PYTHON_IMAGE = original

    def test_docker_command_has_isolation_and_resource_limits(self):
        command = runner._docker_command("python", "codeleaf-run-test")
        joined = " ".join(command)
        for required in ("--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=64", "--memory=128m", "--cpus=0.50", "--user=10001:10001", "--pull=never"):
            self.assertIn(required, joined)
        self.assertNotIn("--privileged", command)
        self.assertNotIn("--mount", command)
        self.assertNotIn("-v", command)
        self.assertNotIn("print('ok')", joined)
        self.assertIn("sys.stdin.buffer.read(n)", joined)

    def test_job_input_rejects_nul_bytes_and_extra_commands(self):
        with self.assertRaises(Exception):
            runner.CreateJob(owner_id="owner-123456", language="python", source="print(1)\x00")
        with self.assertRaises(Exception):
            runner.CreateJob(owner_id="owner-123456", language="python", source="print(1)", command="sh")

    async def test_output_is_bounded_and_overflow_is_signalled(self):
        original_remove = runner._docker_remove
        runner._docker_remove = AsyncMock()
        try:
            stream = asyncio.StreamReader()
            stream.feed_data(b"123456789")
            stream.feed_eof()
            overflow = asyncio.Event()
            value = await runner._read_limited(stream, 4, overflow, "codeleaf-run-test")
            self.assertEqual(value, b"1234")
            self.assertTrue(overflow.is_set())
            runner._docker_remove.assert_awaited_once_with("codeleaf-run-test")
        finally:
            runner._docker_remove = original_remove

    async def test_other_owner_cannot_read_a_job(self):
        runner.JOBS["job-1"] = {"job_id": "job-1", "owner_id": "owner-123456", "status": "completed", "expires_at": 9999999999, "result": {}}
        with self.assertRaises(runner.HTTPException) as context:
            await runner.get_job("job-1", runner.SERVICE_KEY, "other-owner-123")
        self.assertEqual(context.exception.status_code, 404)

    async def test_cancel_requests_container_cleanup(self):
        runner.JOBS["job-2"] = {"job_id": "job-2", "owner_id": "owner-123456", "status": "running", "expires_at": 9999999999, "result": {}, "task": None, "container_name": "codeleaf-run-job-2"}
        original_remove = runner._docker_remove
        runner._docker_remove = AsyncMock()
        try:
            result = await runner.cancel_job("job-2", runner.SERVICE_KEY, "owner-123456")
            self.assertEqual(result["status"], "cancelled")
            runner._docker_remove.assert_awaited_once_with("codeleaf-run-job-2")
        finally:
            runner._docker_remove = original_remove

    def test_timeout_setting_is_bounded(self):
        self.assertGreaterEqual(runner.JOB_TIMEOUT_SECONDS, 1)
        self.assertLessEqual(runner.JOB_TIMEOUT_SECONDS, 8)

    def test_public_result_does_not_expose_internal_fields(self):
        result = runner._public({"job_id": "job-3", "status": "completed", "created_at": "x", "updated_at": "x", "source": "secret code", "owner_id": "private-owner", "result": {"stdout": "ok"}})
        self.assertNotIn("source", result)
        self.assertNotIn("owner_id", result)

if __name__ == "__main__":
    unittest.main(verbosity=2)
