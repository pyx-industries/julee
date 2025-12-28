"""SphinxEnv implementation of SoftwareSystemRepository."""

from julee.c4.entities.software_system import SoftwareSystem, SystemType
from julee.c4.repositories.software_system import SoftwareSystemRepository

from .base import SphinxEnvC4RepositoryMixin


class SphinxEnvSoftwareSystemRepository(
    SphinxEnvC4RepositoryMixin[SoftwareSystem], SoftwareSystemRepository
):
    """SphinxEnv implementation of SoftwareSystemRepository."""

    entity_class = SoftwareSystem

    async def get_by_type(self, system_type: SystemType) -> list[SoftwareSystem]:
        """Get all systems of a specific type."""
        all_systems = await self.list_all()
        return [s for s in all_systems if s.system_type == system_type]

    async def get_internal_systems(self) -> list[SoftwareSystem]:
        """Get all internal (owned) systems."""
        return await self.get_by_type(SystemType.INTERNAL)

    async def get_external_systems(self) -> list[SoftwareSystem]:
        """Get all external systems."""
        return await self.get_by_type(SystemType.EXTERNAL)

    async def get_by_tag(self, tag: str) -> list[SoftwareSystem]:
        """Get systems with a specific tag."""
        tag_lower = tag.lower()
        all_systems = await self.list_all()
        return [
            s for s in all_systems
            if any(t.lower() == tag_lower for t in s.tags)
        ]

    async def get_by_owner(self, owner: str) -> list[SoftwareSystem]:
        """Get systems owned by a specific team."""
        owner_lower = owner.lower()
        all_systems = await self.list_all()
        return [s for s in all_systems if s.owner.lower() == owner_lower]
