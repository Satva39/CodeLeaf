"""Mocked Catalyst adapter checks; this never contacts a real Catalyst account."""
from __future__ import annotations

import hashlib
import io
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage import factory as storage_factory  # noqa: E402
from app.storage.catalyst_stratus import CatalystStratusStorage  # noqa: E402
from app.storage.base import StorageError  # noqa: E402


class FakeObject:
    def __init__(self, bucket, key):
        self.bucket = bucket
        self.key = key

    def get_details(self):
        payload = self.bucket.objects[self.key]
        return {"key": self.key, "size": len(payload), "content_type": "application/zip"}


class FakeBucket:
    def __init__(self):
        self.objects = {}
        self.parts = {}
        self.deleted = []
        self.put_failures_remaining = 0
        self.part_failures_remaining = 0
        self.always_fail_put = False
        self.corrupt_put = False
        self.fail_head = False
        self.always_fail_part = False

    def put_object(self, key, body, options=None):
        if hasattr(body, "read"):
            body = body.read()
        assert isinstance(body, bytes)
        if self.always_fail_put or self.put_failures_remaining:
            self.put_failures_remaining = max(0, self.put_failures_remaining - 1)
            raise RuntimeError("simulated upload failure after consuming stream")
        if self.corrupt_put and body:
            body = body[:-1] + (b"x" if body[-1:] != b"x" else b"y")
        self.objects[key] = body
        return {"status": "success"}

    def head_object(self, key, throw_err=False):
        if self.fail_head:
            raise PermissionError("simulated expired/invalid authorization")
        return key in self.objects

    def object(self, key):
        return FakeObject(self, key)

    def get_object(self, key, options=None):
        payload = self.objects[key]
        start, end = map(int, options["range"].split("-"))
        return payload[start : end + 1]

    def initiate_multipart_upload(self, *, key):
        self.parts[key] = []
        return {"upload_id": "fake-upload-id"}

    def upload_part(self, *, key, upload_id, part_number, body):
        data = body.read() if hasattr(body, "read") else body
        assert isinstance(data, bytes)
        if self.always_fail_part or self.part_failures_remaining:
            self.part_failures_remaining = max(0, self.part_failures_remaining - 1)
            raise RuntimeError("simulated part failure after consuming stream")
        self.parts[key].append((part_number, data))
        return {"status": "success"}

    def complete_multipart_upload(self, *, key, upload_id):
        self.objects[key] = b"".join(data for _, data in sorted(self.parts[key]))
        return {"status": "success"}

    def delete_object(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)
        return {"status": "success"}


class FakeTransferManager:
    def __init__(self, bucket):
        self.bucket = bucket

    def get_iterable_object(self, key, part_size_mb):
        payload = self.bucket.objects[key]
        block_size = 7
        return [payload[offset : offset + block_size] for offset in range(0, len(payload), block_size)]


def make_storage(bucket, **kwargs):
    return CatalystStratusStorage(
        project_id="test-project",
        project_zaid="test-zaid",
        environment="Development",
        client_id="client-id",
        client_secret="client-secret",
        refresh_token="refresh-token",
        bucket_name="test-bucket",
        verify_checksum=True,
        max_retries=2,
        bucket=bucket,
        transfer_manager_factory=FakeTransferManager,
        **kwargs,
    )


