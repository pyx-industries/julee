"""
HTTP implementation of the PollingService protocol.

This module provides HTTP-specific polling functionality including
REST API endpoints, webhooks, and other HTTP-based data sources.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict

import httpx

from ..polling_service import PollingConfig, PollingResult, PollingService


class HttpPollingService(PollingService):
    """HTTP implementation of PollingService protocol."""

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

            return PollingResult(
                success=True,
                content=content,
                content_hash=content_hash,
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

    async def test_connection(self, config: PollingConfig) -> bool:
        """Test HTTP endpoint connectivity."""
        try:
            url = config.connection_params["url"]
            response = await self.client.head(url, timeout=10)
            return response.status_code < 500
        except:
            return False

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()
