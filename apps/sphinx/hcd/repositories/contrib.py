"""Sphinx environment implementation of ContribRepository."""

from typing import TYPE_CHECKING

from julee.hcd.entities.contrib import ContribModule
from julee.hcd.domain.repositories.contrib import ContribRepository

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvContribRepository(
    SphinxEnvRepositoryMixin[ContribModule], ContribRepository
):
    """Sphinx env-backed implementation of ContribRepository.

    Stores contrib modules in env.hcd_storage["contribs"] for parallel-safe
    Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "ContribModule"
        self.entity_key = "contribs"
        self.id_field = "slug"
        self.entity_class = ContribModule

    async def get_by_docname(self, docname: str) -> list[ContribModule]:
        """Get all contrib modules defined in a specific document."""
        return await self.find_by_docname(docname)
