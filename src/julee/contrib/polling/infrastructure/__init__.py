"""
Infrastructure layer for the polling contrib module.

This module contains the concrete implementations of domain protocols
and external system integrations for the polling contrib module.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.infrastructure.services.polling.http import HttpPollerService
- from julee.contrib.polling.infrastructure.temporal.manager import PollingManager
- from julee.contrib.polling.infrastructure.temporal.proxies import WorkflowPollerServiceProxy
- from julee.contrib.polling.infrastructure.temporal.activities import TemporalPollerService
"""
