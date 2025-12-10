"""
Polling service for external endpoint operations in the Capture, Extract,
Assemble, Publish workflow.

This module provides the polling service protocol and base models for
interacting with various types of external endpoints (HTTP, gRPC, database,
etc.) for data polling and change detection.

The polling service layer handles external integrations for data retrieval
while remaining separate from the repository layer which handles local
metadata persistence. Concrete implementations are organized by polling method
into submodules.
"""

# Re-export core polling service components
from .polling_service import (
    PollingConfig,
    PollingProtocol,
    PollingResult,
    PollingService,
)

__all__ = [
    # Core protocol and models
    "PollingService",
    "PollingConfig",
    "PollingResult",
    "PollingProtocol",
]
