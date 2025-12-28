"""Dependency injection for sphinx_hcd extension.

Provides factory functions for creating handlers and services
used by the extension.
"""

from typing import TYPE_CHECKING

from .infrastructure.handlers import (
    AcceleratorPlaceholderHandler,
    AppPlaceholderHandler,
    C4BridgePlaceholderHandler,
    CodeLinksPlaceholderHandler,
    ContribPlaceholderHandler,
    EntityDiagramPlaceholderHandler,
    EpicPlaceholderHandler,
    IntegrationPlaceholderHandler,
    JourneyPlaceholderHandler,
    PersonaPlaceholderHandler,
)

if TYPE_CHECKING:
    from .services.placeholder_handlers import PlaceholderResolutionHandler


def get_placeholder_handlers() -> list["PlaceholderResolutionHandler"]:
    """Get all placeholder resolution handlers.

    Returns handlers in the order they should be processed.
    Order matters for some cross-references.

    Returns:
        List of placeholder resolution handlers
    """
    return [
        # Core entity handlers
        AppPlaceholderHandler(),
        EpicPlaceholderHandler(),
        AcceleratorPlaceholderHandler(),
        IntegrationPlaceholderHandler(),
        PersonaPlaceholderHandler(),
        JourneyPlaceholderHandler(),
        ContribPlaceholderHandler(),
        # Cross-cutting handlers
        C4BridgePlaceholderHandler(),
        CodeLinksPlaceholderHandler(),
        EntityDiagramPlaceholderHandler(),
    ]
