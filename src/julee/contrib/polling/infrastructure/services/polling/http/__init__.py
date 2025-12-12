"""
HTTP polling implementation.

This module provides HTTP-specific polling functionality for the polling
contrib module.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.infrastructure.services.polling.http.http_poller_service import HttpPollerService
"""

__all__ = []
