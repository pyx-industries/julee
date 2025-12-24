"""Route configuration for polling pipelines.

Defines routing rules for NewDataDetectionResponse to downstream pipelines.
These routes can be loaded into a RouteRepository for use by the
RouteResponseUseCase.

See: docs/architecture/proposals/pipeline_router_design.md
"""

from julee.shared.domain.models.route import Condition, Route

# Polling routes configuration
#
# These routes define how NewDataDetectionResponse is routed to
# downstream pipelines based on response state.
#
# Note: Target pipelines and request types must be registered separately.
# The routes here only define the routing rules.

polling_routes: list[Route] = [
    # Route 1: When new data is detected and processing should occur
    # Route(
    #     response_type="NewDataDetectionResponse",
    #     condition=Condition.is_true("should_process"),
    #     pipeline="DocumentProcessingPipeline",
    #     request_type="ProcessDocumentRequest",
    #     description="When new data detected, trigger document processing",
    # ),
    #
    # Route 2: When an error occurs during polling
    # Route(
    #     response_type="NewDataDetectionResponse",
    #     condition=Condition.is_true("has_error"),
    #     pipeline="ErrorNotificationPipeline",
    #     request_type="NotifyErrorRequest",
    #     description="When polling fails, notify error handler",
    # ),
]


def get_polling_routes() -> list[Route]:
    """Get all polling routes.

    Returns:
        List of Route configurations for polling pipelines.
    """
    return polling_routes.copy()
