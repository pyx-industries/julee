"""
Memory implementation of AssemblyRepository.

This module provides an in-memory implementation of the AssemblyRepository
protocol that follows the Clean Architecture patterns defined in the
Fun-Police Framework. It handles assembly storage in memory dictionaries,
ensuring idempotency and proper error handling.

The implementation uses Python dictionaries to store assembly data, making it
ideal for testing scenarios where external dependencies should be avoided.
All operations are still async to maintain interface compatibility.
"""

import logging
from typing import Any

from julee.contrib.ceap.entities.assembly import Assembly
from julee.contrib.ceap.repositories.assembly import AssemblyRepository
from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)


class MemoryAssemblyRepository(AssemblyRepository, MemoryRepositoryMixin[Assembly]):
    """
    Memory implementation of AssemblyRepository using Python dictionaries.

    This implementation stores assembly data in memory using a dictionary
    keyed by assembly_id. This provides a lightweight, dependency-free
    option for testing.
    """

    def __init__(self) -> None:
        """Initialize repository with empty in-memory storage."""
        self.logger = logger
        self.entity_name = "Assembly"
        self.id_field = "assembly_id"
        self.storage: dict[str, Assembly] = {}

        logger.debug("Initializing MemoryAssemblyRepository")

    async def get(self, assembly_id: str) -> Assembly | None:
        """Retrieve an assembly by ID.

        Args:
            assembly_id: Unique assembly identifier

        Returns:
            Assembly if found, None otherwise
        """
        return self._get_entity(assembly_id)

    async def save(self, assembly: Assembly) -> None:
        """Save assembly metadata (status, updated_at, etc.).

        Args:
            assembly: Assembly entity
        """
        self._save_entity(assembly)

    async def generate_id(self) -> str:
        """Generate a unique assembly identifier.

        Returns:
            Unique assembly ID string
        """
        return self._generate_id("assembly")

    async def get_many(self, assembly_ids: list[str]) -> dict[str, Assembly | None]:
        """Retrieve multiple assemblies by ID.

        Args:
            assembly_ids: List of unique assembly identifiers

        Returns:
            Dict mapping assembly_id to Assembly (or None if not found)
        """
        return self._get_many_entities(assembly_ids)

    def _add_log_extras(self, entity: Assembly, log_data: dict[str, Any]) -> None:
        """Add assembly-specific data to log entries."""
        super()._add_log_extras(entity, log_data)
        log_data["assembled_document_id"] = entity.assembled_document_id
