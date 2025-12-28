"""Tests for placeholder resolution handlers."""

import pytest


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
        from apps.sphinx.hcd.infrastructure.handlers import (
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

        assert AppPlaceholderHandler is not None
        assert EpicPlaceholderHandler is not None
        assert AcceleratorPlaceholderHandler is not None
        assert IntegrationPlaceholderHandler is not None
        assert PersonaPlaceholderHandler is not None
        assert JourneyPlaceholderHandler is not None
        assert ContribPlaceholderHandler is not None
        assert C4BridgePlaceholderHandler is not None
        assert CodeLinksPlaceholderHandler is not None
        assert EntityDiagramPlaceholderHandler is not None

    def test_dependencies_import(self) -> None:
        """Test dependencies module imports."""
        from apps.sphinx.hcd.dependencies import get_placeholder_handlers

        assert get_placeholder_handlers is not None

    def test_get_placeholder_handlers_returns_handlers(self) -> None:
        """Test get_placeholder_handlers returns correct handlers."""
        from apps.sphinx.hcd.dependencies import get_placeholder_handlers

        handlers = get_placeholder_handlers()

        assert len(handlers) == 10
        names = [h.name for h in handlers]
        assert "App" in names
        assert "Epic" in names
        assert "Accelerator" in names
        assert "Integration" in names
        assert "Persona" in names
        assert "Journey" in names
        assert "Contrib" in names
        assert "C4Bridge" in names
        assert "CodeLinks" in names
        assert "EntityDiagram" in names
