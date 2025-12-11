"""
Temporal infrastructure for the polling contrib module.

This module contains the temporal-specific implementations for the polling
contrib module, including activity registrations, workflow proxies, and
activity name constants.

This keeps all polling-temporal integration within the contrib module,
maintaining proper dependency direction (contrib imports from core, not vice versa).
"""

from .activities import TemporalPollerService
from .activity_names import POLLING_SERVICE_ACTIVITY_BASE
from .proxies import WorkflowPollerServiceProxy

__all__ = [
    "TemporalPollerService",
    "POLLING_SERVICE_ACTIVITY_BASE",
    "WorkflowPollerServiceProxy",
]
