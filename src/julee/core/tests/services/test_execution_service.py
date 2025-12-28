"""Unit tests for ExecutionService implementations."""

import uuid


class TestDefaultExecutionService:
    """Tests for DefaultExecutionService."""

    def test_returns_string_id(self):
        """get_execution_id() returns a string."""
        from julee.core.services.execution import DefaultExecutionService

        service = DefaultExecutionService()
        execution_id = service.get_execution_id()

        assert isinstance(execution_id, str)
        assert len(execution_id) > 0

    def test_generates_valid_uuid(self):
        """Generates valid UUID when no ID provided."""
        from julee.core.services.execution import DefaultExecutionService

        service = DefaultExecutionService()
        execution_id = service.get_execution_id()

        parsed = uuid.UUID(execution_id)
        assert str(parsed) == execution_id

    def test_returns_same_id_repeatedly(self):
        """get_execution_id() returns same ID every call."""
        from julee.core.services.execution import DefaultExecutionService

        service = DefaultExecutionService()

        id1 = service.get_execution_id()
        id2 = service.get_execution_id()

        assert id1 == id2

    def test_uses_provided_id(self):
        """Uses provided ID instead of generating."""
        from julee.core.services.execution import DefaultExecutionService

        custom_id = "my-custom-execution-id"
        service = DefaultExecutionService(execution_id=custom_id)

        assert service.get_execution_id() == custom_id


class TestFixedExecutionService:
    """Tests for FixedExecutionService."""

    def test_returns_provided_id(self):
        """get_execution_id() returns the ID provided."""
        from julee.core.services.execution import FixedExecutionService

        fixed_id = "test-execution-123"
        service = FixedExecutionService(fixed_id)

        assert service.get_execution_id() == fixed_id

    def test_returns_same_id_repeatedly(self):
        """get_execution_id() returns identical ID every call."""
        from julee.core.services.execution import FixedExecutionService

        service = FixedExecutionService("deterministic-id")

        assert service.get_execution_id() == service.get_execution_id()
