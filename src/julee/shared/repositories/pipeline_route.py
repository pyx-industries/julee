"""PipelineRouteRepository protocol for pipeline routing.

Defines the interface for accessing PipelineRoute entities. Implementations may
store routes in memory, files, databases, or fetch from external services.

The repository provides two access patterns:
- list_all(): Get all configured routes (for visualization, introspection)
- list_for_response_type(): Get routes filtered by response type (for routing)

See: docs/architecture/proposals/pipeline_router_design.md
"""

from typing import Protocol, runtime_checkable

from julee.shared.entities.pipeline_route import PipelineRoute


@runtime_checkable
class PipelineRouteRepository(Protocol):
    """Repository protocol for PipelineRoute entities.

    Provides access to routing rules that map response types and conditions
    to target pipelines and request types.

    All methods are async for consistency with julee patterns. Application
    layers can provide sync adapters where needed.
    """

    async def list_all(self) -> list[PipelineRoute]:
        """List all configured routes.

        Returns:
            List of all PipelineRoute entities in the repository

        Use cases:
        - CLI introspection (julee-admin routes list)
        - PlantUML diagram generation
        - Route debugging and validation
        """
        ...

    async def list_for_response_type(self, response_type: str) -> list[PipelineRoute]:
        """List routes that handle a specific response type.

        Args:
            response_type: Fully qualified name or class name of the response

        Returns:
            List of PipelineRoute entities that match the response type.
            Empty list if no routes match.

        Use cases:
        - PipelineRouteResponseUseCase routing logic
        - Efficient filtering without loading all routes
        """
        ...


# Backwards-compatible alias
RouteRepository = PipelineRouteRepository
