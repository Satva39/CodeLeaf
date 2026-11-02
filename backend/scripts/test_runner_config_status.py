
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
import app.phase5_routes as phase5_routes


class RunnerConfigStatusTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(phase5_routes.router)
        self.client = TestClient(app)

        for attribute, value in (
            ("runner_service_url", None),
            ("runner_service_token", None),
            ("jdoodle_client_id", None),
            ("jdoodle_client_secret", None),
        ):
            patcher = patch.object(
                phase5_routes.settings, attribute, value
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.client.close()

    def test_unconfigured_runner_is_reported_safely(self):
        response = self.client.get("/api/runner/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertFalse(payload["configured"])
        self.assertIsNone(payload["provider"])
        self.assertEqual(payload["supported_languages"], [])
        self.assertIn("Browser HTML/CSS/React preview", payload["message"])

    def test_jdoodle_is_reported_without_revealing_credentials(self):
        with (
            patch.object(
                phase5_routes.settings,
                "jdoodle_client_id",
                "TEST_CLIENT_ID",
            ),
            patch.object(
                phase5_routes.settings,
                "jdoodle_client_secret",
                "TEST_SECRET",
            ),
        ):
            response = self.client.get("/api/runner/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["configured"])
        self.assertEqual(payload["provider"], "jdoodle")
        self.assertIn("python", payload["supported_languages"])
        self.assertIn("javascript", payload["supported_languages"])
        self.assertIn("cpp", payload["supported_languages"])
        self.assertIn("java", payload["supported_languages"])
        self.assertIn("mysql", payload["supported_languages"])
        self.assertIn("postgresql", payload["supported_languages"])
        self.assertNotIn("TEST_CLIENT_ID", response.text)
        self.assertNotIn("TEST_SECRET", response.text)

    def test_existing_runner_remains_supported(self):
        async def fake_runner_request(method, path, **kwargs):
            if path == "/v1/languages":
                return {
                    "languages": [
                        {"key": "javascript", "aliases": ["js"], "available": True},
                        {"key": "cpp", "aliases": ["c++"], "available": False},
                    ]
                }
            if path == "/v1/database/engines":
                return {"engines": [{"key": "sqlite", "available": True}]}
            raise AssertionError(f"Unexpected Runner endpoint: {path}")

        with (
            patch.object(
                phase5_routes.settings,
                "runner_service_url",
                "https://runner.example.invalid",
            ),
            patch.object(
                phase5_routes.settings,
                "runner_service_token",
                "TEST_RUNNER_SECRET_LONG_ENOUGH_FOR_STATUS_TEST",
            ),
            patch.object(phase5_routes, "runner_request_json", new_callable=AsyncMock, side_effect=fake_runner_request),
            patch.object(phase5_routes, "jdoodle_fallback_configured", return_value=False),
        ):
            response = self.client.get("/api/runner/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["configured"])
        self.assertEqual(payload["provider"], "codeleaf-runner")
        self.assertIn("javascript", payload["supported_languages"])
        self.assertIn("sqlite", payload["supported_languages"])
        self.assertNotIn("cpp", payload["supported_languages"])
        self.assertEqual(payload["providers_by_language"]["javascript"], "codeleaf-runner")
        self.assertNotIn("runner.example.invalid", response.text)
        self.assertNotIn("TEST_RUNNER_SECRET", response.text)


if __name__ == "__main__":
    unittest.main()
