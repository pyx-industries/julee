"""In-memory PipelineRouteRepository implementation.

Provides a simple in-memory storage for PipelineRoute entities. Routes can be
configured at startup from code, configuration files, or other sources.

See: docs/architecture/proposals/pipeline_router_design.md
"""

import logging
from collections import defaultdict

from julee.shared.domain.models.pipeline_route import PipelineRoute

logger = logging.getLogger(__name__)


class InMemoryPipelineRouteRepository:
    """In-memory implementation of PipelineRouteRepository.

    Stores routes in memory with indexing by response_type for efficient
    lookup. Routes are typically loaded at startup and remain static
    during runtime.

    Thread-safety: This implementation is NOT thread-safe. For concurrent
    access, use external synchronization or a thread-safe implementation.
    """

    def __init__(self, routes: list[PipelineRoute] | None = None) -> None:
        """Initialize with optional pre-configured routes.

        Args:
            routes: Initial list of routes to store
        """
        self._routes: list[PipelineRoute] = []
        self._by_response_type: dict[str, list[PipelineRoute]] = defaultdict(list)

        if routes:
            for route in routes:
                self._add_route(route)

    def _add_route(self, route: PipelineRoute) -> None:
        """Add a route to storage and update index."""
        self._routes.append(route)
        self._by_response_type[route.response_type].append(route)

        # Also index by simple class name for flexibility
        simple_name = route.response_type.split(".")[-1]
        if simple_name != route.response_type:
            self._by_response_type[simple_name].append(route)

    async def list_all(self) -> list[PipelineRoute]:
        """List all configured routes.

        Returns:
            List of all PipelineRoute entities
        """
        logger.debug(
            "InMemoryPipelineRouteRepository: Listing all routes",
            extra={"route_count": len(self._routes)},
        )
        return list(self._routes)

    async def list_for_response_type(self, response_type: str) -> list[PipelineRoute]:
        """List routes that handle a specific response type.

        Args:
            response_type: FQN or simple class name of the response

        Returns:
            List of PipelineRoute entities that match the response type.
            Empty list if no routes match.
        """
        routes = self._by_response_type.get(response_type, [])
        logger.debug(
            "InMemoryPipelineRouteRepository: Listing routes for response type",
            extra={
                "response_type": response_type,
                "route_count": len(routes),
            },
        )
        return list(routes)

    def add_route(self, route: PipelineRoute) -> "InMemoryPipelineRouteRepository":
        """Add a route (fluent API for configuration).

        Args:
            route: PipelineRoute to add

        Returns:
            self for method chaining
        """
        self._add_route(route)
        return self

    def add_routes(self, routes: list[PipelineRoute]) -> "InMemoryPipelineRouteRepository":
        """Add multiple routes (fluent API for configuration).

        Args:
            routes: PipelineRoutes to add

        Returns:
            self for method chaining
        """
        for route in routes:
            self._add_route(route)
        return self

    def clear(self) -> None:
        """Remove all routes from storage."""
        count = len(self._routes)
        self._routes.clear()
        self._by_response_type.clear()
        logger.debug(
            "InMemoryPipelineRouteRepository: Cleared routes",
            extra={"cleared_count": count},
        )


# Backwards-compatible alias
InMemoryRouteRepository = InMemoryPipelineRouteRepository
