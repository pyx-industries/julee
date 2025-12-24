"""RST file-backed implementation of AppRepository."""

import logging
from pathlib import Path

from julee.hcd.utils import normalize_name

from ...domain.models.app import App, AppType
from ...domain.repositories.app import AppRepository
from ...parsers.docutils_parser import ParsedDocument, parse_comma_list
from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstAppRepository(RstRepositoryMixin[App], AppRepository):
    """RST file-backed implementation of AppRepository.

    Apps are stored as individual RST files in a directory.
    Each file contains a single define-app directive.
    """

    entity_name = "App"
    id_field = "slug"
    entity_type = "app"
    directive_name = "define-app"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing app RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> App:
        """Build App entity from parsed data."""
        options = data.get("options", {})
        content = data.get("content", "")

        # Name from option or derive from slug
        name = options.get("name", "")
        if not name:
            name = data["slug"].replace("-", " ").title()

        # Parse app type
        app_type = AppType.from_string(options.get("type", "unknown"))

        return App(
            slug=data["slug"],
            name=name,
            app_type=app_type,
            status=options.get("status") or None,
            description=content.strip(),
            accelerators=parse_comma_list(options.get("accelerators", "")),
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    # Query methods from AppRepository protocol

    async def get_by_type(self, app_type: AppType) -> list[App]:
        """Get all apps of a specific type."""
        return [app for app in self.storage.values() if app.app_type == app_type]

    async def get_by_name(self, name: str) -> App | None:
        """Get an app by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        for app in self.storage.values():
            if app.name_normalized == name_normalized:
                return app
        return None

    async def get_all_types(self) -> set[AppType]:
        """Get all unique app types that have apps."""
        return {app.app_type for app in self.storage.values()}

    async def get_apps_with_accelerators(self) -> list[App]:
        """Get all apps that have accelerators defined."""
        return [app for app in self.storage.values() if app.accelerators]
