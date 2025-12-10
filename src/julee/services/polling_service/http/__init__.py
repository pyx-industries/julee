"""
HTTP polling service implementation.

This module provides HTTP-specific polling functionality for the
PollingService protocol, including REST APIs, webhooks, and other
HTTP-based data sources.
"""

from .http_polling_service import HttpPollingService

__all__ = [
    "HttpPollingService",
]
