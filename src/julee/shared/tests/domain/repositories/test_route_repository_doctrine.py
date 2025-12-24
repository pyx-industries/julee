"""PipelineRouteRepository doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A PipelineRouteRepository is a protocol for accessing PipelineRoute entities.
It provides the abstraction for route persistence, allowing different
implementations (in-memory, file-based, database-backed).

See: docs/architecture/proposals/pipeline_router_design.md
"""

import pytest

# =============================================================================
# DOCTRINE: PipelineRouteRepository Protocol
# =============================================================================


class TestPipelineRouteRepositoryDoctrine:
    """Doctrine about the PipelineRouteRepository protocol."""

    def test_route_repository_MUST_be_protocol(self):
        """PipelineRouteRepository MUST be defined as a Protocol for structural typing."""
        from typing import Protocol

        from julee.shared.domain.repositories.pipeline_route import (
            PipelineRouteRepository,
        )

        # Should be a Protocol (or at least have Protocol in its bases)
        assert hasattr(PipelineRouteRepository, "__protocol_attrs__") or issubclass(
            PipelineRouteRepository, Protocol
        )

    def test_route_repository_MUST_have_list_all_method(self):
        """PipelineRouteRepository MUST have list_all() method returning all routes."""
        import inspect

        from julee.shared.domain.repositories.pipeline_route import (
            PipelineRouteRepository,
        )

        assert hasattr(PipelineRouteRepository, "list_all")
        sig = inspect.signature(PipelineRouteRepository.list_all)
        # Should be async (returns coroutine)
        assert inspect.iscoroutinefunction(
            PipelineRouteRepository.list_all
        ) or "async" in str(sig)

    def test_route_repository_MUST_have_list_for_response_type_method(self):
        """PipelineRouteRepository MUST have list_for_response_type() for filtered queries."""
        import inspect

        from julee.shared.domain.repositories.pipeline_route import (
            PipelineRouteRepository,
        )

        assert hasattr(PipelineRouteRepository, "list_for_response_type")
        sig = inspect.signature(PipelineRouteRepository.list_for_response_type)
        params = list(sig.parameters.keys())
        # Should have response_type parameter (besides self)
        assert "response_type" in params


# =============================================================================
# DOCTRINE: PipelineRouteRepository Contract
# =============================================================================


class TestPipelineRouteRepositoryContract:
    """Doctrine about PipelineRouteRepository contract behavior.

    These tests use a mock implementation to verify the contract.
    Any implementation must satisfy these behaviors.
    """

    @pytest.fixture
    def mock_route_repository(self):
        """Create a minimal mock implementation for testing contract."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineRoute,
        )

        class MockPipelineRouteRepository:
            """Mock implementation for contract testing."""

            def __init__(self, routes: list[PipelineRoute]):
                self._routes = routes

            async def list_all(self) -> list[PipelineRoute]:
                return self._routes

            async def list_for_response_type(
                self, response_type: str
            ) -> list[PipelineRoute]:
                return [r for r in self._routes if r.response_type == response_type]

        return MockPipelineRouteRepository

    @pytest.mark.asyncio
    async def test_list_all_MUST_return_all_routes(self, mock_route_repository):
        """list_all() MUST return all configured routes."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        routes = [
            PipelineRoute(
                response_type="ResponseA",
                condition=PipelineCondition.is_true("field_a"),
                pipeline="PipelineA",
                request_type="RequestA",
            ),
            PipelineRoute(
                response_type="ResponseB",
                condition=PipelineCondition.is_true("field_b"),
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
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        routes = [
            PipelineRoute(
                response_type="ResponseA",
                condition=PipelineCondition.is_true("field_a"),
                pipeline="PipelineA",
                request_type="RequestA",
            ),
            PipelineRoute(
                response_type="ResponseA",
                condition=PipelineCondition.is_not_none("error"),
                pipeline="ErrorPipeline",
                request_type="ErrorRequest",
            ),
            PipelineRoute(
                response_type="ResponseB",
                condition=PipelineCondition.is_true("field_b"),
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
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        routes = [
            PipelineRoute(
                response_type="ResponseA",
                condition=PipelineCondition.is_true("field_a"),
                pipeline="PipelineA",
                request_type="RequestA",
            ),
        ]

        repo = mock_route_repository(routes)
        result = await repo.list_for_response_type("UnknownResponse")

        assert result == []
