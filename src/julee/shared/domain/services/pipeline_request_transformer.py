"""PipelineRequestTransformer service protocol.

Defines the interface for transforming a Response into a Request for
a target pipeline. This decouples Response and Request types from each
other, allowing different implementations for different contexts.

The transformer is keyed by (response_type, request_type) pairs from the
PipelineRoute. Each implementation registers transformation functions for the
type pairs it supports.

See: docs/architecture/proposals/pipeline_router_design.md
"""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from julee.shared.domain.models.pipeline_route import PipelineRoute


@runtime_checkable
class PipelineRequestTransformer(Protocol):
    """Service protocol for transforming responses to requests.

    Transforms a Response object into the appropriate Request object
    for a target pipeline, based on the PipelineRoute configuration.

    This is NOT async because transformations are pure data mappings
    with no I/O. The transformer simply extracts fields from the response
    and maps them to the target request structure.

    Implementations typically maintain a registry of transformation
    functions keyed by (response_type, request_type) pairs.
    """

    def transform(self, route: PipelineRoute, response: BaseModel) -> BaseModel:
        """Transform a response into a request for the target pipeline.

        Args:
            route: The PipelineRoute that matched the response, containing:
                - response_type: The type of the source response
                - request_type: The type of the target request
                - pipeline: The target pipeline (for error messages)
            response: The response object to transform

        Returns:
            A request object matching route.request_type

        Raises:
            ValueError: If no transformer is registered for the
                (response_type, request_type) pair

        Note:
            The transformation is synchronous - it's a pure data mapping
            with no I/O operations.
        """
        ...


# Backwards-compatible alias
RequestTransformer = PipelineRequestTransformer
