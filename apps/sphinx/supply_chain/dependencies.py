"""Dependency injection for sphinx_supply_chain extension.

Provides factory functions for creating handlers, services, and use cases
used by the extension.
"""

from typing import TYPE_CHECKING

from julee.supply_chain.use_cases.crud import CreateAcceleratorUseCase

if TYPE_CHECKING:
    from .context import SupplyChainContext
    from .services.placeholder_handlers import PlaceholderResolutionHandler


def get_placeholder_handlers() -> list["PlaceholderResolutionHandler"]:
    """Get all placeholder resolution handlers for supply chain.

    Returns handlers in the order they should be processed.

    Returns:
        List of placeholder resolution handlers
    """
    from .infrastructure.handlers import (
        AcceleratorPlaceholderHandler,
        CodeLinksPlaceholderHandler,
        EntityDiagramPlaceholderHandler,
    )

    return [
        AcceleratorPlaceholderHandler(),
        CodeLinksPlaceholderHandler(),
        EntityDiagramPlaceholderHandler(),
    ]


def get_create_accelerator_use_case(
    context: "SupplyChainContext",
) -> CreateAcceleratorUseCase:
    """Get a CreateAcceleratorUseCase configured with context repositories.

    Args:
        context: Supply chain context with repositories

    Returns:
        Configured CreateAcceleratorUseCase instance
    """
    return CreateAcceleratorUseCase(context.accelerator_repo.async_repo)
