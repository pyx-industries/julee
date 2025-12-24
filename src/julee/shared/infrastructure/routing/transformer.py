"""RequestTransformer implementation using the routing registry.

Provides a concrete RequestTransformer that delegates to registered
transformer functions in the RoutingRegistry.
"""

from pydantic import BaseModel

from julee.shared.domain.models.route import Route
from julee.shared.domain.services.request_transformer import RequestTransformer


class RegistryRequestTransformer:
    """RequestTransformer that uses the global routing registry.

    Looks up transformer functions by (response_type, request_type) pair
    and delegates to them.

    This implementation satisfies the RequestTransformer protocol.
    """

    def __init__(self, registry: "RoutingRegistry | None" = None) -> None:
        """Initialize with optional registry.

        Args:
            registry: RoutingRegistry to use. If None, uses global registry.
        """
        if registry is None:
            from julee.shared.infrastructure.routing.config import routing_registry
            registry = routing_registry
        self._registry = registry

    def transform(self, route: Route, response: BaseModel | dict) -> BaseModel:
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
                f"Register one with routing_registry.register_transformer()"
            )

        return transformer_fn(response)


# Type check that we satisfy the protocol
_: RequestTransformer = RegistryRequestTransformer()
