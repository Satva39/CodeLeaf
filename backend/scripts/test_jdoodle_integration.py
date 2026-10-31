"""Mocked regression tests for CodeLeaf's JDoodle runner integration.

Run from the backend directory:
    python scripts/test_jdoodle_integration.py

These tests do not contact JDoodle and do not consume API credits.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import httpx
from fastapi import HTTPException

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import jdoodle_runner
from app import phase5_routes as routes
from app.config import settings


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, json_error=False):
        self.status_code = status_code
        self.payload = payload if payload is not None else {}
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("invalid JSON")
        return self.payload


class FakeAsyncClient:
    def __init__(self, response=None, post_error=None, **kwargs):
        self.response = response or FakeResponse()
        self.post_error = post_error
        self.kwargs = kwargs
        self.post_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, *, json=None, headers=None):
        self.post_calls.append((url, json, headers))
        if self.post_error is not None:
            raise self.post_error
        return self.response


class JDoodleAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client_id_patch = patch.object(settings, "jdoodle_client_id", "test-client-id")
        self.client_secret_patch = patch.object(settings, "jdoodle_client_secret", "test-client-secret")
        self.client_id_patch.start()
        self.client_secret_patch.start()

    def tearDown(self):
        self.client_secret_patch.stop()
        self.client_id_patch.stop()

    async def test_python_request_uses_expected_jdoodle_payload(self):
        client = FakeAsyncClient(
            response=FakeResponse(
                payload={"statusCode": 200, "output": "hello from python", "memory": "10", "cpuTime": "0.01"}
            )
        )
        with patch.object(jdoodle_runner.httpx, "AsyncClient", return_value=client):
            result = await jdoodle_runner.execute_jdoodle(
                language="python", source="print('hello from python')", stdin=""
            )

        self.assertEqual(result["provider"], "jdoodle")
        self.assertEqual(result["stdout"], "hello from python")
        self.assertEqual(client.post_calls[0][0], jdoodle_runner.JDOODLE_EXECUTE_URL)
        payload = client.post_calls[0][1]
        self.assertEqual(payload["clientId"], "test-client-id")
        self.assertEqual(payload["clientSecret"], "test-client-secret")
        self.assertEqual(payload["language"], "python3")
        self.assertEqual(payload["versionIndex"], "5")
        self.assertEqual(payload["script"], "print('hello from python')")

    async def test_javascript_request_uses_nodejs_configuration(self):
        client = FakeAsyncClient(
            response=FakeResponse(payload={"statusCode": 200, "output": "hello from js"})
        )
        with patch.object(jdoodle_runner.httpx, "AsyncClient", return_value=client):
            result = await jdoodle_runner.execute_jdoodle(
                language="javascript", source="console.log('hello from js')"
            )

        self.assertEqual(result["stdout"], "hello from js")
        payload = client.post_calls[0][1]
        self.assertEqual(payload["language"], "nodejs")
        self.assertEqual(payload["versionIndex"], "7")

    async def test_unsupported_language_is_rejected_before_network_call(self):
        with patch.object(jdoodle_runner.httpx, "AsyncClient") as client_class:
            with self.assertRaises(HTTPException) as raised:
                await jdoodle_runner.execute_jdoodle(language="ruby", source="puts 1")
        self.assertEqual(raised.exception.status_code, 422)
        client_class.assert_not_called()

    async def test_exhausted_provider_credits_map_to_429(self):
        client = FakeAsyncClient(
            response=FakeResponse(payload={"statusCode": 429, "error": "credit limit reached"})
        )
        with patch.object(jdoodle_runner.httpx, "AsyncClient", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                await jdoodle_runner.execute_jdoodle(language="python", source="print(1)")
        self.assertEqual(raised.exception.status_code, 429)

    async def test_provider_timeout_maps_to_504(self):
        client = FakeAsyncClient(post_error=httpx.ReadTimeout("test timeout"))
        with patch.object(jdoodle_runner.httpx, "AsyncClient", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                await jdoodle_runner.execute_jdoodle(language="python", source="print(1)")
        self.assertEqual(raised.exception.status_code, 504)


class RunnerRouteTests(unittest.IsolatedAsyncioTestCase):
    def _prepare_db_for_create(self):
        db = Mock()
        # The route checks recent-job and active-job counts when no idempotency
        # key is supplied. Both begin at zero in this isolated test.
        db.scalar.side_effect = [0, 0]
        db.refresh.side_effect = self._refresh_row
        return db

    @staticmethod
    def _refresh_row(row):
        if getattr(row, "id", None) is None:
            row.id = uuid4()

    def _settings_patches(self, *, external=False):
        return [
            patch.object(settings, "runner_service_url", "https://runner.example" if external else ""),
            patch.object(settings, "runner_service_token", "test-runner-token" if external else ""),
            patch.object(settings, "jdoodle_client_id", "test-client-id"),
            patch.object(settings, "jdoodle_client_secret", "test-client-secret"),
        ]

    async def test_create_job_executes_jdoodle_and_persists_completed_output(self):
        db = self._prepare_db_for_create()
        user = SimpleNamespace(id=uuid4())
        body = routes.RunnerCreateInput(language="python", source="print(42)")
        usage_reservation = SimpleNamespace(id=uuid4())

        with (
            patch.object(routes.settings, "runner_service_url", ""),
            patch.object(routes.settings, "runner_service_token", ""),
            patch.object(routes.settings, "jdoodle_client_id", "test-client-id"),
            patch.object(routes.settings, "jdoodle_client_secret", "test-client-secret"),
            patch.object(routes, "effective_plan_id", return_value="full_access"),
            patch.object(routes, "plan_limits", return_value={"code_executions_per_day": 150}),
            patch.object(routes, "reserve_daily_usage", return_value=(usage_reservation, False)),
            patch.object(routes, "finalize_daily_usage") as finalize_usage,
            patch.object(
                routes, "execute_jdoodle",
                new_callable=AsyncMock,
                return_value={"provider": "jdoodle", "stdout": "42", "stderr": ""},
            ) as execute_mock,
        ):
            response = await routes.create_runner_job(body=body, user=user, db=db)

        saved_row = db.add.call_args.args[0]
        self.assertEqual(response["job"]["status"], "completed")
        self.assertEqual(saved_row.status, "completed")
        self.assertEqual(saved_row.result_json["provider"], "jdoodle")
        self.assertEqual(saved_row.result_json["result"]["stdout"], "42")
        self.assertTrue(saved_row.external_job_id.startswith("jdoodle-"))
        execute_mock.assert_awaited_once()
        finalize_usage.assert_called_once()
        self.assertTrue(finalize_usage.call_args.kwargs["success"])

    async def test_jdoodle_provider_error_releases_usage_reservation(self):
        db = self._prepare_db_for_create()
        user = SimpleNamespace(id=uuid4())
        body = routes.RunnerCreateInput(language="python", source="print(42)")
        usage_reservation = SimpleNamespace(id=uuid4())

        with (
            patch.object(routes.settings, "runner_service_url", ""),
            patch.object(routes.settings, "runner_service_token", ""),
            patch.object(routes.settings, "jdoodle_client_id", "test-client-id"),
            patch.object(routes.settings, "jdoodle_client_secret", "test-client-secret"),
            patch.object(routes, "effective_plan_id", return_value="full_access"),
            patch.object(routes, "plan_limits", return_value={"code_executions_per_day": 150}),
            patch.object(routes, "reserve_daily_usage", return_value=(usage_reservation, False)),
            patch.object(routes, "finalize_daily_usage") as finalize_usage,
            patch.object(
                routes, "execute_jdoodle",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=429, detail="daily credits exhausted"),
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                await routes.create_runner_job(body=body, user=user, db=db)

        self.assertEqual(raised.exception.status_code, 429)
        finalize_usage.assert_called_once()
        self.assertFalse(finalize_usage.call_args.kwargs["success"])
        db.add.assert_not_called()

    async def test_saved_jdoodle_result_is_returned_without_external_polling(self):
        user = SimpleNamespace(id=uuid4())
        job_id = uuid4()
        row = SimpleNamespace(
            id=job_id,
            user_id=user.id,
            language="python",
            status="completed",
            result_json={"provider": "jdoodle", "result": {"stdout": "42", "stderr": ""}},
        )
        db = Mock()
        db.scalar.return_value = row

        with patch.object(routes.httpx, "AsyncClient") as client_class:
            response = await routes.get_runner_job(job_id=job_id, user=user, db=db)

        self.assertEqual(response["job"]["result"]["stdout"], "42")
        client_class.assert_not_called()

    async def test_completed_jdoodle_job_cannot_be_cancelled(self):
        user = SimpleNamespace(id=uuid4())
        job_id = uuid4()
        row = SimpleNamespace(
            id=job_id,
            user_id=user.id,
            result_json={"provider": "jdoodle", "result": {"stdout": "done"}},
        )
        db = Mock()
        db.scalar.return_value = row

        with patch.object(routes.httpx, "AsyncClient") as client_class:
            with self.assertRaises(HTTPException) as raised:
                await routes.cancel_runner_job(job_id=job_id, user=user, db=db)

        self.assertEqual(raised.exception.status_code, 409)
        client_class.assert_not_called()

    async def test_existing_external_runner_remains_preferred(self):
        db = self._prepare_db_for_create()
        user = SimpleNamespace(id=uuid4())
        body = routes.RunnerCreateInput(language="javascript", source="console.log(1)")
        usage_reservation = SimpleNamespace(id=uuid4())
        fake_client = FakeAsyncClient(
            response=FakeResponse(status_code=202, payload={"job_id": "external-job-123", "status": "queued"})
        )

        with (
            patch.object(routes.settings, "runner_service_url", "https://runner.example"),
            patch.object(routes.settings, "runner_service_token", "test-runner-token"),
            patch.object(routes.settings, "jdoodle_client_id", "test-client-id"),
            patch.object(routes.settings, "jdoodle_client_secret", "test-client-secret"),
            patch.object(routes, "effective_plan_id", return_value="full_access"),
            patch.object(routes, "plan_limits", return_value={"code_executions_per_day": 150}),
            patch.object(routes, "reserve_daily_usage", return_value=(usage_reservation, False)),
            patch.object(routes, "finalize_daily_usage"),
            patch.object(routes.httpx, "AsyncClient", return_value=fake_client),
            patch.object(routes, "execute_jdoodle", new_callable=AsyncMock) as execute_mock,
        ):
            response = await routes.create_runner_job(body=body, user=user, db=db)

        saved_row = db.add.call_args.args[0]
        self.assertEqual(response["job"]["status"], "queued")
        self.assertEqual(saved_row.external_job_id, "external-job-123")
        self.assertEqual(saved_row.result_json, {})
        execute_mock.assert_not_awaited()
        self.assertEqual(fake_client.post_calls[0][0], "https://runner.example/v1/jobs")


if __name__ == "__main__":
    unittest.main(verbosity=2)
