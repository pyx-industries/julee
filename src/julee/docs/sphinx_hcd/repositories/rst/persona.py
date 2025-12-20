"""RST file-backed implementation of PersonaRepository."""

import logging
from pathlib import Path

from ...domain.models.persona import Persona
from ...domain.repositories.persona import PersonaRepository
from ...parsers.docutils_parser import ParsedDocument, parse_multiline_list
from ...utils import normalize_name
from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstPersonaRepository(RstRepositoryMixin[Persona], PersonaRepository):
    """RST file-backed implementation of PersonaRepository.

    Personas are stored as individual RST files in a directory.
    Each file contains a single define-persona directive.
    """

    entity_name = "Persona"
    id_field = "slug"
    entity_type = "persona"
    directive_name = "define-persona"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing persona RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> Persona:
        """Build Persona entity from parsed data."""
        options = data.get("options", {})
        content = data.get("content", "")

        # Name from option or derive from slug
        name = options.get("name", "")
        if not name:
            name = data["slug"].replace("-", " ").title()

        return Persona(
            slug=data["slug"],
            name=name,
            goals=parse_multiline_list(options.get("goals", "")),
            frustrations=parse_multiline_list(options.get("frustrations", "")),
            jobs_to_be_done=parse_multiline_list(options.get("jobs-to-be-done", "")),
            context=content.strip(),
            docname=docname,
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    # Query methods from PersonaRepository protocol

    async def get_by_name(self, name: str) -> Persona | None:
        """Get persona by display name."""
        name_normalized = normalize_name(name)
        for persona in self.storage.values():
            if persona.normalized_name == name_normalized:
                return persona
        return None

    async def get_by_normalized_name(self, normalized_name: str) -> Persona | None:
        """Get persona by normalized name."""
        for persona in self.storage.values():
            if persona.normalized_name == normalized_name:
                return persona
        return None

    async def get_by_docname(self, docname: str) -> list[Persona]:
        """Get all personas defined in a specific document."""
        return [
            persona for persona in self.storage.values()
            if persona.docname == docname
        ]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all personas defined in a specific document."""
        to_remove = [
            slug for slug, persona in self.storage.items()
            if persona.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)
