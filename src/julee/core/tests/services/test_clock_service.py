"""Unit tests for ClockService implementations."""

from datetime import datetime, timezone


class TestSystemClockService:
    """Tests for SystemClockService."""

    def test_returns_utc_datetime(self):
        """now() returns UTC datetime."""
        from julee.core.services.clock import SystemClockService

        clock = SystemClockService()
        now = clock.now()

        assert isinstance(now, datetime)
        assert now.tzinfo == timezone.utc

    def test_returns_current_time(self):
        """now() returns approximately current time."""
        from julee.core.services.clock import SystemClockService

        clock = SystemClockService()
        before = datetime.now(timezone.utc)
        now = clock.now()
        after = datetime.now(timezone.utc)

        assert before <= now <= after


class TestFixedClockService:
    """Tests for FixedClockService."""

    def test_returns_provided_time(self):
        """now() returns the time provided at construction."""
        from julee.core.services.clock import FixedClockService

        fixed_time = datetime(2025, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        clock = FixedClockService(fixed_time)

        assert clock.now() == fixed_time

    def test_returns_same_time_repeatedly(self):
        """now() returns identical time on every call."""
        from julee.core.services.clock import FixedClockService

        fixed_time = datetime(2025, 3, 20, 9, 0, 0, tzinfo=timezone.utc)
        clock = FixedClockService(fixed_time)

        assert clock.now() == clock.now() == clock.now()

    def test_converts_naive_datetime_to_utc(self):
        """Naive datetime is converted to UTC."""
        from julee.core.services.clock import FixedClockService

        naive_time = datetime(2025, 1, 1, 12, 0, 0)
        clock = FixedClockService(naive_time)

        result = clock.now()
        assert result.tzinfo == timezone.utc
