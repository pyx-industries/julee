"""
HTTP polling implementation.

This module provides HTTP-specific polling functionality for the polling
contrib module.
"""

from .http_polling_service import HttpPollingService

__all__ = [
    "HttpPollingService",
]
