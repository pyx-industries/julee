"""Handler implementations for sphinx_hcd extension.

Note: AcceleratorPlaceholderHandler, CodeLinksPlaceholderHandler,
and EntityDiagramPlaceholderHandler moved to apps.sphinx.supply_chain.
"""

from .placeholder_resolution import (
    AppPlaceholderHandler,
    C4BridgePlaceholderHandler,
    ContribPlaceholderHandler,
    EpicPlaceholderHandler,
    IntegrationPlaceholderHandler,
    JourneyPlaceholderHandler,
    PersonaPlaceholderHandler,
)

__all__ = [
    "AppPlaceholderHandler",
    "C4BridgePlaceholderHandler",
    "ContribPlaceholderHandler",
    "EpicPlaceholderHandler",
    "IntegrationPlaceholderHandler",
    "JourneyPlaceholderHandler",
    "PersonaPlaceholderHandler",
]
