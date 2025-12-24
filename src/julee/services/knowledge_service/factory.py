"""
Factory function for creating KnowledgeService implementations.

This module provides the factory function for creating configured
KnowledgeService instances based on the service API configuration.
"""

import logging
from typing import Any

from julee.contrib.ceap.entities.document import Document
from julee.contrib.ceap.entities.knowledge_service_config import (
    KnowledgeServiceConfig,
    ServiceApi,
)
from julee.services.knowledge_service import (
    FileRegistrationResult,
    QueryResult,
)

from .anthropic import AnthropicKnowledgeService
from .knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class ConfigurableKnowledgeService(KnowledgeService):
    """
    KnowledgeService implementation that uses the factory pattern.

    This class implements the KnowledgeService protocol by delegating to
    a factory-created service instance. It can be wrapped by temporal
    decorators while maintaining proper protocol compliance.

    No constructor configuration is required - the factory is called
    within each method using the provided config parameter.
    """

    async def register_file(
        self, config: KnowledgeServiceConfig, document: Document
    ) -> FileRegistrationResult:
        """Register a document with the knowledge service."""
        service = knowledge_service_factory(config)
        return await service.register_file(config, document)

    async def execute_query(
        self,
        config: KnowledgeServiceConfig,
        query_text: str,
        service_file_ids: list[str] | None = None,
        query_metadata: dict[str, Any] | None = None,
        assistant_prompt: str | None = None,
    ) -> QueryResult:
        """Execute a query against the knowledge service."""
        service = knowledge_service_factory(config)
        return await service.execute_query(
            config=config,
            query_text=query_text,
            service_file_ids=service_file_ids,
            query_metadata=query_metadata,
            assistant_prompt=assistant_prompt,
        )


def knowledge_service_factory(
    knowledge_service_config: "KnowledgeServiceConfig",
) -> KnowledgeService:
    """Create a configured KnowledgeService instance.

    This factory function takes a KnowledgeServiceConfig domain object
    (containing metadata and service_api information) and returns a properly
    configured KnowledgeService implementation that can handle external
    operations.

    Args:
        knowledge_service_config: KnowledgeServiceConfig domain object with
                                 configuration and API information

    Returns:
        Configured KnowledgeService implementation ready for external
        operations

    Raises:
        ValueError: If the service_api is not supported

    Example:
        >>> from julee.domain import KnowledgeServiceConfig
        >>> from julee.contrib.ceap.entities.knowledge_service_config import (
        ...     ServiceApi
        ... )
        >>> config = KnowledgeServiceConfig(
        ...     knowledge_service_id="ks-123",
        ...     name="My Anthropic Service",
        ...     description="Anthropic-powered document analysis",
        ...     service_api=ServiceApi.ANTHROPIC
        ... )
        >>> service = knowledge_service_factory(config)
        >>> result = await service.register_file(document)
    """
    logger.debug(
        "Creating KnowledgeService via factory",
        extra={
            "knowledge_service_id": (knowledge_service_config.knowledge_service_id),
            "service_api": knowledge_service_config.service_api.value,
        },
    )

    # Route to appropriate implementation based on service_api
    service: KnowledgeService
    if knowledge_service_config.service_api == ServiceApi.ANTHROPIC:
        service = AnthropicKnowledgeService()
    else:
        raise ValueError(
            f"Unsupported service API: {knowledge_service_config.service_api}"
        )

    # Validate that the service satisfies the protocol
    from . import ensure_knowledge_service

    validated_service = ensure_knowledge_service(service)

    logger.info(
        "KnowledgeService created successfully",
        extra={
            "knowledge_service_id": (knowledge_service_config.knowledge_service_id),
            "service_api": knowledge_service_config.service_api.value,
            "implementation": type(validated_service).__name__,
        },
    )

    return validated_service


# Export both the factory function and the configurable class
__all__ = [
    "knowledge_service_factory",
    "ConfigurableKnowledgeService",
]
