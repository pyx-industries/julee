"""RouteRepository doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A RouteRepository is a protocol for accessing Route entities. It provides
the abstraction for route persistence, allowing different implementations
(in-memory, file-based, database-backed).

See: docs/architecture/proposals/pipeline_router_design.md
"""

import pytest
from pydantic import BaseModel


# =============================================================================
# DOCTRINE: RouteRepository Protocol
# =============================================================================


class TestRouteRepositoryDoctrine:
    """Doctrine about the RouteRepository protocol."""

    def test_route_repository_MUST_be_protocol(self):
        """RouteRepository MUST be defined as a Protocol for structural typing."""
        from typing import Protocol, runtime_checkable

        from julee.shared.domain.repositories.route import RouteRepository

        # Should be a Protocol (or at least have Protocol in its bases)
        assert hasattr(RouteRepository, "__protocol_attrs__") or issubclass(
            RouteRepository, Protocol
        )

    def test_route_repository_MUST_have_list_all_method(self):
        """RouteRepository MUST have list_all() method returning all routes."""
        from julee.shared.domain.repositories.route import RouteRepository
        import inspect

        assert hasattr(RouteRepository, "list_all")
        sig = inspect.signature(RouteRepository.list_all)
        # Should be async (returns coroutine)
        assert inspect.iscoroutinefunction(RouteRepository.list_all) or "async" in str(
            sig
        )

    def test_route_repository_MUST_have_list_for_response_type_method(self):
        """RouteRepository MUST have list_for_response_type() for filtered queries."""
        from julee.shared.domain.repositories.route import RouteRepository
        import inspect

        assert hasattr(RouteRepository, "list_for_response_type")
        sig = inspect.signature(RouteRepository.list_for_response_type)
        params = list(sig.parameters.keys())
        # Should have response_type parameter (besides self)
        assert "response_type" in params


# =============================================================================
# DOCTRINE: RouteRepository Contract
# =============================================================================


class TestRouteRepositoryContract:
    """Doctrine about RouteRepository contract behavior.

    These tests use a mock implementation to verify the contract.
    Any implementation must satisfy these behaviors.
    """

    @pytest.fixture
    def mock_route_repository(self):
        """Create a minimal mock implementation for testing contract."""
        from julee.shared.domain.models.route import Condition, Route
        from julee.shared.domain.repositories.route import RouteRepository

        class MockRouteRepository:
            """Mock implementation for contract testing."""

            def __init__(self, routes: list[Route]):
                self._routes = routes

            async def list_all(self) -> list[Route]:
                return self._routes

            async def list_for_response_type(self, response_type: str) -> list[Route]:
                return [r for r in self._routes if r.response_type == response_type]

        return MockRouteRepository

    @pytest.mark.asyncio
    async def test_list_all_MUST_return_all_routes(self, mock_route_repository):
        """list_all() MUST return all configured routes."""
        from julee.shared.domain.models.route import Condition, Route

        routes = [
            Route(
                response_type="ResponseA",
                condition=Condition.is_true("field_a"),
                pipeline="PipelineA",
                request_type="RequestA",
            ),
            Route(
                response_type="ResponseB",
                condition=Condition.is_true("field_b"),
                pipeline="PipelineB",
                request_type="RequestB",
            ),
        ]

        repo = mock_route_repository(routes)
        result = await repo.list_all()

        assert len(result) == 2
        assert result[0].response_type == "ResponseA"
        assert result[1].response_type == "ResponseB"

    @pytest.mark.asyncio
    async def test_list_for_response_type_MUST_filter_by_type(
        self, mock_route_repository
    ):
        """list_for_response_type() MUST return only routes for the specified type."""
        from julee.shared.domain.models.route import Condition, Route

        routes = [
            Route(
                response_type="ResponseA",
                condition=Condition.is_true("field_a"),
                pipeline="PipelineA",
                request_type="RequestA",
            ),
            Route(
                response_type="ResponseA",
                condition=Condition.is_not_none("error"),
                pipeline="ErrorPipeline",
                request_type="ErrorRequest",
            ),
            Route(
                response_type="ResponseB",
                condition=Condition.is_true("field_b"),
                pipeline="PipelineB",
                request_type="RequestB",
            ),
        ]

        repo = mock_route_repository(routes)
        result = await repo.list_for_response_type("ResponseA")

        assert len(result) == 2
        assert all(r.response_type == "ResponseA" for r in result)

    @pytest.mark.asyncio
    async def test_list_for_response_type_MUST_return_empty_for_unknown_type(
        self, mock_route_repository
    ):
        """list_for_response_type() MUST return empty list for unknown response type."""
        from julee.shared.domain.models.route import Condition, Route

        routes = [
            Route(
                response_type="ResponseA",
                condition=Condition.is_true("field_a"),
                pipeline="PipelineA",
                request_type="RequestA",
            ),
        ]

        repo = mock_route_repository(routes)
        result = await repo.list_for_response_type("UnknownResponse")

        assert result == []
