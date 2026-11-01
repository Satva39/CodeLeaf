"""Explicit provider selection with a database-only safe fallback."""
from __future__ import annotations

import logging
from functools import lru_cache

from ..config import settings
from .catalyst_stratus import CatalystStratusStorage

logger = logging.getLogger(__name__)


def _catalyst_configured() -> bool:
    required = (
        settings.catalyst_project_id,
        settings.catalyst_project_zaid,
        settings.catalyst_client_id,
        settings.catalyst_client_secret,
        settings.catalyst_refresh_token,
        settings.catalyst_stratus_bucket,
    )
    return all(value and str(value).strip() for value in required)


@lru_cache(maxsize=1)
def _cached_catalyst_storage() -> CatalystStratusStorage:
    return CatalystStratusStorage(
        project_id=settings.catalyst_project_id or "",
        project_zaid=settings.catalyst_project_zaid or "",
        environment=settings.catalyst_environment,
        client_id=settings.catalyst_client_id or "",
        client_secret=settings.catalyst_client_secret or "",
        refresh_token=settings.catalyst_refresh_token or "",
        bucket_name=settings.catalyst_stratus_bucket or "",
        project_domain=settings.catalyst_project_domain,
        accounts_url=settings.catalyst_accounts_url,
        stratus_resource_suffix=settings.catalyst_stratus_resource_suffix,
        multipart_part_size_mb=settings.catalyst_multipart_part_size_mb,
        max_retries=settings.catalyst_max_retries,
        verify_checksum=settings.catalyst_verify_upload_checksum,
    )


def get_catalyst_storage() -> CatalystStratusStorage | None:
    """Return a configured adapter for reads/migration, independent of write toggle."""
    if not _catalyst_configured():
        return None
    return _cached_catalyst_storage()


def get_active_storage():
    """Return Stratus only when explicitly selected and enabled for new uploads."""
    provider = (settings.portfolio_storage_provider or "database").strip().lower()
    if provider != "catalyst_stratus" or not settings.catalyst_stratus_enabled:
        return None
    storage = get_catalyst_storage()
    if storage is None:
        logger.warning(
            "Catalyst Stratus was selected but is not fully configured; using PostgreSQL archive storage."
        )
    return storage
