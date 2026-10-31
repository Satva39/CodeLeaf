"""Storage provider contracts and typed results for portfolio archives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Iterator, Protocol


@dataclass(frozen=True)
class StoredObject:
    key: str
    size_bytes: int
    checksum_sha256: str
    bucket: str


class StorageError(RuntimeError):
    """A provider operation failed without exposing credentials or file contents."""

    def __init__(self, message: str, *, upload_id: str | None = None) -> None:
        super().__init__(message)
        self.upload_id = upload_id


class ObjectStorage(Protocol):
    bucket_name: str

    def upload_stream(
        self, key: str, stream: BinaryIO, *, expected_size: int | None = None
    ) -> StoredObject: ...

    def object_exists(self, key: str) -> bool: ...

    def object_metadata(self, key: str) -> dict: ...

    def iter_download(self, key: str, *, part_size_mb: int = 20) -> Iterator[bytes]: ...

    def download_range(self, key: str, start: int, end: int) -> bytes: ...

    def delete_object(self, key: str) -> bool: ...
