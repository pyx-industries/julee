"""
Memory implementation of AssemblySpecificationRepository.

This module provides an in-memory implementation of the
AssemblySpecificationRepository protocol that follows the Clean Architecture
patterns defined in the Fun-Police Framework. It handles assembly
specification storage with JSON schemas and knowledge service query
configurations in memory dictionaries, ensuring idempotency and proper
error handling.

The implementation uses Python dictionaries to store specification data,
making it ideal for testing scenarios where external dependencies should be
avoided. All operations are still async to maintain interface compatibility.
"""

import logging
from typing import Any

from julee.contrib.ceap.entities.assembly_specification import (
    AssemblySpecification,
)
from julee.contrib.ceap.repositories.assembly_specification import (
    AssemblySpecificationRepository,
)
from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)


class MemoryAssemblySpecificationRepository(
    AssemblySpecificationRepository,
    MemoryRepositoryMixin[AssemblySpecification],
):
    """
    Memory implementation of AssemblySpecificationRepository using Python
    dictionaries.

    This implementation stores assembly specifications in memory:

    - Specifications: Dictionary keyed by assembly_specification_id containing
      AssemblySpecification objects

    This provides a lightweight, dependency-free option for testing while
    maintaining the same interface as other implementations.
    """

    def __init__(self) -> None:
        """Initialize repository with empty in-memory storage."""
        self.logger = logger
        self.entity_name = "AssemblySpecification"
        self.id_field = "assembly_specification_id"
        self.storage: dict[str, AssemblySpecification] = {}

        logger.debug("Initializing MemoryAssemblySpecificationRepository")

    async def get(self, assembly_specification_id: str) -> AssemblySpecification | None:
        """Retrieve an assembly specification by ID.

        Args:
            assembly_specification_id: Unique specification identifier

        Returns:
            AssemblySpecification if found, None otherwise
        """
        return self._get_entity(assembly_specification_id)

    async def save(self, assembly_specification: AssemblySpecification) -> None:
        """Save an assembly specification.

        Args:
            assembly_specification: Complete AssemblySpecification to save
        """
        self._save_entity(assembly_specification)

    async def generate_id(self) -> str:
        """Generate a unique assembly specification identifier.

        Returns:
            Unique assembly specification ID string
        """
        return self._generate_id("spec")

    async def get_many(
        self, assembly_specification_ids: list[str]
    ) -> dict[str, AssemblySpecification | None]:
        """Retrieve multiple assembly specifications by ID.

        Args:
            assembly_specification_ids: List of unique specification
            identifiers

        Returns:
            Dict mapping specification_id to AssemblySpecification (or None if
            not found)
        """
        return self._get_many_entities(assembly_specification_ids)

    async def list_all(self) -> list[AssemblySpecification]:
        """List all assembly specifications.

        Returns:
            List of all AssemblySpecification entities in the repository
        """
        self.logger.debug(
            f"Memory{self.entity_name}Repository: Listing all "
            f"{self.entity_name.lower()}s"
        )

        specifications = list(self.storage.values())

        self.logger.info(
            f"Memory{self.entity_name}Repository: Listed all "
            f"{self.entity_name.lower()}s",
            extra={"count": len(specifications)},
        )

        return specifications

    def _add_log_extras(
        self, entity: AssemblySpecification, log_data: dict[str, Any]
    ) -> None:
        """Add assembly specification-specific data to log entries."""
        super()._add_log_extras(entity, log_data)
        log_data["spec_name"] = entity.name
        log_data["version"] = entity.version
