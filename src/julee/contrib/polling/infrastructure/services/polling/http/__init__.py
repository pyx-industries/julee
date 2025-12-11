"""
HTTP polling implementation.

This module provides HTTP-specific polling functionality for the polling
contrib module.
"""

from .http_poller_service import HttpPollerService

__all__ = [
    "HttpPollerService",
]
