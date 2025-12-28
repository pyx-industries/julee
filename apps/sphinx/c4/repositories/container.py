"""SphinxEnv implementation of ContainerRepository."""

from julee.c4.entities.container import Container
from julee.c4.repositories.container import ContainerRepository

from .base import SphinxEnvC4RepositoryMixin


class SphinxEnvContainerRepository(
    SphinxEnvC4RepositoryMixin[Container], ContainerRepository
):
    """SphinxEnv implementation of ContainerRepository."""

    entity_class = Container

    async def get_by_system(self, system_slug: str) -> list[Container]:
        """Get all containers in a system."""
        return await self.find_by_field("system_slug", system_slug)

    async def get_by_technology(self, technology: str) -> list[Container]:
        """Get containers using a specific technology."""
        tech_lower = technology.lower()
        all_containers = await self.list_all()
        return [c for c in all_containers if c.technology.lower() == tech_lower]

    async def get_by_tag(self, tag: str) -> list[Container]:
        """Get containers with a specific tag."""
        tag_lower = tag.lower()
        all_containers = await self.list_all()
        return [
            c for c in all_containers
            if any(t.lower() == tag_lower for t in c.tags)
        ]
