"""RST repository base classes and mixins.

Provides common functionality for RST file-backed repository implementations.
RST files are treated as a database backend with lossless round-trip support.
"""

import logging
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.parsers.docutils_parser import (
    ParsedDocument,
    find_entity_by_type,
    parse_rst_file,
)
from julee.hcd.templates import render_entity

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class EntityHandler(Protocol[T]):
    """Protocol for entity lifecycle handlers."""

    async def handle(self, entity: T) -> None:
        """Handle an entity lifecycle event."""
        ...


class RstRepositoryMixin(MemoryRepositoryMixin[T], Generic[T]):
    """Mixin for RST file-backed repositories.

    Extends MemoryRepositoryMixin to add RST file persistence.
    On initialization, loads all RST files from the directory.
    On save, writes the entity to an RST file.
    On delete, removes the RST file.

    Classes using this mixin must provide:
    - self.base_dir: Path to the directory containing RST files
    - self.entity_type: str for template selection (e.g., 'journey')
    - self.directive_name: str for parsing (e.g., 'define-journey')
    - self._build_entity(): method to build entity from parsed data

    Optional handler support:
    - post_save_handler: Called after entity is saved to file
    - post_delete_handler: Called after entity is deleted
    """

    base_dir: Path
    entity_type: str
    directive_name: str
    post_save_handler: EntityHandler[T] | None = None
    post_delete_handler: EntityHandler[T] | None = None

    def __init__(
        self,
        base_dir: Path,
        post_save_handler: EntityHandler[T] | None = None,
        post_delete_handler: EntityHandler[T] | None = None,
    ) -> None:
        """Initialize with base directory and optional handlers.

        Args:
            base_dir: Directory containing RST files
            post_save_handler: Handler called after entity is saved
            post_delete_handler: Handler called after entity is deleted
        """
        self.base_dir = base_dir
        self.storage: dict[str, T] = {}
        self.post_save_handler = post_save_handler
        self.post_delete_handler = post_delete_handler
        self._load_all_files()

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> T | None:
        """Get an entity by ID."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Get multiple entities by ID."""
        return self._get_many_entities(entity_ids)

    async def list_all(self) -> list[T]:
        """List all entities."""
        return self._list_all_entities()

    # -------------------------------------------------------------------------
    # File loading
    # -------------------------------------------------------------------------

    def _load_all_files(self) -> None:
        """Load all RST files from the directory."""
        if not self.base_dir.exists():
            logger.debug(f"RST directory not found: {self.base_dir}")
            return

        count = 0
        for rst_file in self.base_dir.glob("*.rst"):
            # Skip index files
            if rst_file.name == "index.rst":
                continue

            entity = self._parse_file(rst_file)
            if entity:
                entity_id = self._get_entity_id(entity)
                self.storage[entity_id] = entity
                count += 1

        logger.debug(f"Loaded {count} {self.entity_name} entities from {self.base_dir}")

    def _parse_file(self, path: Path) -> T | None:
        """Parse an RST file into an entity.

        Args:
            path: Path to RST file

        Returns:
            Entity or None if parsing fails
        """
        parsed = parse_rst_file(path)

        # Find the entity with matching directive
        entity_data = find_entity_by_type(parsed, self.directive_name)
        if not entity_data:
            logger.debug(f"No {self.directive_name} directive found in {path}")
            return None

        return self._build_entity(
            entity_data,
            parsed=parsed,
            docname=path.stem,
        )

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> T:
        """Build entity from parsed data.

        Args:
            data: Entity data from parsed directive
            parsed: Full ParsedDocument for structure extraction
            docname: Document name (file stem)

        Returns:
            Domain entity

        Note:
            Subclasses must override this method.
        """
        raise NotImplementedError("Subclasses must implement _build_entity")

    def _get_file_path(self, entity_id: str) -> Path:
        """Get the RST file path for an entity.

        Args:
            entity_id: Entity identifier (slug)

        Returns:
            Path to the RST file
        """
        return self.base_dir / f"{entity_id}.rst"

    async def save(self, entity: T) -> None:
        """Save entity to memory and RST file.

        Args:
            entity: Entity to save
        """
        # Save to memory (using protected helper)
        self._save_entity(entity)

        # Write to RST file
        self._write_file(entity)

        # Call post-save handler if configured
        if self.post_save_handler:
            await self.post_save_handler.handle(entity)

    def _write_file(self, entity: T) -> None:
        """Write entity to RST file.

        Args:
            entity: Entity to write
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        entity_id = self._get_entity_id(entity)
        path = self._get_file_path(entity_id)
        content = render_entity(self.entity_type, entity)
        path.write_text(content, encoding="utf-8")
        logger.debug(f"Wrote {self.entity_name} to {path}")

    async def delete(self, entity_id: str) -> bool:
        """Delete entity from memory and remove RST file.

        Args:
            entity_id: Entity identifier

        Returns:
            True if deleted, False if not found
        """
        # Get entity before deletion for handler
        entity = self.storage.get(entity_id)

        # Delete from memory (using protected helper)
        result = self._delete_entity(entity_id)

        if result:
            path = self._get_file_path(entity_id)
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted {self.entity_name} file {path}")

            # Call post-delete handler if configured
            if self.post_delete_handler and entity:
                await self.post_delete_handler.handle(entity)

        return result

    async def clear(self) -> None:
        """Remove all entities and their RST files."""
        # Get all files before clearing storage
        files_to_delete = [
            self._get_file_path(entity_id) for entity_id in self.storage.keys()
        ]

        # Clear memory (using protected helper)
        self._clear_storage()

        # Delete files
        for path in files_to_delete:
            if path.exists():
                path.unlink()

        logger.debug(f"Cleared {len(files_to_delete)} {self.entity_name} files")
