"""Kit repository protocol.

Defines how the framework discovers installed kits. The filesystem is not
the source of truth here: kits are installed distributions, so the default
implementation reads entry points.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.kit import Kit


@runtime_checkable
class KitRepository(Protocol):
    """Repository for installed kit manifests.

    Read-oriented: a kit is declared by the distribution that provides it,
    never created through the repository.
    """

    async def list_all(self) -> list[Kit]:
        """List every installed kit.

        Returns:
            All kits whose manifests load and validate
        """
        ...

    async def get(self, slug: str) -> Kit | None:
        """Get an installed kit by slug.

        Args:
            slug: The kit's identifier

        Returns:
            Kit if installed, None otherwise
        """
        ...
