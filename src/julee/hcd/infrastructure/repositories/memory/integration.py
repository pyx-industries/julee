"""Memory implementation of IntegrationRepository."""

import logging

from julee.hcd.entities.integration import Direction, Integration
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.utils import normalize_name
from julee.shared.infrastructure.repositories.memory.base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)


class MemoryIntegrationRepository(
    MemoryRepositoryMixin[Integration], IntegrationRepository
):
    """In-memory implementation of IntegrationRepository.

    Integrations are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where integrations are populated at builder-inited
    and queried during doctree processing.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, Integration] = {}
        self.entity_name = "Integration"
        self.id_field = "slug"

    async def get_by_direction(self, direction: Direction) -> list[Integration]:
        """Get all integrations with a specific direction."""
        return [
            integration
            for integration in self.storage.values()
            if integration.direction == direction
        ]

    async def get_by_module(self, module: str) -> Integration | None:
        """Get an integration by its module name."""
        for integration in self.storage.values():
            if integration.module == module:
                return integration
        return None

    async def get_by_name(self, name: str) -> Integration | None:
        """Get an integration by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        for integration in self.storage.values():
            if integration.name_normalized == name_normalized:
                return integration
        return None

    async def get_all_directions(self) -> set[Direction]:
        """Get all unique directions that have integrations."""
        return {integration.direction for integration in self.storage.values()}

    async def get_with_dependencies(self) -> list[Integration]:
        """Get all integrations that have external dependencies."""
        return [
            integration
            for integration in self.storage.values()
            if integration.depends_on
        ]

    async def get_by_dependency(self, dep_name: str) -> list[Integration]:
        """Get all integrations that depend on a specific external system."""
        return [
            integration
            for integration in self.storage.values()
            if integration.has_dependency(dep_name)
        ]
