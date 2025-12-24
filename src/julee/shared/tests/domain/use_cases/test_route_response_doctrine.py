"""RouteResponseUseCase doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

RouteResponseUseCase is responsible for routing a response to zero or more
downstream pipelines. It uses RouteRepository to find matching routes and
RequestTransformer to build the appropriate requests.

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
# DOCTRINE: RouteResponseUseCase Structure
# =============================================================================


class TestRouteResponseUseCaseStructure:
    """Doctrine about RouteResponseUseCase structure."""

    def test_use_case_MUST_accept_route_repository_dependency(self):
        """RouteResponseUseCase MUST accept RouteRepository as a dependency."""
        from julee.shared.domain.use_cases.route_response import RouteResponseUseCase
        import inspect

        sig = inspect.signature(RouteResponseUseCase.__init__)
        params = list(sig.parameters.keys())
        assert "route_repository" in params

    def test_use_case_MUST_accept_request_transformer_dependency(self):
        """RouteResponseUseCase MUST accept RequestTransformer as a dependency."""
        from julee.shared.domain.use_cases.route_response import RouteResponseUseCase
        import inspect

        sig = inspect.signature(RouteResponseUseCase.__init__)
        params = list(sig.parameters.keys())
        assert "request_transformer" in params

    def test_use_case_MUST_have_execute_method(self):
        """RouteResponseUseCase MUST have an execute() method."""
        from julee.shared.domain.use_cases.route_response import RouteResponseUseCase
        import inspect

        assert hasattr(RouteResponseUseCase, "execute")
        assert inspect.iscoroutinefunction(RouteResponseUseCase.execute)


# =============================================================================
# DOCTRINE: Request/Response Models
# =============================================================================


class TestRouteResponseRequestDoctrine:
    """Doctrine about RouteResponseRequest."""

    def test_request_MUST_have_response_field(self):
        """RouteResponseRequest MUST have a response field (serialized)."""
        from julee.shared.domain.use_cases.route_response import RouteResponseRequest

        request = RouteResponseRequest(
            response={"has_new_data": True},
            response_type="MockResponse",
        )
        assert request.response == {"has_new_data": True}

    def test_request_MUST_have_response_type_field(self):
        """RouteResponseRequest MUST have response_type for route matching."""
        from julee.shared.domain.use_cases.route_response import RouteResponseRequest

        request = RouteResponseRequest(
            response={"has_new_data": True},
            response_type="MockResponse",
        )
        assert request.response_type == "MockResponse"


class TestRouteResponseResponseDoctrine:
    """Doctrine about RouteResponseResponse."""

    def test_response_MUST_have_dispatches_field(self):
        """RouteResponseResponse MUST have dispatches list."""
        from julee.shared.domain.use_cases.route_response import (
            PipelineDispatch,
            RouteResponseResponse,
        )

        response = RouteResponseResponse(
            dispatches=[
                PipelineDispatch(pipeline="TestPipeline", request={"foo": "bar"})
            ]
        )
        assert len(response.dispatches) == 1


class TestPipelineDispatchDoctrine:
    """Doctrine about PipelineDispatch."""

    def test_dispatch_MUST_have_pipeline_field(self):
        """PipelineDispatch MUST specify target pipeline."""
        from julee.shared.domain.use_cases.route_response import PipelineDispatch

        dispatch = PipelineDispatch(pipeline="NextPipeline", request={"data": "test"})
        assert dispatch.pipeline == "NextPipeline"

    def test_dispatch_MUST_have_request_field(self):
        """PipelineDispatch MUST contain serialized request."""
        from julee.shared.domain.use_cases.route_response import PipelineDispatch

        dispatch = PipelineDispatch(pipeline="NextPipeline", request={"data": "test"})
        assert dispatch.request == {"data": "test"}


# =============================================================================
# DOCTRINE: RouteResponseUseCase Behavior
# =============================================================================


class TestRouteResponseUseCaseBehavior:
    """Doctrine about RouteResponseUseCase execution behavior."""

    @pytest.fixture
    def mock_route_repository(self):
        """Create mock route repository."""
        from julee.shared.domain.models.route import Condition, Route

        class MockRouteRepository:
            def __init__(self, routes: list[Route]):
                self._routes = routes

            async def list_all(self) -> list[Route]:
                return self._routes

            async def list_for_response_type(self, response_type: str) -> list[Route]:
                return [r for r in self._routes if r.response_type == response_type]

        return MockRouteRepository

    @pytest.fixture
    def mock_request_transformer(self):
        """Create mock request transformer."""
        from julee.shared.domain.models.route import Route

        class MockRequestTransformer:
            def transform(self, route: Route, response: BaseModel) -> BaseModel:
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

        return MockRequestTransformer()

    @pytest.mark.asyncio
    async def test_execute_MUST_return_matching_dispatches(
        self, mock_route_repository, mock_request_transformer
    ):
        """execute() MUST return dispatches for all matching routes."""
        from julee.shared.domain.models.route import Condition, Route
        from julee.shared.domain.use_cases.route_response import (
            RouteResponseRequest,
            RouteResponseUseCase,
        )

        routes = [
            Route(
                response_type="MockResponse",
                condition=Condition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = RouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        request = RouteResponseRequest(
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
        from julee.shared.domain.models.route import Condition, Route
        from julee.shared.domain.use_cases.route_response import (
            RouteResponseRequest,
            RouteResponseUseCase,
        )

        routes = [
            Route(
                response_type="MockResponse",
                condition=Condition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
            Route(
                response_type="MockResponse",
                condition=Condition.is_true("needs_notification"),
                pipeline="NotificationPipeline",
                request_type="MockRequestB",
            ),
        ]

        use_case = RouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        # Both conditions are true
        request = RouteResponseRequest(
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
        from julee.shared.domain.models.route import Condition, Route
        from julee.shared.domain.use_cases.route_response import (
            RouteResponseRequest,
            RouteResponseUseCase,
        )

        routes = [
            Route(
                response_type="MockResponse",
                condition=Condition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = RouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        # Condition is false
        request = RouteResponseRequest(
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
        from julee.shared.domain.models.route import Condition, Route
        from julee.shared.domain.use_cases.route_response import (
            RouteResponseRequest,
            RouteResponseUseCase,
        )

        routes = [
            Route(
                response_type="MockResponse",
                condition=Condition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
            Route(
                response_type="OtherResponse",
                condition=Condition.is_true("has_new_data"),
                pipeline="OtherPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = RouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        request = RouteResponseRequest(
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
        from julee.shared.domain.models.route import Condition, Route
        from julee.shared.domain.use_cases.route_response import (
            RouteResponseRequest,
            RouteResponseUseCase,
        )

        routes = [
            Route(
                response_type="MockResponse",
                condition=Condition.is_true("has_new_data"),
                pipeline="ProcessingPipeline",
                request_type="MockRequestA",
            ),
        ]

        use_case = RouteResponseUseCase(
            route_repository=mock_route_repository(routes),
            request_transformer=mock_request_transformer,
        )

        request = RouteResponseRequest(
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
