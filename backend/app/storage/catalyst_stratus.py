"""Zoho Catalyst Stratus adapter using the official Catalyst Python SDK.

This module imports the SDK lazily so CodeLeaf continues to run with its existing
PostgreSQL-only storage configuration when Catalyst is not configured.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from typing import BinaryIO, Iterator

from .base import StorageError, StoredObject

logger = logging.getLogger(__name__)
MULTIPART_THRESHOLD_BYTES = 100 * 1024 * 1024
MAX_MULTIPART_PARTS = 1000


class CatalystStratusStorage:
    def __init__(
        self,
        *,
        project_id: str,
        project_zaid: str,
        environment: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        bucket_name: str,
        project_domain: str = "https://api.catalyst.zoho.in",
        accounts_url: str = "https://accounts.zoho.in",
        stratus_resource_suffix: str = ".zohostratus.in",
        multipart_part_size_mb: int = 25,
        max_retries: int = 3,
        verify_checksum: bool = True,
        bucket=None,
        transfer_manager_factory=None,
    ) -> None:
        self.project_id = project_id
        self.project_zaid = project_zaid
        self.environment = environment
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.bucket_name = bucket_name
        self.project_domain = project_domain.rstrip("/")
        self.accounts_url = accounts_url.rstrip("/")
        self.stratus_resource_suffix = (
            stratus_resource_suffix
            if stratus_resource_suffix.startswith(".")
            else f".{stratus_resource_suffix}"
        )
        self.multipart_part_size_mb = multipart_part_size_mb
        self.max_retries = max_retries
        self.verify_checksum = verify_checksum
        self._bucket = bucket
        self._transfer_manager_factory = transfer_manager_factory

    @staticmethod
    def validate_key(key: str) -> str:
        """Reject provider-unsupported characters and unsafe, non-canonical keys."""
        if not isinstance(key, str) or not key or len(key) > 900:
            raise StorageError("Invalid Stratus object key.")
        if any(char in key for char in ('"', "<", ">", "#", "\\", "|", " ")):
            raise StorageError("The Stratus object key contains unsupported characters.")
        if key.startswith("/") or key.endswith("/") or ".." in key.split("/"):
            raise StorageError("The Stratus object key is not a safe relative path.")
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", key):
            raise StorageError("The Stratus object key contains unsupported characters.")
        return key

    @staticmethod
    def _install_sdk_url_compatibility() -> None:
        """Normalize SDK paths before its base-URL concatenation (SDK 1.5.0).

        Catalyst SDK 1.5.0 builds ``base_url + "/" + path``. Its OAuth and
        Stratus-signature callers pass paths beginning with ``/``, which creates
        malformed URLs with a doubled separator. Normalize only relative-path
        requests that do not specify a Catalyst service or an absolute URL.
        Service-prefixed requests are left untouched.
        """
        from zcatalyst_sdk._http_client import HttpClient, URL_SEPARATOR

        if URL_SEPARATOR != "/":
            return

        current = HttpClient.request
        if getattr(current, "_codeleaf_path_compatibility", False):
            return

        def codeleaf_compatible_request(client, *args, **kwargs):
            service = kwargs.get("catalyst_service")
            if service is None and len(args) > 4:
                service = args[4]

            request_url = kwargs.get("url")
            if request_url is None and len(args) > 1:
                request_url = args[1]

            request_path = kwargs.get("path")
            if request_path is None and len(args) > 2:
                request_path = args[2]

            if (
                service is None
                and request_url is None
                and isinstance(request_path, str)
                and request_path.startswith("/")
            ):
                normalized_path = request_path.lstrip("/")
                if "path" in kwargs:
                    kwargs["path"] = normalized_path
                elif len(args) > 2:
                    args = list(args)
                    args[2] = normalized_path
                    args = tuple(args)

            return current(client, *args, **kwargs)

        codeleaf_compatible_request._codeleaf_path_compatibility = True
        HttpClient.request = codeleaf_compatible_request

    def _get_bucket(self):
        if self._bucket is not None:
            return self._bucket
        try:
            # The SDK reads these variables when its constants module is imported.
            # Set them before importing the SDK so all API and Stratus URLs use the
            # same Catalyst data centre as this project.
            os.environ["X_ZOHO_CATALYST_ACCOUNTS_URL"] = self.accounts_url
            os.environ["X_ZOHO_CATALYST_CONSOLE_URL"] = self.project_domain
            os.environ["X_ZOHO_STRATUS_RESOURCE_SUFFIX"] = self.stratus_resource_suffix

            import zcatalyst_sdk
            self._install_sdk_url_compatibility()
            from zcatalyst_sdk import credentials
            from zcatalyst_sdk.types import ICatalystOptions

            credential = credentials.RefreshTokenCredential(
                {
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            options = ICatalystOptions(
                project_id=self.project_id,
                project_key=self.project_zaid,
                project_domain=self.project_domain,
                environment=self.environment,
            )
            app = zcatalyst_sdk.initialize_app(
                credential=credential,
                options=options,
                name="CodeLeafPortfolioStorage",
            )
            self._bucket = app.stratus().bucket(self.bucket_name)
            return self._bucket
        except Exception as exc:  # SDK errors vary by auth/provider version.
            raise StorageError(
                "Catalyst Stratus could not be initialized. Check the server-side credentials and project configuration."
            ) from exc

    def _transfer_manager(self):
        try:
            if self._transfer_manager_factory:
                return self._transfer_manager_factory(self._get_bucket())
            from zcatalyst_sdk.stratus.transfer_manager import TransferManager

            return TransferManager(self._get_bucket())
        except Exception as exc:
            raise StorageError("Catalyst's Stratus Transfer Manager is unavailable.") from exc

    def _retry(self, operation, *, description: str):
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return operation()
            except Exception as exc:  # SDK exceptions do not share one stable type.
                last_error = exc
                logger.warning(
                    "Catalyst Stratus %s failed on attempt %s/%s (%s).",
                    description,
                    attempt + 1,
                    self.max_retries + 1,
                    type(exc).__name__,
                )
                if attempt >= self.max_retries:
                    break
                time.sleep(min(2 ** attempt, 4))
        raise StorageError(f"Catalyst {description} failed after retries.") from last_error

    @staticmethod
    def _sha256_stream(stream: BinaryIO) -> tuple[int, str]:
        hasher = hashlib.sha256()
        total = 0
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            total += len(block)
            hasher.update(block)
        return total, hasher.hexdigest()

    def upload_stream(
        self, key: str, stream: BinaryIO, *, expected_size: int | None = None
    ) -> StoredObject:
        """Upload small objects as bytes and large objects as multipart chunks."""
        key = self.validate_key(key)
        try:
            stream.seek(0)
            source_size = self._stream_size(stream)
            if expected_size is not None and source_size != expected_size:
                raise StorageError("Source archive size changed before Catalyst upload.")
            if source_size <= 0:
                raise StorageError("Cannot upload an empty project archive.")
            stream.seek(0)
            bucket = self._get_bucket()
            upload_id: str | None = None

            if source_size >= MULTIPART_THRESHOLD_BYTES:
                part_size = self.multipart_part_size_mb * 1024 * 1024
                part_count = (source_size + part_size - 1) // part_size
                if part_count > MAX_MULTIPART_PARTS:
                    raise StorageError("The archive requires more Stratus parts than the SDK supports.")
                init_response = self._retry(
                    lambda: bucket.initiate_multipart_upload(key=key),
                    description="multipart initialization",
                )
                upload_id = str((init_response or {}).get("upload_id") or "") or None
                if not upload_id:
                    raise StorageError("Catalyst did not return a multipart upload identifier.")
                part_number = 1
                try:
                    while True:
                        part = stream.read(part_size)
                        if not part:
                            break
                        self._retry(
                            lambda p=part, n=part_number: self._upload_part(
                                bucket, key, upload_id, n, p
                            ),
                            description=f"multipart part {part_number}",
                        )
                        part_number += 1
                    if part_number - 1 != part_count:
                        raise StorageError("Multipart source length changed during upload.", upload_id=upload_id)
                    self._retry(
                        lambda: bucket.complete_multipart_upload(key=key, upload_id=upload_id),
                        description="multipart completion",
                    )
                except StorageError as exc:
                    if exc.upload_id is None:
                        exc.upload_id = upload_id
                    # The current documented Python SDK does not expose an abort operation.
                    # Keep the upload ID so an operator can identify the pending upload.
                    raise
            else:
                # The installed Catalyst SDK validates the body type. It accepts bytes,
                # but does not accept BytesIO objects, so buffer small objects as bytes.
                _, source_digest = self._sha256_stream(stream)
                stream.seek(0)
                payload = stream.read()
                if not isinstance(payload, bytes) or len(payload) != source_size:
                    raise StorageError(
                        "Could not read the complete archive for Catalyst upload."
                    )

                options = {
                    "overwrite": "true",
                    "content_type": "application/zip",
                    "meta_data": {"sha256": source_digest},
                }

                # A bytes payload can be safely reused across retries.
                self._retry(
                    lambda: bucket.put_object(key, payload, options),
                    description="object upload",
                )

            metadata = self.object_metadata(key)
            remote_size = int(metadata.get("size") or 0)
            if remote_size != source_size:
                raise StorageError("Catalyst object size does not match the source archive.", upload_id=upload_id)

            if source_size >= MULTIPART_THRESHOLD_BYTES:
                # The multipart pass is also the source SHA pass, but stream position is
                # at EOF and a remote read-back is required for an end-to-end verification.
                stream.seek(0)
                _, source_digest = self._sha256_stream(stream)
            if self.verify_checksum:
                remote_digest = self.checksum_object(key)
                if remote_digest != source_digest:
                    raise StorageError("Catalyst object checksum does not match the source archive.", upload_id=upload_id)
            else:
                remote_digest = source_digest
            return StoredObject(
                key=key,
                size_bytes=source_size,
                checksum_sha256=remote_digest,
                bucket=self.bucket_name,
            )
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("Catalyst Stratus upload failed.") from exc

    @staticmethod
    def _stream_size(stream: BinaryIO) -> int:
        current = stream.tell()
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(current)
        return int(size)

    @staticmethod
    def _upload_part(bucket, key: str, upload_id: str, part_number: int, part: bytes):
        if not isinstance(part, bytes) or not part:
            raise StorageError("Invalid or empty multipart upload part.")
        return bucket.upload_part(
            key=key,
            upload_id=upload_id,
            part_number=part_number,
            body=part,
        )

    def object_exists(self, key: str) -> bool:
        key = self.validate_key(key)
        try:
            return bool(self._get_bucket().head_object(key, throw_err=False))
        except Exception as exc:
            raise StorageError("Catalyst could not check object availability.") from exc

    def object_metadata(self, key: str) -> dict:
        key = self.validate_key(key)
        try:
            if not self.object_exists(key):
                raise StorageError("Catalyst object was not found or is not accessible.")
            details = self._get_bucket().object(key).get_details()
            if not isinstance(details, dict):
                raise StorageError("Catalyst returned invalid object metadata.")
            return details
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("Catalyst object metadata could not be retrieved.") from exc

    def iter_objects(self, *, prefix: str = "projects/", page_size: int = 100):
        """List bucket objects through the SDK's documented paginated interface."""
        if not isinstance(prefix, str) or not prefix or len(prefix) > 500:
            raise StorageError("Invalid Stratus object listing prefix.")
        if page_size < 1 or page_size > 1000:
            raise StorageError("Stratus object listing page size must be between 1 and 1000.")
        bucket = self._get_bucket()
        continuation_token = None
        try:
            while True:
                page = bucket.list_paged_objects(
                    page_size,
                    prefix,
                    continuation_token,
                    folder_listing=False,
                    order_by="asc",
                )
                if not isinstance(page, dict):
                    raise StorageError("Catalyst returned an invalid object listing page.")
                for item in page.get("contents") or []:
                    if isinstance(item, dict):
                        yield item
                if not page.get("truncated"):
                    break
                continuation_token = page.get("next_continuation_token")
                if not continuation_token:
                    raise StorageError("Catalyst truncated an object listing without a continuation token.")
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("Catalyst object listing failed.") from exc

    def iter_download(self, key: str, *, part_size_mb: int = 20) -> Iterator[bytes]:
        key = self.validate_key(key)
        if not self.object_exists(key):
            raise StorageError("Catalyst project archive is missing or inaccessible.")
        try:
            parts = self._transfer_manager().get_iterable_object(key, part_size_mb)
            for part in parts:
                if part:
                    yield bytes(part)
        except Exception as exc:
            logger.warning("Catalyst Stratus streamed download failed (%s).", type(exc).__name__)
            raise StorageError("Catalyst project archive download failed.") from exc

    def download_range(self, key: str, start: int, end: int) -> bytes:
        key = self.validate_key(key)
        if start < 0 or end < start:
            raise StorageError("Invalid byte range.")
        try:
            payload = self._get_bucket().get_object(key, {"range": f"{start}-{end}"})
            return bytes(payload)
        except Exception as exc:
            raise StorageError("Catalyst range download failed.") from exc

    def checksum_object(self, key: str) -> str:
        hasher = hashlib.sha256()
        for block in self.iter_download(key):
            hasher.update(block)
        return hasher.hexdigest()

    def delete_object(self, key: str) -> bool:
        key = self.validate_key(key)
        try:
            bucket = self._get_bucket()
            # Call the documented delete operation directly. A preceding HEAD check
            # is not authoritative: Catalyst documents that a false availability
            # result can also mean insufficient permission. The row is retained until
            # this delete call itself succeeds.
            self._retry(
                lambda: bucket.delete_object(key),
                description="object deletion",
            )
            return True
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("Catalyst project archive deletion failed.") from exc
