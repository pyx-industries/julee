"""Sphinx environment implementation of IntegrationRepository."""

from typing import TYPE_CHECKING

from julee.hcd.domain.models.integration import Direction, Integration
from julee.hcd.domain.repositories.integration import IntegrationRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvIntegrationRepository(
    SphinxEnvRepositoryMixin[Integration], IntegrationRepository
):
    """Sphinx env-backed implementation of IntegrationRepository.

    Stores integrations in env.hcd_storage["integrations"] for parallel-safe
    Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "Integration"
        self.entity_key = "integrations"
        self.id_field = "slug"
        self.entity_class = Integration

    async def get_by_direction(self, direction: Direction) -> list[Integration]:
        """Get all integrations with a specific direction."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            # Direction is serialized as its value string
            if data.get("direction") == direction.value:
                result.append(self._deserialize(data))
        return result

    async def get_by_module(self, module: str) -> Integration | None:
        """Get an integration by its module name."""
        storage = self._get_storage()
        for data in storage.values():
            if data.get("module") == module:
                return self._deserialize(data)
        return None

    async def get_by_name(self, name: str) -> Integration | None:
        """Get an integration by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        storage = self._get_storage()
        for data in storage.values():
            if data.get("name_normalized") == name_normalized:
                return self._deserialize(data)
        return None

    async def get_all_directions(self) -> set[Direction]:
        """Get all unique directions that have integrations."""
        storage = self._get_storage()
        directions = set()
        for data in storage.values():
            direction_str = data.get("direction")
            if direction_str:
                directions.add(Direction(direction_str))
        return directions

    async def get_with_dependencies(self) -> list[Integration]:
        """Get all integrations that have external dependencies."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("depends_on"):
                result.append(self._deserialize(data))
        return result

    async def get_by_dependency(self, dep_name: str) -> list[Integration]:
        """Get all integrations that depend on a specific external system."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            entity = self._deserialize(data)
            if entity.has_dependency(dep_name):
                result.append(entity)
        return result
