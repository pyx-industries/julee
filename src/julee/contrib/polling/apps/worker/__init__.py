"""
Worker applications for the polling contrib module.

This module contains worker-specific entry points for the polling contrib module,
including Temporal workflows (pipelines) that orchestrate polling operations
with durability guarantees.

The worker applications in this module can be registered with Temporal workers
to provide polling capabilities within workflow contexts.

Composition API:
    TASK_QUEUE: The Temporal task queue for standalone polling worker
    get_workflow_classes(): Returns workflow classes for registration
    get_activity_classes(): Returns activity classes for external composition

The standalone worker (main.py) is a complete reference implementation.
External composites should use get_workflow_classes() and get_activity_classes(),
then do their own DI wiring.
"""

from .pipelines import NewDataDetectionPipeline

# Task queue for standalone polling worker
TASK_QUEUE = "julee-contrib-polling-queue"


def get_workflow_classes() -> list[type]:
    """Return polling workflow classes for registration.

    Returns:
        List of workflow classes to register with a Temporal worker.
    """
    return [
        NewDataDetectionPipeline,
    ]


def get_activity_classes() -> list[type]:
    """Return polling activity classes for external composition.

    External composites (like apps/worker) should use these classes
    and do their own DI wiring. For the standalone polling worker,
    see main.py which handles its own instantiation.

    Returns:
        List of activity classes that can be instantiated.
    """
    from julee.contrib.polling.infrastructure.temporal.activities import (
        TemporalPollerService,
    )

    return [
        TemporalPollerService,
    ]


__all__ = [
    "TASK_QUEUE",
    "get_workflow_classes",
    "get_activity_classes",
    "NewDataDetectionPipeline",
]
