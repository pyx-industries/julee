"""Memory implementation of CodeInfoRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.code_info import BoundedContextInfo
from julee.hcd.repositories.code_info import CodeInfoRepository

logger = logging.getLogger(__name__)


class MemoryCodeInfoRepository(
    MemoryRepositoryMixin[BoundedContextInfo], CodeInfoRepository
):
    """In-memory implementation of CodeInfoRepository.

    Bounded context info is stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where code info is populated at builder-inited
    by scanning src/ directories.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, BoundedContextInfo] = {}
        self.entity_name = "BoundedContextInfo"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> BoundedContextInfo | None:
        """Get bounded context info by slug."""
        return self._get_entity(entity_id)

    async def get_many(
        self, entity_ids: list[str]
    ) -> dict[str, BoundedContextInfo | None]:
        """Get multiple bounded context infos by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: BoundedContextInfo) -> None:
        """Save bounded context info."""
        self._save_entity(entity)

    async def list_all(self) -> list[BoundedContextInfo]:
        """List all bounded context infos."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete bounded context info by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all bounded context infos."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # CodeInfoRepository-specific queries
    # -------------------------------------------------------------------------

    async def get_by_code_dir(self, code_dir: str) -> BoundedContextInfo | None:
        """Get bounded context info by its code directory name."""
        for info in self.storage.values():
            if info.code_dir == code_dir:
                return info
        return None

    async def get_with_entities(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have domain entities."""
        return [info for info in self.storage.values() if info.has_entities]

    async def get_with_use_cases(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have use cases."""
        return [info for info in self.storage.values() if info.has_use_cases]

    async def get_with_infrastructure(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have infrastructure."""
        return [info for info in self.storage.values() if info.has_infrastructure]

    async def get_all_entity_names(self) -> set[str]:
        """Get all unique entity class names across all bounded contexts."""
        names: set[str] = set()
        for info in self.storage.values():
            names.update(info.get_entity_names())
        return names

    async def get_all_use_case_names(self) -> set[str]:
        """Get all unique use case class names across all bounded contexts."""
        names: set[str] = set()
        for info in self.storage.values():
            names.update(info.get_use_case_names())
        return names
