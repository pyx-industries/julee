"""CodeInfoRepository protocol.

Defines the interface for bounded context code introspection data access.
"""

from typing import Protocol, runtime_checkable

from ..models.code_info import BoundedContextInfo
from .base import BaseRepository


@runtime_checkable
class CodeInfoRepository(BaseRepository[BoundedContextInfo], Protocol):
    """Repository protocol for BoundedContextInfo entities.

    Extends BaseRepository with code introspection-specific query methods.
    Code info is populated once at builder-inited by scanning src/ directories.
    """

    async def get_by_code_dir(self, code_dir: str) -> BoundedContextInfo | None:
        """Get bounded context info by its code directory name.

        Args:
            code_dir: Directory name in src/ (may differ from slug)

        Returns:
            BoundedContextInfo if found, None otherwise
        """
        ...

    async def get_with_entities(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have domain entities.

        Returns:
            List of bounded contexts with at least one entity
        """
        ...

    async def get_with_use_cases(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have use cases.

        Returns:
            List of bounded contexts with at least one use case
        """
        ...

    async def get_with_infrastructure(self) -> list[BoundedContextInfo]:
        """Get all bounded contexts that have infrastructure.

        Returns:
            List of bounded contexts where has_infrastructure is True
        """
        ...

    async def get_all_entity_names(self) -> set[str]:
        """Get all unique entity class names across all bounded contexts.

        Returns:
            Set of entity class names
        """
        ...

    async def get_all_use_case_names(self) -> set[str]:
        """Get all unique use case class names across all bounded contexts.

        Returns:
            Set of use case class names
        """
        ...
