"""PipelineRoute configuration for polling pipelines.

Defines routing rules for NewDataDetectionResponse to downstream pipelines.
These routes can be loaded into a PipelineRouteRepository for use by the
PipelineRouteResponseUseCase.

See: docs/architecture/proposals/pipeline_router_design.md
"""

from julee.core.entities.pipeline_route import PipelineRoute

# Polling routes configuration
#
# These routes define how NewDataDetectionResponse is routed to
# downstream pipelines based on response state.
#
# Note: Target pipelines and request types must be registered separately.
# The routes here only define the routing rules.

polling_routes: list[PipelineRoute] = [
    # Route 1: When new data is detected and processing should occur
    # PipelineRoute(
    #     response_type="NewDataDetectionResponse",
    #     condition=PipelineCondition.is_true("should_process"),
    #     pipeline="DocumentProcessingPipeline",
    #     request_type="ProcessDocumentRequest",
    #     description="When new data detected, trigger document processing",
    # ),
    #
    # Route 2: When an error occurs during polling
    # PipelineRoute(
    #     response_type="NewDataDetectionResponse",
    #     condition=PipelineCondition.is_true("has_error"),
    #     pipeline="ErrorNotificationPipeline",
    #     request_type="NotifyErrorRequest",
    #     description="When polling fails, notify error handler",
    # ),
]


def get_polling_routes() -> list[PipelineRoute]:
    """Get all polling routes.

    Returns:
        List of PipelineRoute configurations for polling pipelines.
    """
    return polling_routes.copy()
