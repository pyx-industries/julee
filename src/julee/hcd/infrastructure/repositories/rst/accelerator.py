"""RST file-backed implementation of AcceleratorRepository."""

import logging
from pathlib import Path

from julee.hcd.entities.accelerator import Accelerator, IntegrationReference
from julee.hcd.parsers.docutils_parser import ParsedDocument, parse_comma_list
from julee.hcd.repositories.accelerator import AcceleratorRepository

from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstAcceleratorRepository(RstRepositoryMixin[Accelerator], AcceleratorRepository):
    """RST file-backed implementation of AcceleratorRepository.

    Accelerators are stored as individual RST files in a directory.
    Each file contains a single define-accelerator directive.
    """

    entity_name = "Accelerator"
    id_field = "slug"
    entity_type = "accelerator"
    directive_name = "define-accelerator"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing accelerator RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> Accelerator:
        """Build Accelerator entity from parsed data."""
        options = data.get("options", {})
        content = data.get("content", "")

        # Convert string lists to IntegrationReference
        sources_from = [
            IntegrationReference(slug=s)
            for s in parse_comma_list(options.get("sources-from", ""))
        ]
        publishes_to = [
            IntegrationReference(slug=s)
            for s in parse_comma_list(options.get("publishes-to", ""))
        ]

        return Accelerator(
            slug=data["slug"],
            status=options.get("status", ""),
            milestone=options.get("milestone") or None,
            acceptance=options.get("acceptance") or None,
            objective=content.strip(),
            sources_from=sources_from,
            publishes_to=publishes_to,
            depends_on=parse_comma_list(options.get("depends-on", "")),
            feeds_into=parse_comma_list(options.get("feeds-into", "")),
            docname=docname,
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    # Query methods from AcceleratorRepository protocol

    async def get_by_status(self, status: str) -> list[Accelerator]:
        """Get all accelerators with a specific status."""
        status_normalized = status.lower().strip()
        return [
            acc
            for acc in self.storage.values()
            if acc.status_normalized == status_normalized
        ]

    async def get_by_docname(self, docname: str) -> list[Accelerator]:
        """Get all accelerators defined in a specific document."""
        return [acc for acc in self.storage.values() if acc.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all accelerators defined in a specific document."""
        to_remove = [
            slug for slug, acc in self.storage.items() if acc.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)

    async def get_by_integration(
        self, integration_slug: str, relationship: str
    ) -> list[Accelerator]:
        """Get accelerators that have a relationship with an integration."""
        results = []
        for acc in self.storage.values():
            if relationship == "sources_from":
                if any(ref.slug == integration_slug for ref in acc.sources_from):
                    results.append(acc)
            elif relationship == "publishes_to":
                if any(ref.slug == integration_slug for ref in acc.publishes_to):
                    results.append(acc)
        return results

    async def get_dependents(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that depend on a specific accelerator."""
        return [
            acc for acc in self.storage.values() if accelerator_slug in acc.depends_on
        ]

    async def get_fed_by(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that feed into a specific accelerator."""
        return [
            acc for acc in self.storage.values() if accelerator_slug in acc.feeds_into
        ]

    async def get_all_statuses(self) -> set[str]:
        """Get all unique statuses across all accelerators."""
        return {
            acc.status_normalized
            for acc in self.storage.values()
            if acc.status_normalized
        }
