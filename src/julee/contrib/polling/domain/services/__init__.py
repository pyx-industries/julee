"""
Polling domain services.

This module contains the service protocols for the polling contrib module.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.domain.services.poller import PollerService
"""

__all__ = []
