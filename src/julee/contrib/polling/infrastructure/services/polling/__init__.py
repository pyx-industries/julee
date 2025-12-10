"""
Polling infrastructure services.

This module contains the concrete implementations of polling services
for different protocols and mechanisms.
"""

from .http import HttpPollingService

__all__ = [
    "HttpPollingService",
]
