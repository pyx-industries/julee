"""
Worker applications for the polling contrib module.

This module contains worker-specific entry points for the polling contrib module,
including Temporal workflows (pipelines) that orchestrate polling operations
with durability guarantees.

The worker applications in this module can be registered with Temporal workers
to provide polling capabilities within workflow contexts.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.apps.worker.pipelines import NewDataDetectionPipeline
"""

__all__ = []
