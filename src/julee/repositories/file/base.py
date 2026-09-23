"""Support for repositories that keep their entities in files.

A repository backed by files holds its entities in memory and writes each
one to a path the subclass chooses, so the files are the record and the
dictionary is the index. Documentation kits use this to treat a directory
of Gherkin features or RST documents as a database, with the files
remaining readable and diffable.

It is the file counterpart of MemoryRepositoryMixin, and like it, the
kernel owns it because every kit that stores anything needs the same
behaviour.

A subclass says where an entity goes, how it is written, and how existing
files are read back:

    class FileStoryRepository(FileRepositoryMixin[Story]):
        def _get_file_path(self, entity): ...
        def _serialize(self, entity): ...
        def _load_all(self): ...
"""

import logging
from abc import abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class FileRepositoryMixin(Generic[T]):
    """Mixin providing file-backed repository patterns.

    Extends the memory repository pattern with file persistence.
    Subclasses must implement:
    - _get_file_path(entity) -> Path
    - _serialize(entity) -> str
    - _load_all() -> None

    Classes using this mixin must provide:
    - self.storage: dict[str, T] for entity storage
    - self.base_path: Path for file storage root
    - self.entity_name: str for logging
    - self.id_field: str naming the entity's ID field
    """

    storage: dict[str, T]
    base_path: Path
    entity_name: str
    id_field: str

    def _get_entity_id(self, entity: T) -> str:
        """Read the entity's id, from whichever field names it.

        Args:
            entity: Entity to read

        Returns:
            The value of the field named by id_field

        Raises:
            TypeError: If that field does not hold a string
        """
        entity_id = getattr(entity, self.id_field)
        if not isinstance(entity_id, str):
            raise TypeError(
                f"{type(entity).__name__}.{self.id_field} is "
                f"{type(entity_id).__name__}, and an id must be a str"
            )
        return entity_id

    @abstractmethod
    def _get_file_path(self, entity: T) -> Path:
        """Get the file path for an entity.

        Args:
            entity: Entity to get path for

        Returns:
            Absolute path where entity should be stored
        """
        ...

    @abstractmethod
    def _serialize(self, entity: T) -> str:
        """Serialize entity to file content.

        Args:
            entity: Entity to serialize

        Returns:
            File content as string
        """
        ...

    @abstractmethod
    def _load_all(self) -> None:
        """Load all entities from disk into memory.

        Called during initialization to populate storage from existing files.
        """
        ...

    async def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID."""
        entity = self.storage.get(entity_id)
        if entity is None:
            logger.debug(
                f"File{self.entity_name}Repository: {self.entity_name} not found",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
        return entity

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID."""
        result: dict[str, T | None] = {}
        for entity_id in entity_ids:
            result[entity_id] = self.storage.get(entity_id)
        return result

    async def save(self, entity: T) -> None:
        """Save an entity to file and memory."""
        entity_id = self._get_entity_id(entity)
        file_path = self._get_file_path(entity)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        content = self._serialize(entity)
        file_path.write_text(content, encoding="utf-8")

        # Update memory storage
        self.storage[entity_id] = entity

        logger.debug(
            f"File{self.entity_name}Repository: Saved {self.entity_name} to {file_path}",
            extra={f"{self.entity_name.lower()}_id": entity_id},
        )

    async def list_all(self) -> list[T]:
        """List all entities."""
        return list(self.storage.values())

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity from file and memory."""
        entity = self.storage.get(entity_id)
        if entity is None:
            return False

        file_path = self._get_file_path(entity)

        # Delete file if it exists
        if file_path.exists():
            file_path.unlink()
            logger.debug(
                f"File{self.entity_name}Repository: Deleted file {file_path}",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )

        # Remove from memory
        del self.storage[entity_id]

        logger.debug(
            f"File{self.entity_name}Repository: Deleted {self.entity_name}",
            extra={f"{self.entity_name.lower()}_id": entity_id},
        )
        return True

    async def clear(self) -> None:
        """Remove all entities from storage and disk."""
        for entity_id in list(self.storage.keys()):
            await self.delete(entity_id)
        logger.debug(f"File{self.entity_name}Repository: Cleared all entities")
