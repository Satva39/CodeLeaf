"""Mocked contract tests for CodeLeaf's OnlineCompiler adapter (no real key needed)."""
from __future__ import annotations

import asyncio
import base64
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch

from app import onlinecompiler_client as client


class FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    response = FakeResponse(200, {})
    get_responses = []
    post_response = None
    last_request = None

    def __init__(self, **kwargs):
        self.options = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, **kwargs):
        type(self).last_request = ("GET", url, kwargs)
        if self.get_responses:
            return self.get_responses.pop(0)
        return self.response

    async def post(self, url, **kwargs):
        type(self).last_request = ("POST", url, kwargs)
        return self.post_response or self.response


class OnlineCompilerAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = client.settings
        self.settings_patchers = [
            patch.object(self.settings, "onlinecompiler_enabled", True),
            patch.object(self.settings, "onlinecompiler_api_key", "TEST_ONLY_NOT_A_REAL_KEY"),
            patch.object(self.settings, "onlinecompiler_base_url", "https://api.onlinecompiler.io"),
            patch.object(self.settings, "onlinecompiler_timeout_seconds", 65),
        ]
        for patcher in self.settings_patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        FakeAsyncClient.get_responses = []
        FakeAsyncClient.post_response = None
        FakeAsyncClient.last_request = None

    def test_compiler_mapping_is_restricted_to_python_and_javascript(self):
        self.assertEqual(client.compiler_for_language("python"), "python-3.14")
        self.assertEqual(client.compiler_for_language("py"), "python-3.14")
        self.assertEqual(client.compiler_for_language("javascript"), "nodejs-24")
        self.assertEqual(client.compiler_for_language("js"), "nodejs-24")
        self.assertIsNone(client.compiler_for_language("cpp"))
        self.assertIsNone(client.compiler_for_language("html"))

    def test_run_result_never_claims_success_from_exit_code_alone(self):
        result = client.normalize_run_result({
            "output": "partial",
            "error": "runtime failed",
            "status": "error",
            "exit_code": 1,
            "signal": None,
            "truncated": False,
            "time": "0.0302",
            "total": "0.0400",
            "memory": "8192",
        })
        self.assertEqual(result["provider"], "onlinecompiler")
        self.assertFalse(result["success"])
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["execution_ms"], 30)
        self.assertEqual(result["stdout"], "partial")

    async def test_capability_check_requires_registry_health_and_valid_key(self):
        FakeAsyncClient.get_responses = [
            FakeResponse(200, [{"id": "python-3.14"}, {"id": "nodejs-24"}]),
            FakeResponse(200, {"status": "ok"}),
            FakeResponse(200, {"remaining": 100}),
        ]
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            status = await client.check_onlinecompiler_capabilities()
        self.assertTrue(status["configured"])
        self.assertTrue(status["reachable"])
        self.assertTrue(status["available"])
        self.assertEqual(set(status["supported_languages"]), {"python", "javascript"})
        self.assertNotIn("TEST_ONLY_NOT_A_REAL_KEY", str(status))

    async def test_invalid_key_does_not_report_available(self):
        FakeAsyncClient.get_responses = [
            FakeResponse(200, [{"id": "python-3.14"}, {"id": "nodejs-24"}]),
            FakeResponse(200, {"status": "ok"}),
            FakeResponse(401, {"detail": "secret omitted"}),
        ]
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            status = await client.check_onlinecompiler_capabilities()
        self.assertTrue(status["configured"])
        self.assertFalse(status["available"])
        self.assertEqual(status["supported_languages"], [])

    async def test_sync_request_uses_private_auth_and_documented_contract(self):
        FakeAsyncClient.post_response = FakeResponse(200, {
            "output": "Hello",
            "error": "",
            "status": "success",
            "exit_code": 0,
            "signal": None,
            "truncated": False,
            "time": "0.03",
            "total": "0.04",
            "memory": "9000",
        })
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            result = await client.run_code_sync(
                language="python",
                code="print('Hello')",
                stdin="",
                files=[{"name": "data.txt", "content": "value"}],
            )
        method, url, request = FakeAsyncClient.last_request
        self.assertEqual(method, "POST")
        self.assertEqual(url, "https://api.onlinecompiler.io/api/run-code-sync/")
        self.assertEqual(request["headers"]["Authorization"], "TEST_ONLY_NOT_A_REAL_KEY")
        self.assertEqual(request["json"]["compiler"], "python-3.14")
        self.assertEqual(request["json"]["code"], "print('Hello')")
        self.assertEqual(request["json"]["files"][0]["encoding"], "utf8")
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "onlinecompiler")

    async def test_hidden_test_request_marks_cases_and_sets_idempotency_header(self):
        FakeAsyncClient.post_response = FakeResponse(200, {
            "verdict": "accepted", "score": 100, "passed": 2, "total": 2,
            "tests": [{"verdict": "accepted", "hidden": True}, {"verdict": "accepted", "hidden": True}],
        })
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            result = await client.run_tests(
                language="javascript",
                code="console.log('x')",
                tests=[
                    {"input": "1", "expected_output": "x", "hidden": True},
                    {"input": "2", "expected_output": "x", "hidden": True},
                ],
                idempotency_key="battle:sample:123",
            )
        method, url, request = FakeAsyncClient.last_request
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/api/run-tests/"))
        self.assertEqual(request["headers"]["Idempotency-Key"], "battle:sample:123")
        self.assertTrue(all(row["hidden"] is True for row in request["json"]["tests"]))
        self.assertEqual(result["verdict"], "accepted")

    async def test_output_files_are_validated_and_normalized_for_download(self):
        content = base64.b64encode(b"a,b\n1,2\n").decode("ascii")
        result = client.normalize_run_result({
            "output": "done", "error": "", "status": "success", "exit_code": 0,
            "files": [{"name": "result.csv", "mime": "text/csv", "size": 8,
                       "content_base64": content, "url": "https://api.onlinecompiler.io/api/files/1/"}],
        })
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["name"], "result.csv")
        self.assertEqual(result["files"][0]["mime"], "text/csv")
        self.assertNotIn("url", result["files"][0])
        self.assertFalse(result["files_truncated"])

    async def test_zero_monthly_or_key_usage_prevents_runtime_advertising(self):
        FakeAsyncClient.get_responses = [
            FakeResponse(200, [{"id": "python-3.14"}, {"id": "nodejs-24"}]),
            FakeResponse(200, {"status": "ok"}),
            FakeResponse(200, {"remaining": 0, "key": {"remaining": 100}}),
        ]
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            status = await client.check_onlinecompiler_capabilities()
        self.assertTrue(status["reachable"])
        self.assertFalse(status["available"])
        self.assertEqual(status["supported_languages"], [])

    async def test_reserved_input_file_names_are_rejected(self):
        with self.assertRaises(client.OnlineCompilerError):
            await client.run_code_sync(language="python", code="print(1)", files=[{"name": "input", "content": "x"}])

    async def test_provider_rate_limit_is_preserved_as_429_and_not_leaked(self):
        FakeAsyncClient.post_response = FakeResponse(429, {"error": "private provider detail"})
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            with self.assertRaises(client.OnlineCompilerError) as raised:
                await client.run_code_sync(language="python", code="print('x')")
        self.assertEqual(raised.exception.status_code, 429)
        self.assertNotIn("private provider detail", str(raised.exception))
        self.assertNotIn("TEST_ONLY_NOT_A_REAL_KEY", str(raised.exception))

    async def test_invalid_source_and_hidden_test_count_are_rejected(self):
        with self.assertRaises(client.OnlineCompilerError):
            await client.run_code_sync(language="python", code="print('x')\x00")
        with self.assertRaises(client.OnlineCompilerError):
            await client.run_tests(language="python", code="print('x')", tests=[])


if __name__ == "__main__":
    unittest.main(verbosity=2)
