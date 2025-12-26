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

from .pipelines import (
    ExtractAssembleWorkflow,
    ValidateDocumentWorkflow,
)

# Task queue for standalone CEAP worker
TASK_QUEUE = "julee-contrib-ceap-queue"


def get_workflow_classes() -> list[type]:
    """Return CEAP workflow classes for registration.

    Returns:
        List of workflow classes to register with a Temporal worker.
    """
    return [
        ExtractAssembleWorkflow,
        ValidateDocumentWorkflow,
    ]


def get_activity_classes() -> list[type]:
    """Return CEAP activity classes for external composition.

    External composites (like apps/worker) should use these classes
    and do their own DI wiring. For the standalone CEAP worker,
    see main.py which handles its own instantiation.

    Returns:
        List of activity classes that can be instantiated with dependencies.
    """
    from julee.contrib.ceap.infrastructure.temporal.repositories.activities import (
        TemporalMinioAssemblyRepository,
        TemporalMinioAssemblySpecificationRepository,
        TemporalMinioDocumentPolicyValidationRepository,
        TemporalMinioDocumentRepository,
        TemporalMinioKnowledgeServiceConfigRepository,
        TemporalMinioKnowledgeServiceQueryRepository,
        TemporalMinioPolicyRepository,
    )
    from julee.contrib.ceap.infrastructure.temporal.services.activities import (
        TemporalKnowledgeService,
    )

    return [
        TemporalMinioAssemblyRepository,
        TemporalMinioAssemblySpecificationRepository,
        TemporalMinioDocumentRepository,
        TemporalMinioKnowledgeServiceConfigRepository,
        TemporalMinioKnowledgeServiceQueryRepository,
        TemporalMinioPolicyRepository,
        TemporalMinioDocumentPolicyValidationRepository,
        TemporalKnowledgeService,
    ]


__all__ = [
    "TASK_QUEUE",
    "get_workflow_classes",
    "get_activity_classes",
    "ExtractAssembleWorkflow",
    "ValidateDocumentWorkflow",
]
