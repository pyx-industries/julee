"""Sphinx environment implementation of EpicRepository."""

from typing import TYPE_CHECKING

from julee.hcd.domain.models.epic import Epic
from julee.hcd.domain.repositories.epic import EpicRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvEpicRepository(SphinxEnvRepositoryMixin[Epic], EpicRepository):
    """Sphinx env-backed implementation of EpicRepository.

    Stores epics in env.hcd_storage["epics"] for parallel-safe Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "Epic"
        self.entity_key = "epics"
        self.id_field = "slug"
        self.entity_class = Epic

    async def get_by_docname(self, docname: str) -> list[Epic]:
        """Get all epics defined in a specific document."""
        return await self.find_by_docname(docname)

    async def get_with_story_ref(self, story_title: str) -> list[Epic]:
        """Get epics that contain a specific story."""
        story_normalized = normalize_name(story_title)
        storage = self._get_storage()
        result = []
        for data in storage.values():
            story_refs = data.get("story_refs", [])
            if any(normalize_name(ref) == story_normalized for ref in story_refs):
                result.append(self._deserialize(data))
        return result

    async def get_all_story_refs(self) -> set[str]:
        """Get all unique story references across all epics."""
        storage = self._get_storage()
        refs: set[str] = set()
        for data in storage.values():
            story_refs = data.get("story_refs", [])
            refs.update(normalize_name(ref) for ref in story_refs)
        return refs
