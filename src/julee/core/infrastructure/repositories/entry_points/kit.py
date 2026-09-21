"""Entry-point based kit repository.

Kits announce themselves through the ``julee.kits`` entry-point group. Each
entry point resolves to a :class:`~julee.core.entities.kit.Kit` manifest.

Loading a manifest imports the kit's top-level module, which is why a
manifest must be a plain value: no side effects, no imports of FastAPI,
Temporal or Sphinx at module scope.
"""

import logging
from importlib.metadata import entry_points

from julee.core.entities.kit import Kit

__all__ = ["ENTRY_POINT_GROUP", "EntryPointKitRepository"]

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "julee.kits"
"""The entry-point group kits register their manifest in."""


class EntryPointKitRepository:
    """Reads kit manifests from installed distributions."""

    def list_all_sync(self) -> list[Kit]:
        """List every installed kit whose manifest loads.

        A manifest that fails to load, or that is not a Kit, is logged and
        skipped: one broken kit must not stop a solution from starting.

        Returns:
            Installed kits, ordered by slug
        """
        kits: list[Kit] = []
        for entry_point in entry_points(group=ENTRY_POINT_GROUP):
            try:
                manifest = entry_point.load()
            except Exception:
                logger.warning(
                    "Could not load kit manifest for %s",
                    entry_point.name,
                    exc_info=True,
                )
                continue
            if not isinstance(manifest, Kit):
                logger.warning(
                    "Kit manifest for %s is %s, expected a Kit",
                    entry_point.name,
                    type(manifest).__name__,
                )
                continue
            if manifest.slug != entry_point.name:
                logger.warning(
                    "Kit %s declares slug %r; using the entry-point name",
                    entry_point.name,
                    manifest.slug,
                )
                manifest = manifest.model_copy(update={"slug": entry_point.name})
            kits.append(manifest)
        return sorted(kits, key=lambda kit: kit.slug)

    def get_sync(self, slug: str) -> Kit | None:
        """Get an installed kit by slug.

        Args:
            slug: The kit's identifier

        Returns:
            Kit if installed, None otherwise
        """
        for kit in self.list_all_sync():
            if kit.slug == slug:
                return kit
        return None

    async def list_all(self) -> list[Kit]:
        """List every installed kit. See :meth:`list_all_sync`."""
        return self.list_all_sync()

    async def get(self, slug: str) -> Kit | None:
        """Get an installed kit by slug. See :meth:`get_sync`."""
        return self.get_sync(slug)
