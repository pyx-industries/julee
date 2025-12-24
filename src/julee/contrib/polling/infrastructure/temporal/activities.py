"""
Temporal activities for the polling contrib module.

This module contains the temporal activity implementations for polling operations.
These activities are registered with Temporal and can be called from workflows
to perform durable polling operations.

By keeping these activities within the contrib module, we maintain proper
dependency direction - contrib modules define their own temporal integration
without requiring the core framework to know about specific contrib modules.
"""

import logging

from julee.core.infrastructure.temporal.decorators import temporal_activity_registration

from ..services.polling.http.http_poller_service import HttpPollerService
from .activity_names import POLLING_SERVICE_ACTIVITY_BASE


@temporal_activity_registration(POLLING_SERVICE_ACTIVITY_BASE)
class TemporalPollerService(HttpPollerService):
    """
    Temporal activity wrapper for PollerService operations.

    This class wraps the HttpPollerService to make it compatible with Temporal
    activities. It inherits all the polling functionality while being registered
    as a Temporal activity that can be called from workflows.

    The temporal activity registration provides durability, retries, and
    observability for polling operations within workflow contexts.
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger: logging.Logger = logging.getLogger(__name__)


# Export the temporal activity class
__all__ = [
    "TemporalPollerService",
]
