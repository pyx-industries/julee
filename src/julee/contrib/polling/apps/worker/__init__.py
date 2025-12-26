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
