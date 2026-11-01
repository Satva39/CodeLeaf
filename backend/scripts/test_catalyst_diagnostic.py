"""Tests for the temporary, token-protected Catalyst production diagnostic."""
from __future__ import annotations

import hashlib
import io
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.storage.catalyst_smoke_test import run_stratus_smoke_test  # noqa: E402
from app.storage.factory import get_active_storage  # noqa: E402

TOKEN = "temporary-diagnostic-test-token-" + ("x" * 40)
HEADER = "X-Catalyst-Diagnostic-Token"
EXPECTED_BUCKET = "codeleaf-project-archives-prod-8392"
PAYLOAD = (
    b"CodeLeaf temporary Catalyst Stratus connectivity diagnostic. "
    b"This object contains no student or portfolio data.\n"
)


@dataclass
class FakeStoredObject:
    checksum_sha256: str


class FakeStorage:
    bucket_name = EXPECTED_BUCKET

    def __init__(self, *, fail_upload_after_write: bool = False) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self.fail_upload_after_write = fail_upload_after_write

    def upload_stream(self, key, stream, *, expected_size=None):
        payload = stream.read()
        if expected_size is not None and len(payload) != expected_size:
            raise AssertionError("unexpected test upload size")
        self.objects[key] = payload
        if self.fail_upload_after_write:
            raise RuntimeError("simulated upload failure after partial object creation")
        return FakeStoredObject(hashlib.sha256(payload).hexdigest())

    def object_exists(self, key):
        return key in self.objects

    def object_metadata(self, key):
        return {"key": key, "size": len(self.objects[key])}

    def download_range(self, key, start, end):
        return self.objects[key][start : end + 1]

    def checksum_object(self, key):
        return hashlib.sha256(self.objects[key]).hexdigest()

    def delete_object(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)
        return True


class CatalystDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.original_settings = {
            "catalyst_diagnostic_token": settings.catalyst_diagnostic_token,
            "catalyst_environment": settings.catalyst_environment,
            "catalyst_stratus_bucket": settings.catalyst_stratus_bucket,
            "catalyst_accounts_url": settings.catalyst_accounts_url,
            "catalyst_project_domain": settings.catalyst_project_domain,
            "catalyst_stratus_resource_suffix": settings.catalyst_stratus_resource_suffix,
            "portfolio_storage_provider": settings.portfolio_storage_provider,
            "catalyst_stratus_enabled": settings.catalyst_stratus_enabled,
        }
        settings.catalyst_diagnostic_token = SecretStr(TOKEN)
        settings.catalyst_environment = "Production"
        settings.catalyst_stratus_bucket = EXPECTED_BUCKET
        settings.catalyst_accounts_url = "https://accounts.zoho.in"
        settings.catalyst_project_domain = "https://api.catalyst.zoho.in"
        settings.catalyst_stratus_resource_suffix = ".zohostratus.in"
        settings.portfolio_storage_provider = "database"
        settings.catalyst_stratus_enabled = False

    def tearDown(self) -> None:
        for name, value in self.original_settings.items():
            setattr(settings, name, value)

    def test_missing_token_returns_404_and_does_not_initialize_storage(self):
        with patch("app.diagnostic_routes.get_catalyst_storage") as getter:
            response = self.client.post("/api/diagnostics/catalyst-stratus")
        self.assertEqual(response.status_code, 404)
        getter.assert_not_called()

    def test_missing_server_token_returns_404(self):
        settings.catalyst_diagnostic_token = None
        with patch("app.diagnostic_routes.get_catalyst_storage") as getter:
            response = self.client.post(
                "/api/diagnostics/catalyst-stratus",
                headers={HEADER: TOKEN},
            )
        self.assertEqual(response.status_code, 404)
        getter.assert_not_called()

    def test_incorrect_token_returns_404_and_does_not_initialize_storage(self):
        with patch("app.diagnostic_routes.get_catalyst_storage") as getter:
            response = self.client.post(
                "/api/diagnostics/catalyst-stratus",
                headers={HEADER: "wrong-diagnostic-token"},
            )
        self.assertEqual(response.status_code, 404)
        getter.assert_not_called()

    def test_correct_token_runs_successful_production_smoke_test(self):
        storage = FakeStorage()
        with patch("app.diagnostic_routes.get_catalyst_storage", return_value=storage):
            # The temporary route must never consult the active portfolio provider.
            with patch(
                "app.storage.factory.get_active_storage",
                side_effect=AssertionError("active portfolio storage must not be called"),
            ) as active_getter:
                response = self.client.post(
                    "/api/diagnostics/catalyst-stratus",
                    headers={HEADER: TOKEN},
                )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "PASS")
        self.assertTrue(all(value == "PASS" for value in body["checks"].values()))
        self.assertEqual(storage.objects, {})
        self.assertEqual(len(storage.deleted), 1)
        active_getter.assert_not_called()

    def test_production_configuration_validation_fails_closed(self):
        settings.catalyst_environment = "Development"
        with patch("app.diagnostic_routes.get_catalyst_storage") as getter:
            response = self.client.post(
                "/api/diagnostics/catalyst-stratus",
                headers={HEADER: TOKEN},
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "FAIL")
        self.assertEqual(body["checks"]["production_configuration"], "FAIL")
        getter.assert_not_called()

    def test_failed_upload_attempt_still_cleans_partial_object(self):
        storage = FakeStorage(fail_upload_after_write=True)
        report = run_stratus_smoke_test(
            storage, key_prefix="smoke-tests/render"
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["checks"]["upload"], "FAIL")
        self.assertEqual(report["checks"]["cleanup"], "PASS")
        self.assertEqual(storage.objects, {})
        self.assertEqual(len(storage.deleted), 1)

    def test_active_portfolio_provider_remains_database(self):
        settings.portfolio_storage_provider = "database"
        settings.catalyst_stratus_enabled = False
        self.assertIsNone(get_active_storage())

    def test_production_configuration_rejects_wrong_bucket_and_endpoints(self):
        from app.diagnostic_routes import _is_production_configuration

        settings.catalyst_stratus_bucket = "wrong-bucket"
        self.assertFalse(_is_production_configuration())
        settings.catalyst_stratus_bucket = EXPECTED_BUCKET
        settings.catalyst_accounts_url = "https://accounts.zoho.com"
        self.assertFalse(_is_production_configuration())
        settings.catalyst_accounts_url = "https://accounts.zoho.in"
        settings.catalyst_project_domain = "https://api.catalyst.zoho.com"
        self.assertFalse(_is_production_configuration())


if __name__ == "__main__":
    unittest.main(verbosity=2)
