"""
Polling Contrib Module.

This module provides ready-made polling functionality for external endpoints.
It follows the Julee contrib module pattern, providing a complete polling
solution that can be imported and used by Julee solutions.

The polling module includes:
- Entities for polling configuration and results
- Service protocols for polling operations
- HTTP implementation for REST API polling
- Co-located tests and examples

Example usage:
    from julee.contrib.polling.entities.polling_config import PollingConfig, PollingProtocol
    from julee.contrib.polling.infrastructure.services.polling.http import HttpPollerService
    from julee.contrib.polling.services.poller import PollerService
    from julee.contrib.polling.entities.polling_config import PollingResult

    # Configure polling
    config = PollingConfig(
        endpoint_identifier="api-v1",
        polling_protocol=PollingProtocol.HTTP,
        connection_params={"url": "https://api.example.com/data"},
        timeout_seconds=30
    )

    # Poll the endpoint
    service = HttpPollerService()
    result = await service.poll_endpoint(config)

Note: All imports must be explicit to avoid import chains that can pull
non-deterministic code into Temporal workflows. Import directly from
the specific modules you need rather than using this convenience module.
"""

# No re-exports to avoid import chains that pull non-deterministic code
# into Temporal workflows. Import from specific submodules instead:
#
# Entities:
# - from julee.contrib.polling.entities.polling_config import PollingConfig, PollingProtocol, PollingResult
#
# Services (protocols):
# - from julee.contrib.polling.services.poller import PollerService
#
# Infrastructure:
# - from julee.contrib.polling.infrastructure.services.polling.http import HttpPollerService
# - from julee.contrib.polling.infrastructure.temporal.manager import PollingManager
# - from julee.contrib.polling.infrastructure.temporal.proxies import WorkflowPollerServiceProxy
# - from julee.contrib.polling.infrastructure.temporal.activities import TemporalPollerService

__all__ = []
