"""Memory implementation of CodeInfoRepository."""

import logging

from julee.hcd.entities.code_info import BoundedContextInfo
from julee.hcd.repositories.code_info import CodeInfoRepository
from julee.shared.infrastructure.repositories.memory.base import MemoryRepositoryMixin

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
