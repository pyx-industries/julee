"""
Infrastructure services for the polling contrib module.

This module contains the concrete implementations of domain services
for the polling contrib module.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.infrastructure.services.polling.http import HttpPollerService
"""
