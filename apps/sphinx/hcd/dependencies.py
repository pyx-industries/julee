"""Dependency injection for sphinx_hcd extension.

Provides factory functions for creating handlers, services, and use cases
used by the extension.

Note: Accelerator handlers and use case factories moved to apps.sphinx.supply_chain.
"""

from typing import TYPE_CHECKING

from julee.hcd.use_cases.crud import CreateEpicUseCase

from .infrastructure.handlers import (
    AppPlaceholderHandler,
    C4BridgePlaceholderHandler,
    ContribPlaceholderHandler,
    EpicPlaceholderHandler,
    IntegrationPlaceholderHandler,
    JourneyPlaceholderHandler,
    PersonaPlaceholderHandler,
)

if TYPE_CHECKING:
    from .context import HCDContext
    from .services.placeholder_handlers import PlaceholderResolutionHandler


def get_placeholder_handlers() -> list["PlaceholderResolutionHandler"]:
    """Get all placeholder resolution handlers.

    Returns handlers in the order they should be processed.
    Order matters for some cross-references.

    Note: AcceleratorPlaceholderHandler moved to apps.sphinx.supply_chain.

    Returns:
        List of placeholder resolution handlers
    """
    return [
        # Core entity handlers
        AppPlaceholderHandler(),
        EpicPlaceholderHandler(),
        IntegrationPlaceholderHandler(),
        PersonaPlaceholderHandler(),
        JourneyPlaceholderHandler(),
        ContribPlaceholderHandler(),
        # Cross-cutting handlers
        C4BridgePlaceholderHandler(),
        # NOTE: CodeLinksPlaceholderHandler and EntityDiagramPlaceholderHandler
        # moved to apps.sphinx.supply_chain
    ]


# Use Case Factories
# These provide configured use case instances for directives


def get_create_epic_use_case(context: "HCDContext") -> CreateEpicUseCase:
    """Get a CreateEpicUseCase configured with context repositories.

    Args:
        context: HCD context with repositories

    Returns:
        Configured CreateEpicUseCase instance
    """
    return CreateEpicUseCase(context.epic_repo.async_repo)
