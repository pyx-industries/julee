"""RST file-backed implementation of IntegrationRepository."""

import logging
from pathlib import Path

from julee.hcd.utils import normalize_name

from ...domain.models.integration import Direction, Integration
from ...domain.repositories.integration import IntegrationRepository
from ...parsers.docutils_parser import ParsedDocument
from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstIntegrationRepository(RstRepositoryMixin[Integration], IntegrationRepository):
    """RST file-backed implementation of IntegrationRepository.

    Integrations are stored as individual RST files in a directory.
    Each file contains a single define-integration directive.
    """

    entity_name = "Integration"
    id_field = "slug"
    entity_type = "integration"
    directive_name = "define-integration"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing integration RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> Integration:
        """Build Integration entity from parsed data."""
        options = data.get("options", {})
        content = data.get("content", "")

        # Name from option or derive from slug
        name = options.get("name", "")
        if not name:
            name = data["slug"].replace("-", " ").title()

        # Module from slug (convert to Python module name)
        module = data["slug"].replace("-", "_")

        # Parse direction
        direction = Direction.from_string(options.get("direction", "bidirectional"))

        return Integration(
            slug=data["slug"],
            module=module,
            name=name,
            description=content.strip(),
            direction=direction,
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    # Query methods from IntegrationRepository protocol

    async def get_by_direction(self, direction: Direction) -> list[Integration]:
        """Get all integrations with a specific data flow direction."""
        return [
            integration
            for integration in self.storage.values()
            if integration.direction == direction
        ]

    async def get_by_module(self, module: str) -> Integration | None:
        """Get an integration by its module name."""
        for integration in self.storage.values():
            if integration.module == module:
                return integration
        return None

    async def get_by_name(self, name: str) -> Integration | None:
        """Get an integration by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        for integration in self.storage.values():
            if integration.name_normalized == name_normalized:
                return integration
        return None

    async def get_all_directions(self) -> set[Direction]:
        """Get all unique directions that have integrations."""
        return {integration.direction for integration in self.storage.values()}

    async def get_with_dependencies(self) -> list[Integration]:
        """Get all integrations that have external dependencies."""
        return [
            integration
            for integration in self.storage.values()
            if integration.depends_on
        ]

    async def get_by_dependency(self, dep_name: str) -> list[Integration]:
        """Get all integrations that depend on a specific external system."""
        dep_normalized = normalize_name(dep_name)
        return [
            integration
            for integration in self.storage.values()
            if integration.has_dependency(dep_normalized)
        ]
