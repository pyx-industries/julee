"""RST repository base classes and mixins.

Provides common functionality for RST file-backed repository implementations.
RST files are treated as a database backend with lossless round-trip support.
"""

import logging
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from julee.hcd.parsers.docutils_parser import (
    ParsedDocument,
    find_entity_by_type,
    parse_rst_file,
)
from julee.hcd.templates import render_entity
from julee.shared.infrastructure.repositories.memory.base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


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
    """

    base_dir: Path
    entity_type: str
    directive_name: str

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing RST files
        """
        self.base_dir = base_dir
        self.storage: dict[str, T] = {}
        self._load_all_files()

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
        # Save to memory
        await super().save(entity)

        # Write to RST file
        self._write_file(entity)

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
        result = await super().delete(entity_id)

        if result:
            path = self._get_file_path(entity_id)
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted {self.entity_name} file {path}")

        return result

    async def clear(self) -> None:
        """Remove all entities and their RST files."""
        # Get all files before clearing storage
        files_to_delete = [
            self._get_file_path(entity_id) for entity_id in self.storage.keys()
        ]

        # Clear memory
        await super().clear()

        # Delete files
        for path in files_to_delete:
            if path.exists():
                path.unlink()

        logger.debug(f"Cleared {len(files_to_delete)} {self.entity_name} files")
