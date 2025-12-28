"""Sphinx environment implementation of ContribRepository."""

from julee.hcd.entities.contrib import ContribModule
from julee.hcd.repositories.contrib import ContribRepository

from .base import SphinxEnvRepositoryMixin


class SphinxEnvContribRepository(
    SphinxEnvRepositoryMixin[ContribModule], ContribRepository
):
    """Sphinx env-backed implementation of ContribRepository.

    Stores contrib modules in env.hcd_storage["contribs"] for parallel-safe
    Sphinx builds.
    """

    entity_class = ContribModule
    entity_key = "contribs"  # Override: not "contribmodules"

    async def list_filtered(
        self, solution_slug: str | None = None
    ) -> list[ContribModule]:
        """List contrib modules with optional solution filter."""
        all_entities = await self.list_all()
        if solution_slug is None:
            return all_entities
        return [e for e in all_entities if e.solution_slug == solution_slug]

    async def list_slugs(self, solution_slug: str | None = None) -> list[str]:
        """List all contrib module slugs with optional solution filter."""
        entities = await self.list_filtered(solution_slug)
        return [e.slug for e in entities]

    async def get_by_docname(self, docname: str) -> list[ContribModule]:
        """Get all contrib modules defined in a specific document."""
        return await self.find_by_docname(docname)
