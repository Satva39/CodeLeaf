"""Phase 6 integration contract tests for the private CodeLeaf Runner bridge.

Run from the backend directory with:
    python scripts/test_phase6_runner_integration.py
"""
from __future__ import annotations

import asyncio
from contextlib import ExitStack
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import HTTPException

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import phase5_routes as routes
from app import runner_client


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class FakeAsyncClient:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.response = FakeResponse(200, {"ok": True})
        self.__class__.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


class RunnerClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_runner_client_sends_service_and_user_headers_without_json_on_get(self):
        FakeAsyncClient.instances.clear()
        with (
            patch.object(runner_client.settings, "runner_service_url", "https://runner.example"),
            patch.object(runner_client.settings, "runner_service_token", "R" * 48),
            patch.object(runner_client.httpx, "AsyncClient", FakeAsyncClient),
        ):
            payload = await runner_client.runner_request_json(
                "GET", "/v1/jobs/00000000-0000-0000-0000-000000000001", user_id="user-123"
            )

        self.assertEqual(payload, {"ok": True})
        client = FakeAsyncClient.instances[-1]
        method, url, kwargs = client.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(url, "https://runner.example/v1/jobs/00000000-0000-0000-0000-000000000001")
        self.assertEqual(kwargs["headers"]["X-Runner-Key"], "R" * 48)
        self.assertEqual(kwargs["headers"]["X-CodeLeaf-User"], "user-123")
        self.assertNotIn("json", kwargs)
        self.assertFalse(client.kwargs["follow_redirects"])

    async def test_runner_client_rejects_non_v1_paths_before_network(self):
        with (
            patch.object(runner_client.settings, "runner_service_url", "https://runner.example"),
            patch.object(runner_client.settings, "runner_service_token", "R" * 48),
            patch.object(runner_client.httpx, "AsyncClient") as client_class,
        ):
            with self.assertRaises(runner_client.RunnerServiceError):
                await runner_client.runner_request_json("GET", "https://evil.example/v1/languages")
        client_class.assert_not_called()


class RunnerInputTests(unittest.TestCase):
    def test_multi_file_payload_is_accepted_within_runner_limits(self):
        body = routes.RunnerCreateInput(
            language="cpp",
            files=[
                {"name": "main.cpp", "content": "int main(){return helper();}"},
                {"name": "helper.hpp", "content": "inline int helper(){return 0;}"},
            ],
        )
        self.assertEqual(body.language, "cpp")
        self.assertEqual(len(body.files), 2)

    def test_multi_file_payload_rejects_paths_duplicate_names_and_utf8_byte_overflow(self):
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", files=[{"name": "src/main.py", "content": "print(1)"}])
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", files=[
                {"name": "main.py", "content": "print(1)"},
                {"name": "MAIN.PY", "content": "print(2)"},
            ])
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", files=[{"name": "unicode.py", "content": "é" * 32769}])
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", source="é" * 32769)
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", source="print(1)", stdin="é" * 8193)

    def test_multi_file_payload_enforces_runner_file_count_and_byte_limits(self):
        too_many = [{"name": f"file{i}.py", "content": "x"} for i in range(11)]
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", files=too_many)
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", files=[{"name": "large.py", "content": "x" * 65537}])
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="python", files=[
                {"name": "a.py", "content": "x" * 65536},
                {"name": "b.py", "content": "y" * 65536},
                {"name": "c.py", "content": "z"},
            ])

    def test_sqlite_database_job_uses_engine_key_and_requires_query(self):
        body = routes.RunnerCreateInput(language="sqlite3", source="SELECT 1")
        self.assertEqual(body.language, "sqlite")
        with self.assertRaises(ValueError):
            routes.RunnerCreateInput(language="sqlite", files=[{"name": "query.sql", "content": "SELECT 1"}])


