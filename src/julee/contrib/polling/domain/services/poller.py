"""
PollerService protocol for external endpoint polling operations.

This module defines the PollerService protocol that handles interactions
with various types of external endpoints for data polling and change detection.

Concrete implementations of this protocol are provided for different polling
mechanisms and are created via factory functions.
"""

from typing import Protocol, runtime_checkable

from ..models.polling_config import PollingConfig, PollingResult


@runtime_checkable
class PollerService(Protocol):
    """
    Protocol for polling external endpoints for data.

    This protocol defines the interface for a poller service that can perform
    individual poll operations on different endpoint types. Implementations
    handle the specifics of different polling mechanisms.
    """

    async def poll_endpoint(self, config: PollingConfig) -> PollingResult:
        """
        Poll an endpoint according to the provided configuration.

        Args:
            config: PollingConfig containing endpoint details and parameters

        Returns:
            PollingResult with success status, content, and metadata

        Raises:
            PollingError: When polling operation fails
        """
        ...
