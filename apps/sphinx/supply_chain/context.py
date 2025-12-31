"""Supply Chain Sphinx context.

Provides access to supply chain repositories and use cases during Sphinx builds.
"""

from typing import TYPE_CHECKING

from apps.sphinx.hcd.adapters import SyncRepositoryAdapter
from julee.supply_chain.infrastructure.repositories.memory.accelerator import (
    MemoryAcceleratorRepository,
)

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from julee.supply_chain.entities.accelerator import Accelerator


class SupplyChainContext:
    """Context for supply chain Sphinx extension.

    Provides access to accelerator repository and use cases.
    """

    def __init__(self):
        """Initialize with in-memory repositories wrapped in SyncRepositoryAdapter."""
        self._accelerator_repo = SyncRepositoryAdapter(MemoryAcceleratorRepository())

    @property
    def accelerator_repo(self) -> "SyncRepositoryAdapter[Accelerator]":
        """Get accelerator repository adapter."""
        return self._accelerator_repo


# Module-level context storage
_supply_chain_context: SupplyChainContext | None = None


def get_supply_chain_context(app: "Sphinx | None" = None) -> SupplyChainContext:
    """Get the supply chain context, creating if needed.

    Args:
        app: Sphinx application (optional, for future use)

    Returns:
        SupplyChainContext instance
    """
    global _supply_chain_context
    if _supply_chain_context is None:
        _supply_chain_context = SupplyChainContext()
    return _supply_chain_context


def set_supply_chain_context(ctx: SupplyChainContext) -> None:
    """Set the supply chain context.

    Args:
        ctx: Context to set
    """
    global _supply_chain_context
    _supply_chain_context = ctx


def ensure_supply_chain_context(app: "Sphinx") -> SupplyChainContext:
    """Ensure supply chain context exists on Sphinx env.

    Args:
        app: Sphinx application

    Returns:
        SupplyChainContext instance
    """
    if not hasattr(app.env, "supply_chain_context"):
        app.env.supply_chain_context = SupplyChainContext()
    return app.env.supply_chain_context
