"""Sphinx environment implementation of CodeInfoRepository."""

from typing import TYPE_CHECKING

from julee.hcd.entities.code_info import BoundedContextInfo
from julee.hcd.repositories.code_info import CodeInfoRepository

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvCodeInfoRepository(
    SphinxEnvRepositoryMixin[BoundedContextInfo], CodeInfoRepository
):
    """Sphinx env-backed implementation of CodeInfoRepository.

    Stores bounded context info in env.hcd_storage["code_info"] for
    parallel-safe Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "BoundedContextInfo"
        self.entity_key = "code_info"
        self.id_field = "slug"
        self.entity_class = BoundedContextInfo

    async def get_by_code_dir(self, code_dir: str) -> BoundedContextInfo | None:
        """Get bounded context info by its code directory name."""
        storage = self._get_storage()
        for data in storage.values():
            if data.get("code_dir") == code_dir:
                return self._deserialize(data)
        return None

    async def get_with_entities(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have domain entities."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("has_entities"):
                result.append(self._deserialize(data))
        return result

    async def get_with_use_cases(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have use cases."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("has_use_cases"):
                result.append(self._deserialize(data))
        return result

    async def get_with_infrastructure(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have infrastructure."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("has_infrastructure"):
                result.append(self._deserialize(data))
        return result

    async def get_all_entity_names(self) -> set[str]:
        """Get all unique entity class names across all bounded contexts."""
        storage = self._get_storage()
        names: set[str] = set()
        for data in storage.values():
            entity = self._deserialize(data)
            names.update(entity.get_entity_names())
        return names

    async def get_all_use_case_names(self) -> set[str]:
        """Get all unique use case class names across all bounded contexts."""
        storage = self._get_storage()
        names: set[str] = set()
        for data in storage.values():
            entity = self._deserialize(data)
            names.update(entity.get_use_case_names())
        return names
