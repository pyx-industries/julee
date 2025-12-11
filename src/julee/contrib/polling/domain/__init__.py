"""
Domain layer for the polling contrib module.

This module contains the core domain models, services, and business rules
for the polling contrib module. It defines the fundamental concepts and
protocols that govern polling operations.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.domain.models.polling_config import PollingConfig, PollingProtocol, PollingResult
- from julee.contrib.polling.domain.services.poller import PollerService
"""

__all__ = []
