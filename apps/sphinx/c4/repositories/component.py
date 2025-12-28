"""SphinxEnv implementation of ComponentRepository."""

from julee.c4.entities.component import Component
from julee.c4.repositories.component import ComponentRepository

from .base import SphinxEnvC4RepositoryMixin


class SphinxEnvComponentRepository(
    SphinxEnvC4RepositoryMixin[Component], ComponentRepository
):
    """SphinxEnv implementation of ComponentRepository."""

    entity_class = Component

    async def get_by_container(self, container_slug: str) -> list[Component]:
        """Get all components in a container."""
        return await self.find_by_field("container_slug", container_slug)

    async def get_by_technology(self, technology: str) -> list[Component]:
        """Get components using a specific technology."""
        tech_lower = technology.lower()
        all_components = await self.list_all()
        return [c for c in all_components if c.technology.lower() == tech_lower]

    async def get_by_tag(self, tag: str) -> list[Component]:
        """Get components with a specific tag."""
        tag_lower = tag.lower()
        all_components = await self.list_all()
        return [
            c for c in all_components
            if any(t.lower() == tag_lower for t in c.tags)
        ]
