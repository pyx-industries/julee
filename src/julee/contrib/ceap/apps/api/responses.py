"""API response models for operational endpoints.

These are API-layer concerns (health checks, etc.), not domain objects.
Domain responses live in use_cases/.
"""

from enum import Enum

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    """Service status enumeration."""

    UP = "up"
    DOWN = "down"


class SystemStatus(str, Enum):
    """Overall system status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealthStatus(BaseModel):
    """Health status for individual services."""

    api: ServiceStatus
    temporal: ServiceStatus
    storage: ServiceStatus


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""

    status: SystemStatus
    timestamp: str
    services: ServiceHealthStatus
