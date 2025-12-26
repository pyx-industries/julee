"""
Worker applications for the CEAP contrib module.

This module contains worker-specific entry points for the CEAP contrib module,
including Temporal workflows (pipelines) that orchestrate document extraction,
assembly, and validation operations with durability guarantees.

The worker applications in this module can be registered with Temporal workers
to provide CEAP capabilities within workflow contexts.

Composition API:
    TASK_QUEUE: The Temporal task queue for standalone CEAP worker
    get_workflow_classes(): Returns workflow classes for registration
    get_activity_classes(): Returns activity classes for external composition

The standalone worker (main.py) is a complete reference implementation.
External composites should use get_workflow_classes() and get_activity_classes(),
then do their own DI wiring.
"""
