"""Tests for TemporalExecutionService.

Note: Actually calling .get_execution_id() requires a workflow context.
These tests verify structure and importability only.
"""


class TestTemporalExecutionService:
    """Tests for TemporalExecutionService."""

    def test_has_get_execution_id_method(self):
        """TemporalExecutionService has get_execution_id() method."""
        from julee.core.infrastructure.temporal.execution import (
            TemporalExecutionService,
        )

        service = TemporalExecutionService()
        assert hasattr(service, "get_execution_id")
        assert callable(service.get_execution_id)

    def test_satisfies_execution_service_protocol(self):
        """TemporalExecutionService satisfies ExecutionService protocol structurally."""
        import inspect

        from julee.core.infrastructure.temporal.execution import (
            TemporalExecutionService,
        )
        from julee.core.services.execution import ExecutionService

        # Check method signature matches protocol
        protocol_sig = inspect.signature(ExecutionService.get_execution_id)
        impl_sig = inspect.signature(TemporalExecutionService.get_execution_id)

        # Both should have only 'self' parameter
        assert list(protocol_sig.parameters.keys()) == ["self"]
        assert list(impl_sig.parameters.keys()) == ["self"]
