"""
Unit tests for HttpPollingService.

This module tests the HTTP polling service implementation using httpx's
built-in MockTransport for mocking HTTP responses. Tests use table-based
parametrization for comprehensive coverage of different scenarios.
"""

import hashlib

import httpx
import pytest

from julee.services.polling_service import PollingConfig, PollingProtocol
from julee.services.polling_service.http import HttpPollingService


class TestHttpPollingServicePollEndpoint:
    """Test the poll_endpoint method of HttpPollingService."""

    @pytest.mark.parametrize(
        "status_code,content,expected_success,description",
        [
            (200, b"test content", True, "HTTP 200 with content"),
            (201, b"created", True, "HTTP 201 created"),
            (204, b"", True, "HTTP 204 no content"),
            (299, b"success boundary", True, "HTTP 299 (2xx boundary)"),
            (300, b"redirect", False, "HTTP 300 redirect (not 2xx)"),
            (404, b"not found", False, "HTTP 404 client error"),
            (418, b"teapot", False, "HTTP 418 client error"),
            (500, b"server error", False, "HTTP 500 server error"),
            (502, b"bad gateway", False, "HTTP 502 bad gateway"),
            (503, b"unavailable", False, "HTTP 503 service unavailable"),
        ],
    )
    @pytest.mark.asyncio
    async def test_poll_endpoint_status_codes(
        self, status_code: int, content: bytes, expected_success: bool, description: str
    ):
        """Test poll_endpoint with various HTTP status codes."""

        def handler(request):
            return httpx.Response(status_code=status_code, content=content)

        mock_transport = httpx.MockTransport(handler)

        async with HttpPollingService() as service:
            service.client = httpx.AsyncClient(transport=mock_transport)

            config = PollingConfig(
                endpoint_identifier="test-api",
                polling_protocol=PollingProtocol.HTTP,
                connection_params={"url": "https://example.com/api"},
            )

            result = await service.poll_endpoint(config)

            assert result.success == expected_success, f"Failed for {description}"
            if expected_success:
                assert result.content == content
                assert result.content_hash is not None
            else:
                assert result.content == b""
                assert result.content_hash is None
            assert result.metadata["status_code"] == status_code

    @pytest.mark.parametrize(
        "exception_type,description",
        [
            (httpx.ConnectTimeout, "Connection timeout"),
            (httpx.ReadTimeout, "Read timeout"),
            (httpx.ConnectError, "Connection error"),
            (httpx.RequestError, "Generic request error"),
        ],
    )
    @pytest.mark.asyncio
    async def test_poll_endpoint_network_errors(
        self, exception_type: type, description: str
    ):
        """Test poll_endpoint with various network errors."""

        def handler(request):
            raise exception_type("Mock network error")

        mock_transport = httpx.MockTransport(handler)

        async with HttpPollingService() as service:
            service.client = httpx.AsyncClient(transport=mock_transport)

            config = PollingConfig(
                endpoint_identifier="test-api",
                polling_protocol=PollingProtocol.HTTP,
                connection_params={"url": "https://example.com/api"},
            )

            result = await service.poll_endpoint(config)

            assert result.success is False, f"Should fail for {description}"
            assert result.content == b""
            assert "Mock network error" in result.error_message
            assert result.metadata["error_type"] == exception_type.__name__

    @pytest.mark.asyncio
    async def test_poll_endpoint_content_hash_generation(self):
        """Test that poll_endpoint generates correct content hash."""
        test_content = b"test content for hashing"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        def handler(request):
            return httpx.Response(status_code=200, content=test_content)

        mock_transport = httpx.MockTransport(handler)

        async with HttpPollingService() as service:
            service.client = httpx.AsyncClient(transport=mock_transport)

            config = PollingConfig(
                endpoint_identifier="test-api",
                polling_protocol=PollingProtocol.HTTP,
                connection_params={"url": "https://example.com/api"},
            )

            result = await service.poll_endpoint(config)

            assert result.success is True
            assert result.content == test_content
            assert result.content_hash == expected_hash

    @pytest.mark.asyncio
    async def test_poll_endpoint_uses_config_parameters(self):
        """Test that poll_endpoint uses configuration parameters correctly."""
        captured_request = None

        def handler(request):
            nonlocal captured_request
            captured_request = request
            return httpx.Response(status_code=200, content=b"success")

        mock_transport = httpx.MockTransport(handler)

        async with HttpPollingService() as service:
            service.client = httpx.AsyncClient(transport=mock_transport)

            config = PollingConfig(
                endpoint_identifier="test-api",
                polling_protocol=PollingProtocol.HTTP,
                connection_params={
                    "url": "https://api.example.com/data",
                    "headers": {"Authorization": "Bearer token123"},
                },
                polling_params={"method": "POST"},
                timeout_seconds=30,
            )

            result = await service.poll_endpoint(config)

            assert result.success is True
            assert captured_request is not None
            assert str(captured_request.url) == "https://api.example.com/data"
            assert captured_request.method == "POST"
            assert captured_request.headers["Authorization"] == "Bearer token123"
