"""Dependency injection for sphinx_hcd extension.

Provides factory functions for creating handlers, services, and use cases
used by the extension.
"""

from typing import TYPE_CHECKING

from julee.hcd.use_cases.crud import (
    CreateAcceleratorUseCase,
    CreateEpicUseCase,
)

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
    from .context import HCDContext
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


# Use Case Factories
# These provide configured use case instances for directives


def get_create_accelerator_use_case(context: "HCDContext") -> CreateAcceleratorUseCase:
    """Get a CreateAcceleratorUseCase configured with context repositories.

    Args:
        context: HCD context with repositories

    Returns:
        Configured CreateAcceleratorUseCase instance
    """
    return CreateAcceleratorUseCase(context.accelerator_repo.async_repo)


def get_create_epic_use_case(context: "HCDContext") -> CreateEpicUseCase:
    """Get a CreateEpicUseCase configured with context repositories.

    Args:
        context: HCD context with repositories

    Returns:
        Configured CreateEpicUseCase instance
    """
    return CreateEpicUseCase(context.epic_repo.async_repo)
