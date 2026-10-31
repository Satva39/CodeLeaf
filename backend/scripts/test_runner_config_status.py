
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

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
        self.assertIn("Browser HTML/CSS/JavaScript preview", payload["message"])

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
        self.assertEqual(
            payload["supported_languages"],
            ["python", "javascript"],
        )
        self.assertNotIn("TEST_CLIENT_ID", response.text)
        self.assertNotIn("TEST_SECRET", response.text)

    def test_existing_runner_remains_supported(self):
        with (
            patch.object(
                phase5_routes.settings,
                "runner_service_url",
                "https://runner.example.invalid",
            ),
            patch.object(
                phase5_routes.settings,
                "runner_service_token",
                "TEST_RUNNER_SECRET",
            ),
        ):
            response = self.client.get("/api/runner/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["configured"])
        self.assertEqual(payload["provider"], "external")
        self.assertNotIn("runner.example.invalid", response.text)
        self.assertNotIn("TEST_RUNNER_SECRET", response.text)


if __name__ == "__main__":
    unittest.main()
