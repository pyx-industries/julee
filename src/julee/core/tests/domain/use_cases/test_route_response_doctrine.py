"""PipelineRouteResponseUseCase doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

PipelineRouteResponseUseCase is responsible for routing a response to zero or more
downstream pipelines. It uses PipelineRouteRepository to find matching routes and
PipelineRequestTransformer to build the appropriate requests.

See: docs/architecture/proposals/pipeline_router_design.md
"""

import pytest
from pydantic import BaseModel

# =============================================================================
# MOCK IMPLEMENTATIONS FOR TESTING
# =============================================================================


class MockResponse(BaseModel):
    """Sample response for testing."""

    has_new_data: bool = True
    needs_notification: bool = False
    content: bytes = b"test"
    current_hash: str = "abc123"
    endpoint_id: str = "ep-1"


class MockRequestA(BaseModel):
    """Sample request A for testing."""

    data: bytes
    source_hash: str


class MockRequestB(BaseModel):
    """Sample request B for testing."""

    message: str
    source_id: str


# =============================================================================
# DOCTRINE: PipelineRouteResponseUseCase Structure
# =============================================================================


class TestPipelineRouteResponseUseCaseStructure:
    """Doctrine about PipelineRouteResponseUseCase structure."""

    def test_use_case_MUST_accept_route_repository_dependency(self):
        """PipelineRouteResponseUseCase MUST accept PipelineRouteRepository as a dependency."""
        import inspect

        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseUseCase,
        )

        sig = inspect.signature(PipelineRouteResponseUseCase.__init__)
        params = list(sig.parameters.keys())
        assert "route_repository" in params

    def test_use_case_MUST_accept_request_transformer_dependency(self):
        """PipelineRouteResponseUseCase MUST accept PipelineRequestTransformer as a dependency."""
        import inspect

        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseUseCase,
        )

        sig = inspect.signature(PipelineRouteResponseUseCase.__init__)
        params = list(sig.parameters.keys())
        assert "request_transformer" in params

    def test_use_case_MUST_have_execute_method(self):
        """PipelineRouteResponseUseCase MUST have an execute() method."""
        import inspect

        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseUseCase,
        )

        assert hasattr(PipelineRouteResponseUseCase, "execute")
        assert inspect.iscoroutinefunction(PipelineRouteResponseUseCase.execute)


# =============================================================================
# DOCTRINE: Request/Response Models
# =============================================================================


class TestPipelineRouteResponseRequestDoctrine:
    """Doctrine about PipelineRouteResponseRequest."""

    def test_request_MUST_have_response_field(self):
        """PipelineRouteResponseRequest MUST have a response field (serialized)."""
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
        )

        request = PipelineRouteResponseRequest(
            response={"has_new_data": True},
            response_type="MockResponse",
        )
        assert request.response == {"has_new_data": True}

    def test_request_MUST_have_response_type_field(self):
        """PipelineRouteResponseRequest MUST have response_type for route matching."""
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
        )

        request = PipelineRouteResponseRequest(
            response={"has_new_data": True},
            response_type="MockResponse",
        )
        assert request.response_type == "MockResponse"


class TestPipelineRouteResponseResponseDoctrine:
    """Doctrine about PipelineRouteResponseResponse."""

    def test_response_MUST_have_dispatches_field(self):
        """PipelineRouteResponseResponse MUST have dispatches list."""
        from julee.core.use_cases.pipeline_route_response import (
            PipelineDispatch,
            PipelineRouteResponseResponse,
        )

        response = PipelineRouteResponseResponse(
            dispatches=[
                PipelineDispatch(pipeline="TestPipeline", request={"foo": "bar"})
            ]
        )
        assert len(response.dispatches) == 1


class TestPipelineDispatchDoctrine:
    """Doctrine about PipelineDispatch."""

    def test_dispatch_MUST_have_pipeline_field(self):
        """PipelineDispatch MUST specify target pipeline."""
        from julee.core.use_cases.pipeline_route_response import (
            PipelineDispatch,
        )

        dispatch = PipelineDispatch(pipeline="NextPipeline", request={"data": "test"})
        assert dispatch.pipeline == "NextPipeline"

    def test_dispatch_MUST_have_request_field(self):
        """PipelineDispatch MUST contain serialized request."""
        from julee.core.use_cases.pipeline_route_response import (
            PipelineDispatch,
        )

        dispatch = PipelineDispatch(pipeline="NextPipeline", request={"data": "test"})
        assert dispatch.request == {"data": "test"}


# =============================================================================
# DOCTRINE: PipelineRouteResponseUseCase Behavior
# =============================================================================


