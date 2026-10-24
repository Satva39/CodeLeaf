"""Unit tests for the non-sensitive isolated runner configuration status endpoint.

Run from backend/: python scripts/test_runner_config_status.py
No database connection or provider secrets are required.
"""
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

    def tearDown(self):
        self.client.close()

    def test_unconfigured_runner_is_reported_without_revealing_secrets(self):
        with patch.object(phase5_routes.settings, "runner_service_url", None), patch.object(
            phase5_routes.settings, "runner_service_token", None
        ):
            response = self.client.get("/api/runner/status")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertFalse(payload["configured"])
        self.assertEqual(payload["supported_languages"], [])
        self.assertIn("Browser HTML/CSS/JavaScript preview", payload["message"])
        self.assertNotIn("runner_service_token", response.text)
        self.assertNotIn("runner_service_url", response.text)

    def test_configured_runner_reports_supported_languages_without_returning_url_or_token(self):
        fake_url = "https://runner.example.invalid"
        fake_token = "TEST_SECRET_DO_NOT_RETURN"
        with patch.object(phase5_routes.settings, "runner_service_url", fake_url), patch.object(
            phase5_routes.settings, "runner_service_token", fake_token
        ):
            response = self.client.get("/api/runner/status")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["configured"])
        self.assertEqual(payload["supported_languages"], ["python", "javascript"])
        self.assertNotIn(fake_url, response.text)
        self.assertNotIn(fake_token, response.text)


if __name__ == "__main__":
    unittest.main()