def main() -> None:
    bucket = FakeBucket()
    storage = make_storage(bucket)
    payload = b"a mocked CodeLeaf ZIP archive payload"

    # A bytes payload can be safely reused when the SDK call fails before success.
    bucket.put_failures_remaining = 1
    result = storage.upload_stream(
        "projects/test-uuid/archive.zip", io.BytesIO(payload), expected_size=len(payload)
    )
    assert result.size_bytes == len(payload)
    assert result.checksum_sha256 == hashlib.sha256(payload).hexdigest()
    assert storage.object_exists(result.key)
    assert storage.object_metadata(result.key)["size"] == len(payload)
    assert b"".join(storage.iter_download(result.key)) == payload
    assert storage.download_range(result.key, 3, 8) == payload[3:9]
    assert storage.checksum_object(result.key) == result.checksum_sha256

    # Exercise multipart part-byte retries and remote checksum validation.
    multipart_bucket = FakeBucket()
    multipart_bucket.part_failures_remaining = 1
    multipart_storage = make_storage(multipart_bucket, multipart_part_size_mb=1)
    multipart_payload = (b"multipart-data-" * 100_000)[:2_300_000]
    with patch("app.storage.catalyst_stratus.MULTIPART_THRESHOLD_BYTES", 1):
        multipart_result = multipart_storage.upload_stream(
            "projects/test-uuid/multipart.zip",
            io.BytesIO(multipart_payload),
            expected_size=len(multipart_payload),
        )
    assert multipart_bucket.objects[multipart_result.key] == multipart_payload
    assert multipart_result.checksum_sha256 == hashlib.sha256(multipart_payload).hexdigest()

    assert storage.delete_object(result.key) is True
    assert not storage.object_exists(result.key)
    assert not storage.object_exists("projects/missing/archive.zip")

    # Exhausted multipart failures retain the upload id for manual reconciliation.
    failed_part_bucket = FakeBucket()
    failed_part_bucket.always_fail_part = True
    try:
        with patch("app.storage.catalyst_stratus.MULTIPART_THRESHOLD_BYTES", 1):
            make_storage(failed_part_bucket, multipart_part_size_mb=1).upload_stream(
                "projects/test-uuid/incomplete.zip",
                io.BytesIO(b"multipart-failure-payload"),
                expected_size=len(b"multipart-failure-payload"),
            )
    except StorageError as exc:
        assert exc.upload_id == "fake-upload-id"
    else:
        raise AssertionError("Multipart failure must expose its upload ID for reconciliation")

    # A remote object with a different payload must fail end-to-end checksum validation.
    corrupt_bucket = FakeBucket()
    corrupt_bucket.corrupt_put = True
    try:
        make_storage(corrupt_bucket).upload_stream(
            "projects/test-uuid/corrupt.zip", io.BytesIO(payload), expected_size=len(payload)
        )
    except StorageError as exc:
        assert "checksum" in str(exc).lower()
    else:
        raise AssertionError("Checksum mismatch must fail closed")

    # Expired/invalid auth is surfaced as a safe provider error, not a credential leak.
    unauthorized_bucket = FakeBucket()
    unauthorized_bucket.fail_head = True
    try:
        make_storage(unauthorized_bucket).object_exists("projects/test-uuid/archive.zip")
    except StorageError:
        pass
    else:
        raise AssertionError("Authorization failure must raise StorageError")

    # Exhausted failures surface as a typed, non-secret exception.
    failed_bucket = FakeBucket()
    failed_bucket.always_fail_put = True
    try:
        make_storage(failed_bucket).upload_stream(
            "projects/test-uuid/fail.zip", io.BytesIO(payload), expected_size=len(payload)
        )
    except StorageError:
        pass
    else:
        raise AssertionError("Exhausted upload failures must raise StorageError")

    for bad_key in ("../escape.zip", "/absolute.zip", "folder\\bad.zip", "a # b.zip"):
        try:
            storage.validate_key(bad_key)
        except StorageError:
            pass
        else:
            raise AssertionError(f"Expected unsafe key to be rejected: {bad_key!r}")

    # Verify the official third-party SDK initialization argument mapping without
    # installing credentials or contacting a live Catalyst project.
    credential_calls = []
    option_calls = []
    initialize_calls = []
    auth_bucket = FakeBucket()

    class FakeApp:
        def stratus(self):
            return self

        def bucket(self, bucket_name):
            assert bucket_name == "auth-test-bucket"
            return auth_bucket

    sdk_module = types.ModuleType("zcatalyst_sdk")
    sdk_module.__path__ = []
    http_client_module = types.ModuleType("zcatalyst_sdk._http_client")

    class FakeHttpClient:
        URL_SEPARATOR = "/"

        def request(self, method, url=None, path=None, user=None, catalyst_service=None, external=False, **kwargs):
            return path

    http_client_module.HttpClient = FakeHttpClient
    http_client_module.URL_SEPARATOR = "/"
    credentials_module = types.ModuleType("zcatalyst_sdk.credentials")
    credentials_module.RefreshTokenCredential = lambda values: credential_calls.append(values) or "credential-object"
    types_module = types.ModuleType("zcatalyst_sdk.types")
    types_module.ICatalystOptions = lambda **values: option_calls.append(values) or "options-object"
    sdk_module.credentials = credentials_module
    sdk_module.initialize_app = lambda **values: initialize_calls.append(values) or FakeApp()
    with patch.dict(sys.modules, {
        "zcatalyst_sdk": sdk_module,
        "zcatalyst_sdk._http_client": http_client_module,
        "zcatalyst_sdk.credentials": credentials_module,
        "zcatalyst_sdk.types": types_module,
    }):
        auth_storage = CatalystStratusStorage(
            project_id="project-id", project_zaid="project-zaid", environment="Development",
            client_id="client-id", client_secret="client-secret", refresh_token="refresh-token",
            bucket_name="auth-test-bucket", project_domain="https://api.catalyst.zoho.in",
            accounts_url="https://accounts.zoho.in",
            stratus_resource_suffix=".zohostratus.in",
        )
        assert auth_storage._get_bucket() is auth_bucket
    assert credential_calls == [{"refresh_token": "refresh-token", "client_id": "client-id", "client_secret": "client-secret"}]
    assert option_calls == [{"project_id": "project-id", "project_key": "project-zaid", "project_domain": "https://api.catalyst.zoho.in", "environment": "Development"}]
    assert os.environ["X_ZOHO_CATALYST_ACCOUNTS_URL"] == "https://accounts.zoho.in"
    assert os.environ["X_ZOHO_CATALYST_CONSOLE_URL"] == "https://api.catalyst.zoho.in"
    assert os.environ["X_ZOHO_STRATUS_RESOURCE_SUFFIX"] == ".zohostratus.in"

    # Verify the SDK compatibility layer normalizes no-service paths but leaves
    # service-prefixed and explicit-URL requests unchanged.
    fake_http = FakeHttpClient()
    assert fake_http.request("POST", path="/oauth/v2/token") == "oauth/v2/token"
    assert fake_http.request("POST", path="/baas/v1/project/test/bucket/signature") == "baas/v1/project/test/bucket/signature"
    assert fake_http.request("POST", path="/objects", catalyst_service="stratus") == "/objects"
    assert fake_http.request("POST", url="https://example.test/objects", path="/objects") == "/objects"

    assert initialize_calls[0]["credential"] == "credential-object"
    assert initialize_calls[0]["options"] == "options-object"

    # Unconfigured Catalyst must not prevent the database-only configuration.
    storage_factory._cached_catalyst_storage.cache_clear()
    with patch.object(storage_factory.settings, "catalyst_project_id", None), \
         patch.object(storage_factory.settings, "catalyst_project_zaid", None):
        assert storage_factory.get_catalyst_storage() is None
        assert storage_factory.get_active_storage() is None
    storage_factory._cached_catalyst_storage.cache_clear()

    print("Mocked Stratus checks passed: SDK credential mapping, small/multipart upload, retries, authorization failure, range/download, checksum mismatch, delete and disabled configuration.")
    print("No real Catalyst account was contacted; run catalyst_stratus_smoke_test.py separately for live connectivity.")


if __name__ == "__main__":
    main()
