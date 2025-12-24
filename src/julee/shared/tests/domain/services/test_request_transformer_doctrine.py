"""PipelineRequestTransformer doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A PipelineRequestTransformer is a service protocol that transforms a Response
into a Request for a target pipeline, based on the PipelineRoute configuration.
This decouples Response and Request types from each other.

See: docs/architecture/proposals/pipeline_router_design.md
"""

import pytest
from pydantic import BaseModel


# =============================================================================
# DOCTRINE: PipelineRequestTransformer Protocol
# =============================================================================


class TestPipelineRequestTransformerDoctrine:
    """Doctrine about the PipelineRequestTransformer protocol."""

    def test_request_transformer_MUST_be_protocol(self):
        """PipelineRequestTransformer MUST be defined as a Protocol for structural typing."""
        from typing import Protocol

        from julee.shared.domain.services.pipeline_request_transformer import (
            PipelineRequestTransformer,
        )

        # Should be a Protocol (or at least have Protocol in its bases)
        assert hasattr(PipelineRequestTransformer, "__protocol_attrs__") or issubclass(
            PipelineRequestTransformer, Protocol
        )

    def test_request_transformer_MUST_have_transform_method(self):
        """PipelineRequestTransformer MUST have transform(route, response) method."""
        from julee.shared.domain.services.pipeline_request_transformer import (
            PipelineRequestTransformer,
        )
        import inspect

        assert hasattr(PipelineRequestTransformer, "transform")
        sig = inspect.signature(PipelineRequestTransformer.transform)
        params = list(sig.parameters.keys())
        # Should have route and response parameters (besides self)
        assert "route" in params
        assert "response" in params


# =============================================================================
# DOCTRINE: PipelineRequestTransformer Contract
# =============================================================================


class TestPipelineRequestTransformerContract:
    """Doctrine about PipelineRequestTransformer contract behavior.

    These tests use a mock implementation to verify the contract.
    Any implementation must satisfy these behaviors.
    """

    @pytest.fixture
    def sample_response_class(self):
        """Sample response class for testing."""

        class SampleResponse(BaseModel):
            content: bytes = b"test content"
            current_hash: str = "abc123"
            endpoint_id: str = "endpoint-1"

        return SampleResponse

    @pytest.fixture
    def sample_request_class(self):
        """Sample request class for testing."""

        class SampleRequest(BaseModel):
            data: bytes
            source_hash: str
            source_id: str

        return SampleRequest

    @pytest.fixture
    def mock_request_transformer(self, sample_request_class):
        """Create a minimal mock implementation for testing contract."""
        from julee.shared.domain.models.pipeline_route import PipelineRoute
        from julee.shared.domain.services.pipeline_request_transformer import (
            PipelineRequestTransformer,
        )

        SampleRequest = sample_request_class

        class MockPipelineRequestTransformer:
            """Mock implementation for contract testing."""

            def transform(
                self, route: PipelineRoute, response: BaseModel
            ) -> BaseModel:
                # Simple transformation based on route types
                if route.request_type == "SampleRequest":
                    return SampleRequest(
                        data=response.content,
                        source_hash=response.current_hash,
                        source_id=response.endpoint_id,
                    )
                raise ValueError(f"Unknown request type: {route.request_type}")

        return MockPipelineRequestTransformer()

    def test_transform_MUST_return_request_matching_route_type(
        self,
        mock_request_transformer,
        sample_response_class,
        sample_request_class,
    ):
        """transform() MUST return a request matching the route's request_type."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="SampleResponse",
            condition=PipelineCondition.is_true("has_data"),
            pipeline="NextPipeline",
            request_type="SampleRequest",
        )

        response = sample_response_class()
        request = mock_request_transformer.transform(route, response)

        assert isinstance(request, sample_request_class)

    def test_transform_MUST_map_response_fields_to_request_fields(
        self,
        mock_request_transformer,
        sample_response_class,
    ):
        """transform() MUST correctly map response fields to request fields."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="SampleResponse",
            condition=PipelineCondition.is_true("has_data"),
            pipeline="NextPipeline",
            request_type="SampleRequest",
        )

        response = sample_response_class(
            content=b"my content",
            current_hash="hash123",
            endpoint_id="ep-42",
        )

        request = mock_request_transformer.transform(route, response)

        assert request.data == b"my content"
        assert request.source_hash == "hash123"
        assert request.source_id == "ep-42"

    def test_transform_MUST_raise_for_unknown_type_pair(
        self,
        mock_request_transformer,
        sample_response_class,
    ):
        """transform() MUST raise error for unknown (response_type, request_type) pair."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="SampleResponse",
            condition=PipelineCondition.is_true("has_data"),
            pipeline="NextPipeline",
            request_type="UnknownRequest",  # Not registered
        )

        response = sample_response_class()

        with pytest.raises(ValueError, match="Unknown request type"):
            mock_request_transformer.transform(route, response)
