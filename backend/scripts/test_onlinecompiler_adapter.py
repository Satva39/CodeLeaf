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

    def test_compiler_mapping_covers_all_verified_codeleaf_runtimes(self):
        expected = {
            "python": "python-3.14", "javascript": "nodejs-24",
            "typescript": "typescript-deno", "c": "gcc-15", "cpp": "g++-15",
            "cpp20": "g++-15-cpp20", "java": "openjdk-25",
            "csharp": "dotnet-csharp-10", "fsharp": "dotnet-fsharp-10",
            "go": "go-1.26", "rust": "rust-1.93", "php": "php-8.5",
            "ruby": "ruby-4.0", "haskell": "haskell-9.12", "bash": "bash-5.2",
            "fortran": "gfortran-15", "vbnet": "dotnet-vbnet-10",
            "kotlin": "kotlin-2.4", "r": "r-4.6", "swift": "swift-6.4",
            "cobol": "gnucobol-3.2", "perl": "perl-5.44", "julia": "julia-1.13",
            "pascal": "fpc-3.2", "octave": "octave-11", "nasm": "nasm-3",
            "lua": "lua-5.5", "ocaml": "ocaml-5.4", "clisp": "sbcl-2.6",
            "erlang": "erlang-29", "elixir": "elixir-1.20", "prolog": "swipl-10",
            "d": "ldc-1.43", "freebasic": "fbc-1.10", "dart": "dart-3.13",
            "clojure": "clojure-1.12", "groovy": "groovy-6.0", "scala": "scala-3.10",
            "zig": "zig-0.17", "nim": "nim-2.2", "crystal": "crystal-1.22",
            "ada": "gnat-15", "powershell": "powershell-7.6", "racket": "racket-9.3",
            "objectivec": "clang-objc-21", "sql": "sqlite-3", "duckdb": "duckdb-1.5", "sqlite": "sqlite-3",
        }
        for language, compiler_id in expected.items():
            with self.subTest(language=language):
                self.assertEqual(client.compiler_for_language(language), compiler_id)
        self.assertEqual(client.compiler_for_language("pandas"), "python-3.14-pandas2")
        self.assertEqual(client.compiler_for_language("C++"), "g++-15")
        self.assertEqual(client.compiler_for_language("C++20"), "g++-15-cpp20")
        self.assertEqual(client.compiler_for_language("c#"), "dotnet-csharp-10")
        self.assertEqual(client.compiler_for_language("f#"), "dotnet-fsharp-10")
        self.assertEqual(client.compiler_for_language("Deno"), "typescript-deno")
        self.assertEqual(client.compiler_for_language("duckdb"), "duckdb-1.5")
        self.assertEqual(client.compiler_for_language("sql"), "sqlite-3")
        self.assertEqual(client.compiler_for_language("sqlite3"), "sqlite-3")
        self.assertIsNone(client.compiler_for_language("mysql"))
        self.assertIsNone(client.compiler_for_language("postgresql"))
        self.assertIsNone(client.compiler_for_language("html"))
        self.assertIsNone(client.compiler_for_language("vue"))
        self.assertIsNone(client.compiler_for_language("django"))
        self.assertIsNone(client.compiler_for_language("fastapi"))
        self.assertIsNone(client.compiler_for_language("pytorch"))
        self.assertIsNone(client.compiler_for_language("numpy"))
        self.assertIsNone(client.compiler_for_language("scipy"))
        self.assertIsNone(client.compiler_for_language("scikit-learn"))
        self.assertIsNone(client.compiler_for_language("micropython"))

    def test_mapping_covers_every_documented_onlinecompiler_compiler_id(self):
        documented_ids = {
            "python-3.14", "gcc-15", "g++-15", "openjdk-25", "dotnet-csharp-10",
            "dotnet-fsharp-10", "go-1.26", "rust-1.93", "php-8.5", "ruby-4.0",
            "haskell-9.12", "typescript-deno", "nodejs-24", "sqlite-3", "duckdb-1.5",
            "bash-5.2", "gfortran-15", "dotnet-vbnet-10", "kotlin-2.4", "r-4.6",
            "swift-6.4", "gnucobol-3.2", "perl-5.44", "julia-1.13", "fpc-3.2",
            "octave-11", "nasm-3", "lua-5.5", "ocaml-5.4", "sbcl-2.6", "erlang-29",
            "elixir-1.20", "swipl-10", "ldc-1.43", "fbc-1.10", "dart-3.13",
            "clojure-1.12", "groovy-6.0", "scala-3.10", "zig-0.17", "nim-2.2",
            "crystal-1.22", "gnat-15", "powershell-7.6", "racket-9.3", "clang-objc-21",
            "python-3.14-pandas2", "g++-15-cpp20",
        }
        self.assertTrue(documented_ids.issubset(set(client.ONLINECOMPILER_LANGUAGE_TO_ID.values())))

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
            FakeResponse(200, [
                {"id": "python-3.14"}, {"id": "nodejs-24"},
                {"id": "gcc-15"}, {"id": "g++-15"}, {"id": "openjdk-25"},
                {"id": "dotnet-csharp-10"}, {"id": "typescript-deno"},
                {"id": "go-1.26"}, {"id": "rust-1.93"}, {"id": "php-8.5"},
            ]),
            FakeResponse(200, {"status": "ok"}),
            FakeResponse(200, {"remaining": 100}),
        ]
        with patch.object(client.httpx, "AsyncClient", FakeAsyncClient):
            status = await client.check_onlinecompiler_capabilities()
        self.assertTrue(status["configured"])
        self.assertTrue(status["reachable"])
        self.assertTrue(status["available"])
        self.assertTrue({"python", "javascript", "c", "cpp", "java", "csharp", "typescript"}.issubset(set(status["supported_languages"])))
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
