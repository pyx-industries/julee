"""Routing configuration and registry.

Provides a central registry for routes and transformers that solution
developers configure at startup. Pipelines use this registry to route
responses to downstream pipelines.
"""

import importlib
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from julee.shared.domain.models.route import Route
from julee.shared.repositories.memory.route import InMemoryRouteRepository

logger = logging.getLogger(__name__)


# Type alias for transformer functions
TransformerFn = Callable[[BaseModel | dict], BaseModel]


class RoutingRegistry:
    """Registry for routes and transformers.

    Solution developers register their routing configuration here.
    Pipelines query this registry to route responses to downstream pipelines.

    Thread Safety:
        This registry is NOT thread-safe. Configuration should happen
        at startup before any workflows run.
    """

    def __init__(self) -> None:
        self._routes: list[Route] = []
        self._transformers: dict[tuple[str, str], TransformerFn] = {}
        self._route_modules: list[str] = []

    def register_route(self, route: Route) -> "RoutingRegistry":
        """Register a single route.

        Args:
            route: Route to register

        Returns:
            self for method chaining
        """
        self._routes.append(route)
        logger.debug(
            f"Registered route: {route.response_type} -> {route.pipeline}"
        )
        return self

    def register_routes(self, routes: list[Route]) -> "RoutingRegistry":
        """Register multiple routes.

        Args:
            routes: Routes to register

        Returns:
            self for method chaining
        """
        for route in routes:
            self.register_route(route)
        return self

    def register_transformer(
        self,
        response_type: str,
        request_type: str,
        transformer: TransformerFn,
    ) -> "RoutingRegistry":
        """Register a transformer function for a type pair.

        Args:
            response_type: Source response type name (class name or FQN)
            request_type: Target request type name (class name or FQN)
            transformer: Function that transforms response to request

        Returns:
            self for method chaining
        """
        # Register both FQN and simple name for flexibility
        key = (response_type, request_type)
        self._transformers[key] = transformer

        # Also register with simple names
        simple_response = response_type.split(".")[-1]
        simple_request = request_type.split(".")[-1]
        simple_key = (simple_response, simple_request)
        if simple_key != key:
            self._transformers[simple_key] = transformer

        logger.debug(f"Registered transformer: {response_type} -> {request_type}")
        return self

    def register_route_module(self, module_name: str) -> "RoutingRegistry":
        """Register a module to load routes from.

        The module should have either:
        - A `get_*_routes()` function returning list[Route]
        - A `*_routes` variable containing list[Route]

        Args:
            module_name: Fully qualified module name

        Returns:
            self for method chaining
        """
        self._route_modules.append(module_name)
        return self

    def load_route_modules(self) -> "RoutingRegistry":
        """Load routes from all registered modules.

        Call this after registering modules but before workflows run.

        Returns:
            self for method chaining
        """
        for module_name in self._route_modules:
            try:
                module = importlib.import_module(module_name)

                # Look for get_*_routes() functions
                for name in dir(module):
                    if name.startswith("get_") and name.endswith("_routes"):
                        func = getattr(module, name)
                        if callable(func):
                            routes = func()
                            if isinstance(routes, list):
                                self.register_routes(routes)

                # Look for *_routes lists
                for name in dir(module):
                    if name.endswith("_routes") and not name.startswith("get_"):
                        value = getattr(module, name)
                        if isinstance(value, list) and all(
                            isinstance(r, Route) for r in value
                        ):
                            self.register_routes(value)

                logger.info(f"Loaded routes from module: {module_name}")

            except ImportError as e:
                logger.warning(f"Could not load route module {module_name}: {e}")
            except Exception as e:
                logger.error(f"Error loading routes from {module_name}: {e}")

        return self

    def get_route_repository(self) -> InMemoryRouteRepository:
        """Get a route repository with all registered routes.

        Returns:
            InMemoryRouteRepository populated with registered routes
        """
        return InMemoryRouteRepository(self._routes.copy())

    def get_transformer(
        self,
        response_type: str,
        request_type: str,
    ) -> TransformerFn | None:
        """Get the transformer for a type pair.

        Args:
            response_type: Source response type
            request_type: Target request type

        Returns:
            Transformer function if registered, None otherwise
        """
        # Try exact match first
        key = (response_type, request_type)
        if key in self._transformers:
            return self._transformers[key]

        # Try simple names
        simple_response = response_type.split(".")[-1]
        simple_request = request_type.split(".")[-1]
        simple_key = (simple_response, simple_request)
        return self._transformers.get(simple_key)

    def clear(self) -> None:
        """Clear all registered routes and transformers.

        Primarily for testing.
        """
        self._routes.clear()
        self._transformers.clear()
        self._route_modules.clear()

    @property
    def route_count(self) -> int:
        """Number of registered routes."""
        return len(self._routes)

    @property
    def transformer_count(self) -> int:
        """Number of registered transformers."""
        return len(self._transformers)


# Global registry instance
# Solution developers import and configure this at startup
routing_registry = RoutingRegistry()
