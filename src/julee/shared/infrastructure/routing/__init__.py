"""Routing infrastructure for pipeline orchestration.

Provides configuration and runtime support for routing responses
to downstream pipelines. This module is used by pipelines' run_next()
methods to determine and execute downstream dispatches.

Solution developers configure routing by:
1. Defining routes in their solution's route modules
2. Implementing transformers for their response→request type pairs
3. Registering both with the RoutingRegistry

Example:
    # In solution's routing config
    from julee.shared.infrastructure.routing import routing_registry

    routing_registry.register_routes(my_routes)
    routing_registry.register_transformer("MyResponse", "MyRequest", my_transform_fn)
"""

from julee.shared.infrastructure.routing.config import (
    RoutingRegistry,
    routing_registry,
)
from julee.shared.infrastructure.routing.transformer import (
    RegistryRequestTransformer,
)

__all__ = [
    "RegistryRequestTransformer",
    "RoutingRegistry",
    "routing_registry",
]
