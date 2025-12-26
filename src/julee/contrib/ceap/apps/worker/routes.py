"""PipelineRoute configuration for CEAP pipelines.

Defines routing rules for CEAP workflow responses to downstream pipelines.
These routes can be loaded into a PipelineRouteRepository for use by the
PipelineRouteResponseUseCase.

See: docs/architecture/proposals/pipeline_router_design.md
"""

from julee.core.entities.pipeline_route import PipelineRoute

# CEAP routes configuration
#
# These routes define how CEAP workflow responses are routed to
# downstream pipelines based on response state.
#
# Note: Target pipelines and request types must be registered separately.
# The routes here only define the routing rules.

ceap_routes: list[PipelineRoute] = [
    # Route 1: When assembly completes successfully
    # PipelineRoute(
    #     response_type="ExtractAssembleResponse",
    #     condition=PipelineCondition.is_true("success"),
    #     pipeline="NotificationPipeline",
    #     request_type="NotifyAssemblyCompleteRequest",
    #     description="When assembly completes, notify stakeholders",
    # ),
    #
    # Route 2: When validation completes with violations
    # PipelineRoute(
    #     response_type="ValidateDocumentResponse",
    #     condition=PipelineCondition.is_false("passed"),
    #     pipeline="ViolationHandlerPipeline",
    #     request_type="HandleViolationsRequest",
    #     description="When validation fails, trigger violation handling",
    # ),
]


def get_ceap_routes() -> list[PipelineRoute]:
    """Get all CEAP routes.

    Returns:
        List of PipelineRoute configurations for CEAP pipelines.
    """
    return ceap_routes.copy()
