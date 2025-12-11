"""
HTTP implementation of the PollerService protocol.

This module provides HTTP-specific polling functionality including
REST API endpoints, webhooks, and other HTTP-based data sources.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx

from julee.contrib.polling.domain.models import PollingConfig, PollingResult
from julee.contrib.polling.domain.services import PollerService


class HttpPollerService(PollerService):
    """HTTP implementation of PollerService protocol."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient()

    async def poll_endpoint(self, config: PollingConfig) -> PollingResult:
        """Poll an HTTP endpoint."""
        try:
            # Extract HTTP-specific params
            url = config.connection_params["url"]
            headers = config.connection_params.get("headers", {})
            method = config.polling_params.get("method", "GET")
            auth_params = config.connection_params.get("auth", {})

            # Make HTTP request
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                timeout=config.timeout_seconds,
                **auth_params,
            )

            content = response.content
            content_hash = hashlib.sha256(content).hexdigest()

            # Only consider 2xx status codes as successful
            success = 200 <= response.status_code < 300

            return PollingResult(
                success=success,
                content=content if success else b"",
                content_hash=content_hash if success else None,
                polled_at=datetime.now(timezone.utc),
                metadata={
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                    "url": url,
                    "method": method,
                },
            )

        except Exception as e:
            return PollingResult(
                success=False,
                content=b"",
                error_message=str(e),
                polled_at=datetime.now(timezone.utc),
                metadata={"error_type": type(e).__name__},
            )

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self) -> "HttpPollerService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