class TestPipelineRouteResponseUseCaseBehavior:
    """Doctrine about PipelineRouteResponseUseCase execution behavior."""

    @pytest.fixture
    def mock_route_repository(self):
        """Create mock route repository."""
        from julee.core.entities.pipeline_route import (
            PipelineRoute,
        )

        class MockPipelineRouteRepository:
            def __init__(self, routes: list[PipelineRoute]):
                self._routes = routes

            async def list_all(self) -> list[PipelineRoute]:
                return self._routes

            async def list_for_response_type(
                self, response_type: str
            ) -> list[PipelineRoute]:
                return [r for r in self._routes if r.response_type == response_type]

        return MockPipelineRouteRepository

    @pytest.fixture
    def mock_request_transformer(self):
        """Create mock request transformer."""
        from julee.core.entities.pipeline_route import PipelineRoute

        class MockPipelineRequestTransformer:
            def transform(self, route: PipelineRoute, response: BaseModel) -> BaseModel:
                if route.request_type == "MockRequestA":
                    return MockRequestA(
                        data=response.get("content", b""),
                        source_hash=response.get("current_hash", ""),
                    )
                elif route.request_type == "MockRequestB":
                    return MockRequestB(
                        message="notification",
                        source_id=response.get("endpoint_id", ""),
                    )
                raise ValueError(f"Unknown: {route.request_type}")

        return MockPipelineRequestTransformer()

    @pytest.mark.asyncio
    async def test_execute_MUST_return_matching_dispatches(
        self, mock_route_repository, mock_request_transformer
    ):
        """execute() MUST return dispatches for all matching routes."""
        from julee.core.entities.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
            PipelineRouteResponseUseCase,
        )

        routes = [
            PipelineRoute(
                response_type="MockResponse",
                condition=PipelineCondition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = PipelineRouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        request = PipelineRouteResponseRequest(
            response={"has_new_data": True, "content": b"data", "current_hash": "h1"},
            response_type="MockResponse",
        )

        response = await use_case.execute(request)

        assert len(response.dispatches) == 1
        assert response.dispatches[0].pipeline == "ProcessingPipeline"

    @pytest.mark.asyncio
    async def test_execute_MUST_return_multiple_dispatches_for_multiplex(
        self, mock_route_repository, mock_request_transformer
    ):
        """execute() MUST return multiple dispatches when multiple routes match."""
        from julee.core.entities.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
            PipelineRouteResponseUseCase,
        )

        routes = [
            PipelineRoute(
                response_type="MockResponse",
                condition=PipelineCondition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
            PipelineRoute(
                response_type="MockResponse",
                condition=PipelineCondition.is_true("needs_notification"),
                pipeline="NotificationPipeline",
                request_type="MockRequestB",
            ),
        ]

        use_case = PipelineRouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        # Both conditions are true
        request = PipelineRouteResponseRequest(
            response={
                "has_new_data": True,
                "needs_notification": True,
                "content": b"data",
                "current_hash": "h1",
                "endpoint_id": "ep-1",
            },
            response_type="MockResponse",
        )

        response = await use_case.execute(request)

        assert len(response.dispatches) == 2
        pipelines = {d.pipeline for d in response.dispatches}
        assert pipelines == {"ProcessingPipeline", "NotificationPipeline"}

    @pytest.mark.asyncio
    async def test_execute_MUST_return_empty_when_no_routes_match(
        self, mock_route_repository, mock_request_transformer
    ):
        """execute() MUST return empty dispatches when no routes match."""
        from julee.core.entities.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
            PipelineRouteResponseUseCase,
        )

        routes = [
            PipelineRoute(
                response_type="MockResponse",
                condition=PipelineCondition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = PipelineRouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        # Condition is false
        request = PipelineRouteResponseRequest(
            response={"has_new_data": False},
            response_type="MockResponse",
        )

        response = await use_case.execute(request)

        assert response.dispatches == []

    @pytest.mark.asyncio
    async def test_execute_MUST_filter_by_response_type(
        self, mock_route_repository, mock_request_transformer
    ):
        """execute() MUST only consider routes matching the response type."""
        from julee.core.entities.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
            PipelineRouteResponseUseCase,
        )

        routes = [
            PipelineRoute(
                response_type="MockResponse",
                condition=PipelineCondition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
            PipelineRoute(
                response_type="OtherResponse",
                condition=PipelineCondition.is_true("has_new_data"),
                pipeline="OtherPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = PipelineRouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        request = PipelineRouteResponseRequest(
            response={"has_new_data": True, "content": b"data", "current_hash": "h1"},
            response_type="MockResponse",  # Only match MockResponse routes
        )

        response = await use_case.execute(request)

        assert len(response.dispatches) == 1
        assert response.dispatches[0].pipeline == "ProcessingPipeline"

    @pytest.mark.asyncio
    async def test_execute_MUST_include_transformed_request_in_dispatch(
        self, mock_route_repository, mock_request_transformer
    ):
        """execute() MUST include the transformed request in each dispatch."""
        from julee.core.entities.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.core.use_cases.pipeline_route_response import (
            PipelineRouteResponseRequest,
            PipelineRouteResponseUseCase,
        )

        routes = [
            PipelineRoute(
                response_type="MockResponse",
                condition=PipelineCondition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = PipelineRouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        request = PipelineRouteResponseRequest(
            response={
                "has_new_data": True,
                "content": b"my content",
                "current_hash": "hash456",
            },
            response_type="MockResponse",
        )

        response = await use_case.execute(request)

        assert len(response.dispatches) == 1
        dispatch_request = response.dispatches[0].request
        # Should be serialized MockRequestA
        assert dispatch_request["source_hash"] == "hash456"
