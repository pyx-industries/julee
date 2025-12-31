"""Tests for placeholder resolution handlers."""



class TestHandlerImports:
    """Test that handler modules import correctly."""

    def test_placeholder_handler_protocol_imports(self) -> None:
        """Test PlaceholderResolutionHandler protocol imports."""
        from apps.sphinx.hcd.services.placeholder_handlers import (
            BasePlaceholderHandler,
            PlaceholderResolutionHandler,
        )

        assert PlaceholderResolutionHandler is not None
        assert BasePlaceholderHandler is not None

    def test_handler_implementations_import(self) -> None:
        """Test handler implementations import."""
        # NOTE: AcceleratorPlaceholderHandler, CodeLinksPlaceholderHandler,
        # EntityDiagramPlaceholderHandler moved to apps.sphinx.supply_chain
        from apps.sphinx.hcd.infrastructure.handlers import (
            AppPlaceholderHandler,
            C4BridgePlaceholderHandler,
            ContribPlaceholderHandler,
            EpicPlaceholderHandler,
            IntegrationPlaceholderHandler,
            JourneyPlaceholderHandler,
            PersonaPlaceholderHandler,
        )

        assert AppPlaceholderHandler is not None
        assert EpicPlaceholderHandler is not None
        assert IntegrationPlaceholderHandler is not None
        assert PersonaPlaceholderHandler is not None
        assert JourneyPlaceholderHandler is not None
        assert ContribPlaceholderHandler is not None
        assert C4BridgePlaceholderHandler is not None

    def test_dependencies_import(self) -> None:
        """Test dependencies module imports."""
        from apps.sphinx.hcd.dependencies import get_placeholder_handlers

        assert get_placeholder_handlers is not None

    def test_get_placeholder_handlers_returns_handlers(self) -> None:
        """Test get_placeholder_handlers returns correct handlers."""
        from apps.sphinx.hcd.dependencies import get_placeholder_handlers

        handlers = get_placeholder_handlers()

        # NOTE: AcceleratorPlaceholderHandler, CodeLinksPlaceholderHandler,
        # EntityDiagramPlaceholderHandler moved to apps.sphinx.supply_chain
        assert len(handlers) == 7
        names = [h.name for h in handlers]
        assert "App" in names
        assert "Epic" in names
        assert "Integration" in names
        assert "Persona" in names
        assert "Journey" in names
        assert "Contrib" in names
        assert "C4Bridge" in names


class TestUseCaseFactories:
    """Test use case factory functions."""

    def test_use_case_factory_imports(self) -> None:
        """Test use case factories import correctly."""
        # NOTE: get_create_accelerator_use_case moved to apps.sphinx.supply_chain
        from apps.sphinx.hcd.dependencies import get_create_epic_use_case

        assert get_create_epic_use_case is not None

    def test_get_create_accelerator_use_case(self) -> None:
        """Test get_create_accelerator_use_case returns configured use case."""
        # NOTE: Accelerator use case factory moved to apps.sphinx.supply_chain
        from apps.sphinx.supply_chain.context import SupplyChainContext
        from apps.sphinx.supply_chain.dependencies import get_create_accelerator_use_case
        from julee.supply_chain.use_cases.crud import CreateAcceleratorUseCase

        context = SupplyChainContext()
        use_case = get_create_accelerator_use_case(context)

        assert isinstance(use_case, CreateAcceleratorUseCase)

    def test_get_create_epic_use_case(self) -> None:
        """Test get_create_epic_use_case returns configured use case."""
        from apps.sphinx.hcd.context import HCDContext
        from apps.sphinx.hcd.dependencies import get_create_epic_use_case
        from julee.hcd.use_cases.crud import CreateEpicUseCase

        context = HCDContext()
        use_case = get_create_epic_use_case(context)

        assert isinstance(use_case, CreateEpicUseCase)
