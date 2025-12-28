"""
Knowledge service implementations for CEAP.

This module provides the factory function and implementations for
creating configured knowledge service instances.
"""

import logging

logger = logging.getLogger(__name__)


def ensure_knowledge_service(service: object):
    """Ensure an object satisfies the KnowledgeService protocol.

    Args:
        service: The service implementation to validate

    Returns:
        The validated service (type checker knows it satisfies
        KnowledgeService)

    Raises:
        TypeError: If the service doesn't satisfy the protocol
    """
    from julee.contrib.ceap.services.knowledge_service import KnowledgeService

    if not isinstance(service, KnowledgeService):
        raise TypeError(
            f"Service {type(service).__name__} does not satisfy "
            f"KnowledgeService protocol"
        )

    return service


__all__ = [
    "ensure_knowledge_service",
]