class RunnerRouteTests(unittest.IsolatedAsyncioTestCase):
    def _db_for_create(self):
        db = Mock()
        db.scalar.side_effect = [0, 0]
        db.refresh.side_effect = lambda row: setattr(row, "id", getattr(row, "id", None) or uuid4())
        return db

    def _create_patches(self, *, capabilities):
        reservation = SimpleNamespace(id=uuid4())
        patches = [
            patch.object(routes, "_load_runner_capabilities", new_callable=AsyncMock, return_value=capabilities),
            patch.object(routes, "effective_plan_id", return_value="full_access"),
            patch.object(routes, "plan_limits", return_value={"code_executions_per_day": 150}),
            patch.object(routes, "reserve_daily_usage", return_value=(reservation, False)),
            patch.object(routes, "finalize_daily_usage"),
        ]
        return patches

    async def test_multi_file_code_job_is_submitted_to_runner_with_user_scope(self):
        db = self._db_for_create()
        user = SimpleNamespace(id=uuid4())
        job_id = str(uuid4())
        body = routes.RunnerCreateInput(language="cpp", files=[
            {"name": "main.cpp", "content": "int main(){return helper();}"},
            {"name": "helper.hpp", "content": "inline int helper(){return 0;}"},
        ])
        async def submit(method, path, **kwargs):
            self.assertEqual(method, "POST")
            self.assertEqual(path, "/v1/jobs")
            self.assertEqual(kwargs["user_id"], str(user.id))
            self.assertEqual(kwargs["payload"]["language"], "cpp")
            self.assertEqual([item["name"] for item in kwargs["payload"]["files"]], ["main.cpp", "helper.hpp"])
            return {"job_id": job_id, "status": "queued"}

        with ExitStack() as stack:
            for patcher in self._create_patches(capabilities=({"cpp"}, set(), True)):
                stack.enter_context(patcher)
            request_mock = stack.enter_context(
                patch.object(routes, "runner_request_json", new_callable=AsyncMock, side_effect=submit)
            )
            response = await routes.create_runner_job(body=body, user=user, db=db)

        saved = db.add.call_args.args[0]
        self.assertEqual(response["job"]["status"], "queued")
        self.assertEqual(saved.external_job_id, job_id)
        self.assertEqual(saved.result_json, {"provider": "codeleaf-runner", "job_type": "code"})
        request_mock.assert_awaited_once()

    async def test_database_job_uses_database_queue_and_saves_job_type(self):
        db = self._db_for_create()
        user = SimpleNamespace(id=uuid4())
        job_id = str(uuid4())
        body = routes.RunnerCreateInput(
            language="postgresql",
            source="SELECT name FROM learners",
            setup_sql="CREATE TABLE learners(name TEXT); INSERT INTO learners VALUES ('CodeLeaf');",
        )
        async def submit(method, path, **kwargs):
            self.assertEqual(path, "/v1/database/jobs")
            self.assertEqual(kwargs["payload"], {
                "engine": "postgresql",
                "query": "SELECT name FROM learners",
                "setup_sql": "CREATE TABLE learners(name TEXT); INSERT INTO learners VALUES ('CodeLeaf');",
            })
            self.assertEqual(kwargs["user_id"], str(user.id))
            return {"job_id": job_id, "status": "queued"}

        with ExitStack() as stack:
            for patcher in self._create_patches(capabilities=(set(), {"postgresql"}, True)):
                stack.enter_context(patcher)
            request_mock = stack.enter_context(
                patch.object(routes, "runner_request_json", new_callable=AsyncMock, side_effect=submit)
            )
            stack.enter_context(patch.object(routes, "jdoodle_fallback_configured", return_value=True))
            response = await routes.create_runner_job(body=body, user=user, db=db)

        saved = db.add.call_args.args[0]
        self.assertEqual(response["job"]["provider"], "codeleaf-runner")
        self.assertEqual(saved.result_json["job_type"], "database")
        request_mock.assert_awaited_once()

    async def test_database_job_poll_uses_database_endpoint_and_formats_rows(self):
        user = SimpleNamespace(id=uuid4())
        job_id = uuid4()
        row = SimpleNamespace(
            id=job_id, user_id=user.id, language="mysql", status="running",
            external_job_id=str(uuid4()),
            result_json={"provider": "codeleaf-runner", "job_type": "database"},
            updated_at=None,
        )
        db = Mock()
        db.scalar.return_value = row
        response_data = {
            "status": "completed",
            "result": {
                "engine": "mysql", "columns": ["name"], "rows": [["CodeLeaf"]],
                "row_count": 1, "execution_ms": 14,
            },
        }
        with patch.object(routes, "runner_request_json", new_callable=AsyncMock, return_value=response_data) as request_mock:
            response = await routes.get_runner_job(job_id=job_id, user=user, db=db)

        self.assertEqual(request_mock.await_args.args[:2], ("GET", f"/v1/database/jobs/{row.external_job_id}"))
        self.assertEqual(request_mock.await_args.kwargs["user_id"], str(user.id))
        self.assertEqual(response["job"]["result"]["rows"], [["CodeLeaf"]])
        self.assertIn("CodeLeaf", response["job"]["result"]["stdout"])
        self.assertEqual(row.status, "completed")

    async def test_database_job_cancel_uses_database_endpoint(self):
        user = SimpleNamespace(id=uuid4())
        job_id = uuid4()
        row = SimpleNamespace(
            id=job_id, user_id=user.id, language="sqlite", status="queued",
            external_job_id=str(uuid4()), result_json={"provider": "codeleaf-runner", "job_type": "database"},
            updated_at=None,
        )
        db = Mock()
        db.scalar.return_value = row
        with patch.object(routes, "runner_request_json", new_callable=AsyncMock, return_value={"status": "cancelled"}) as request_mock:
            response = await routes.cancel_runner_job(job_id=job_id, user=user, db=db)
        self.assertEqual(request_mock.await_args.args[:2], ("DELETE", f"/v1/database/jobs/{row.external_job_id}"))
        self.assertEqual(response, {"ok": True, "status": "cancelled"})


    async def test_database_job_queue_poll_has_no_false_success_output(self):
        user = SimpleNamespace(id=uuid4())
        job_id = uuid4()
        row = SimpleNamespace(
            id=job_id, user_id=user.id, language="sqlite", status="queued",
            external_job_id=str(uuid4()),
            result_json={"provider": "codeleaf-runner", "job_type": "database"},
            updated_at=None,
        )
        db = Mock()
        db.scalar.return_value = row
        with patch.object(routes, "runner_request_json", new_callable=AsyncMock, return_value={"status": "queued", "result": {}}):
            response = await routes.get_runner_job(job_id=job_id, user=user, db=db)
        self.assertEqual(response["job"]["status"], "queued")
        self.assertEqual(response["job"]["result"], {})

    async def test_database_job_running_cannot_be_cancelled(self):
        user = SimpleNamespace(id=uuid4())
        job_id = uuid4()
        row = SimpleNamespace(
            id=job_id, user_id=user.id, language="mysql", status="running",
            external_job_id=str(uuid4()), result_json={"provider": "codeleaf-runner", "job_type": "database"},
            updated_at=None,
        )
        db = Mock()
        db.scalar.return_value = row
        with patch.object(
            routes, "runner_request_json", new_callable=AsyncMock,
            side_effect=routes.RunnerServiceError("running", status_code=409),
        ):
            with self.assertRaises(HTTPException) as raised:
                await routes.cancel_runner_job(job_id=job_id, user=user, db=db)
        self.assertEqual(raised.exception.status_code, 409)

    async def test_runner_submit_failure_does_not_duplicate_execution_via_jdoodle(self):
        db = self._db_for_create()
        user = SimpleNamespace(id=uuid4())
        body = routes.RunnerCreateInput(language="python", source="print(1)")
        patches = self._create_patches(capabilities=({"python"}, set(), True))
        with ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            stack.enter_context(patch.object(routes, "runner_request_json", new_callable=AsyncMock, side_effect=routes.RunnerServiceError("unavailable")))
            stack.enter_context(patch.object(routes, "jdoodle_fallback_configured", return_value=True))
            jdoodle_mock = stack.enter_context(patch.object(routes, "execute_jdoodle", new_callable=AsyncMock))
            with self.assertRaises(HTTPException) as raised:
                await routes.create_runner_job(body=body, user=user, db=db)
        self.assertEqual(raised.exception.status_code, 503)
        jdoodle_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main(verbosity=2)
