"""System API router for health checks and status.

These are operational endpoints, not domain operations.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter
from minio import Minio
from temporalio.client import Client

from julee.contrib.ceap.apps.api.responses import (
    HealthCheckResponse,
    ServiceHealthStatus,
    ServiceStatus,
    SystemStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_temporal_health() -> ServiceStatus:
    """Check if Temporal service is available."""
    try:
        temporal_address = os.getenv(
            "TEMPORAL_ENDPOINT", os.getenv("TEMPORAL_HOST", "localhost:7233")
        )
        _ = await Client.connect(temporal_address, namespace="default")
        return ServiceStatus.UP
    except Exception as e:
        logger.warning("Temporal health check failed: %s", e)
        return ServiceStatus.DOWN


async def check_storage_health() -> ServiceStatus:
    """Check if storage service (Minio) is available."""
    try:
        endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"

        client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        _ = list(client.list_buckets())
        return ServiceStatus.UP
    except Exception as e:
        logger.warning("Storage health check failed: %s", e)
        return ServiceStatus.DOWN


async def check_api_health() -> ServiceStatus:
    """Check if API service is available (self-check)."""
    return ServiceStatus.UP


def determine_overall_status(services: ServiceHealthStatus) -> SystemStatus:
    """Determine overall system status based on service statuses."""
    service_statuses = [services.api, services.temporal, services.storage]

    if all(status == ServiceStatus.UP for status in service_statuses):
        return SystemStatus.HEALTHY
    elif any(status == ServiceStatus.UP for status in service_statuses):
        return SystemStatus.DEGRADED
    else:
        return SystemStatus.UNHEALTHY


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Comprehensive health check endpoint that checks all services."""
    logger.info("Performing health check")

    results = await asyncio.gather(
        check_api_health(),
        check_temporal_health(),
        check_storage_health(),
        return_exceptions=True,
    )

    api_status = results[0]
    temporal_status = results[1]
    storage_status = results[2]

    if isinstance(api_status, Exception):
        logger.error("API health check error: %s", api_status)
        api_status = ServiceStatus.DOWN
    if isinstance(temporal_status, Exception):
        logger.error("Temporal health check error: %s", temporal_status)
        temporal_status = ServiceStatus.DOWN
    if isinstance(storage_status, Exception):
        logger.error("Storage health check error: %s", storage_status)
        storage_status = ServiceStatus.DOWN

    services = ServiceHealthStatus(
        api=ServiceStatus(api_status),
        temporal=ServiceStatus(temporal_status),
        storage=ServiceStatus(storage_status),
    )

    overall_status = determine_overall_status(services)

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )
