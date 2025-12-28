"""Tests for TemporalClockService.

Note: Actually calling .now() requires a workflow context.
These tests verify structure and importability only.
"""


class TestTemporalClockService:
    """Tests for TemporalClockService."""

    def test_has_now_method(self):
        """TemporalClockService has now() method."""
        from julee.core.infrastructure.temporal.clock import TemporalClockService

        service = TemporalClockService()
        assert hasattr(service, "now")
        assert callable(service.now)

    def test_satisfies_clock_service_protocol(self):
        """TemporalClockService satisfies ClockService protocol structurally."""
        import inspect

        from julee.core.infrastructure.temporal.clock import TemporalClockService
        from julee.core.services.clock import ClockService

        # Check method signature matches protocol
        protocol_sig = inspect.signature(ClockService.now)
        impl_sig = inspect.signature(TemporalClockService.now)

        # Both should have only 'self' parameter
        assert list(protocol_sig.parameters.keys()) == ["self"]
        assert list(impl_sig.parameters.keys()) == ["self"]
