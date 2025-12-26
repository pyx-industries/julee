"""
Polling entities.

This module contains the core domain entities for the polling contrib module.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.entities.polling_config import PollingConfig, PollingProtocol, PollingResult
"""
