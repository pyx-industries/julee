"""PipelineRequestTransformer implementation using the pipeline routing registry.

Provides a concrete PipelineRequestTransformer that delegates to registered
transformer functions in the PipelineRoutingRegistry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from julee.shared.domain.models.pipeline_route import PipelineRoute
from julee.shared.domain.services.pipeline_request_transformer import (
    PipelineRequestTransformer,
)

if TYPE_CHECKING:
    from julee.shared.infrastructure.pipeline_routing.config import (
        PipelineRoutingRegistry,
    )


class RegistryPipelineRequestTransformer:
    """PipelineRequestTransformer that uses the global pipeline routing registry.

    Looks up transformer functions by (response_type, request_type) pair
    and delegates to them.

    This implementation satisfies the PipelineRequestTransformer protocol.
    """

    def __init__(self, registry: PipelineRoutingRegistry | None = None) -> None:
        """Initialize with optional registry.

        Args:
            registry: PipelineRoutingRegistry to use. If None, uses global registry.
        """
        if registry is None:
            from julee.shared.infrastructure.pipeline_routing.config import (
                pipeline_routing_registry,
            )

            registry = pipeline_routing_registry
        self._registry = registry

    def transform(self, route: PipelineRoute, response: BaseModel | dict) -> BaseModel:
        """Transform a response into a request for the target pipeline.

        Args:
            route: The matched route (contains response_type, request_type)
            response: The response to transform (may be dict if serialized)

        Returns:
            Request object for the target pipeline

        Raises:
            ValueError: If no transformer is registered for the type pair
        """
        transformer_fn = self._registry.get_transformer(
            route.response_type,
            route.request_type,
        )

        if transformer_fn is None:
            raise ValueError(
                f"No transformer registered for "
                f"({route.response_type}, {route.request_type}). "
                f"Register one with pipeline_routing_registry.register_transformer()"
            )

        return transformer_fn(response)


# Backwards-compatible alias
RegistryRequestTransformer = RegistryPipelineRequestTransformer


# Type check that we satisfy the protocol
_: PipelineRequestTransformer = RegistryPipelineRequestTransformer()
