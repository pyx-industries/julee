"""
Infrastructure layer for the polling contrib module.

This module contains the concrete implementations of domain protocols
and external system integrations for the polling contrib module.
"""

from .services import HttpPollingService
from .temporal import WorkflowPollingServiceProxy

__all__ = [
    "HttpPollingService",
    "WorkflowPollingServiceProxy",
]
