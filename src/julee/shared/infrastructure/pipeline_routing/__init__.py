"""Pipeline routing infrastructure for pipeline orchestration.

Provides configuration and runtime support for routing responses
to downstream pipelines. This module is used by pipelines' run_next()
methods to determine and execute downstream dispatches.

Solution developers configure routing by:
1. Defining routes in their solution's route modules
2. Implementing transformers for their response→request type pairs
3. Registering both with the PipelineRoutingRegistry

Example:
    # In solution's routing config
    from julee.shared.infrastructure.pipeline_routing import pipeline_routing_registry

    pipeline_routing_registry.register_routes(my_routes)
    pipeline_routing_registry.register_transformer("MyResponse", "MyRequest", my_transform_fn)
"""

from julee.shared.infrastructure.pipeline_routing.config import (
    PipelineRoutingRegistry,
    pipeline_routing_registry,
)
from julee.shared.infrastructure.pipeline_routing.transformer import (
    RegistryPipelineRequestTransformer,
)

__all__ = [
    "PipelineRoutingRegistry",
    "RegistryPipelineRequestTransformer",
    "pipeline_routing_registry",
]

# Backwards-compatible aliases
RoutingRegistry = PipelineRoutingRegistry
routing_registry = pipeline_routing_registry
RegistryRequestTransformer = RegistryPipelineRequestTransformer
