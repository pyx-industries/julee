"""
Polling Contrib Module.

This module provides ready-made polling functionality for external endpoints.
It follows the Julee contrib module pattern, providing a complete polling
solution that can be imported and used by Julee solutions.

The polling module includes:
- Domain models for polling configuration and results
- Service protocols for polling operations
- HTTP implementation for REST API polling
- Co-located tests and examples

Example usage:
    from julee.contrib.polling import PollingConfig, HttpPollingService
    from julee.contrib.polling import PollingProtocol, PollingResult

    # Configure polling
    config = PollingConfig(
        endpoint_identifier="api-v1",
        polling_protocol=PollingProtocol.HTTP,
        connection_params={"url": "https://api.example.com/data"},
        timeout_seconds=30
    )

    # Poll the endpoint
    service = HttpPollingService()
    result = await service.poll_endpoint(config)
"""

from .domain import PollingConfig, PollingProtocol, PollingResult, PollingService
from .infrastructure import HttpPollingService
from .infrastructure.temporal import WorkflowPollingServiceProxy

__all__ = [
    # Domain models
    "PollingConfig",
    "PollingProtocol",
    "PollingResult",
    # Domain services
    "PollingService",
    # Infrastructure implementations
    "HttpPollingService",
    # Temporal integration
    "WorkflowPollingServiceProxy",
]
