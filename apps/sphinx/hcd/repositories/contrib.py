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

    async def get_by_docname(self, docname: str) -> list[ContribModule]:
        """Get all contrib modules defined in a specific document."""
        return await self.find_by_docname(docname)
