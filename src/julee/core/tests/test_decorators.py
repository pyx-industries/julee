"""Tests for core decorators."""

import logging
from typing import Protocol, runtime_checkable

import pytest
from pydantic import BaseModel

from julee.core.decorators import (
    UseCaseConfigurationError,
    UseCaseError,
    is_use_case,
    use_case,
)


# Test fixtures (not test classes - tell pytest to skip collection)
class TestRequest(BaseModel):
    __test__ = False
    value: str


class TestResponse(BaseModel):
    __test__ = False
    result: str


@runtime_checkable
class TestRepository(Protocol):
    async def get(self, id: str) -> str | None: ...


class ValidRepository:
    async def get(self, id: str) -> str | None:
        return f"got-{id}"


class InvalidRepository:
    """Does not implement TestRepository protocol."""

    def something_else(self) -> None:
        pass


# =============================================================================
# Basic decorator tests
# =============================================================================


class TestUseCaseDecorator:
    """Tests for @use_case decorator."""

    def test_decorator_marks_class_as_use_case(self):
        """Decorated class should be marked as use case."""

        @use_case
        class MyUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="ok")

        assert is_use_case(MyUseCase) is True

    def test_undecorated_class_not_marked(self):
        """Undecorated class should not be marked."""

        class NotAUseCase:
            pass

        assert is_use_case(NotAUseCase) is False

    def test_raises_if_no_execute_method(self):
        """Should raise if class has no execute method."""
        with pytest.raises(UseCaseConfigurationError, match="must have an execute"):

            @use_case
            class NoExecute:
                def __init__(self):
                    pass


# =============================================================================
# Protocol validation tests
# =============================================================================


class TestProtocolValidation:
    """Tests for Protocol validation in __init__."""

    def test_accepts_valid_protocol_implementation(self):
        """Should accept a valid Protocol implementation."""

        @use_case
        class MyUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="ok")

        # Should not raise
        uc = MyUseCase(ValidRepository())
        assert uc.repo is not None

    def test_rejects_invalid_protocol_implementation(self):
        """Should reject invalid Protocol implementation."""

        @use_case
        class MyUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="ok")

        with pytest.raises(
            UseCaseConfigurationError, match="does not implement TestRepository"
        ):
            MyUseCase(InvalidRepository())

    def test_validates_keyword_arguments(self):
        """Should validate Protocol in keyword arguments."""

        @use_case
        class MyUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="ok")

        with pytest.raises(UseCaseConfigurationError):
            MyUseCase(repo=InvalidRepository())

    def test_allows_non_protocol_parameters(self):
        """Should allow parameters without Protocol type hints."""

        @use_case
        class MyUseCase:
            def __init__(self, repo: TestRepository, name: str):
                self.repo = repo
                self.name = name

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result=self.name)

        uc = MyUseCase(ValidRepository(), "test")
        assert uc.name == "test"


# =============================================================================
# Logging tests
# =============================================================================


class TestLogging:
    """Tests for automatic logging."""

    @pytest.mark.asyncio
    async def test_logs_on_success(self, caplog):
        """Should log debug on entry and info on completion."""

        @use_case
        class LoggedUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="success")

        uc = LoggedUseCase(ValidRepository())

        with caplog.at_level(logging.DEBUG):
            result = await uc.execute(TestRequest(value="test"))

        assert result.result == "success"
        assert "Use case starting" in caplog.text
        assert "Use case completed" in caplog.text

        # Check extra fields in log records
        records = [r for r in caplog.records if "Use case" in r.message]
        assert len(records) >= 2
        assert any(getattr(r, "use_case", None) == "LoggedUseCase" for r in records)

    @pytest.mark.asyncio
    async def test_logs_on_failure(self, caplog):
        """Should log error on failure."""

        @use_case
        class FailingUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                raise ValueError("intentional failure")

        uc = FailingUseCase(ValidRepository())

        with caplog.at_level(logging.DEBUG):
            with pytest.raises(UseCaseError):
                await uc.execute(TestRequest(value="test"))

        assert "Use case failed" in caplog.text
        assert "intentional failure" in caplog.text


# =============================================================================
# Error wrapping tests
# =============================================================================


class TestErrorWrapping:
    """Tests for error wrapping in UseCaseError."""

    @pytest.mark.asyncio
    async def test_wraps_exception_in_use_case_error(self):
        """Should wrap exceptions in UseCaseError."""

        @use_case
        class FailingUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                raise ValueError("original error")

        uc = FailingUseCase(ValidRepository())

        with pytest.raises(UseCaseError) as exc_info:
            await uc.execute(TestRequest(value="test"))

        assert "FailingUseCase failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ValueError)

    @pytest.mark.asyncio
    async def test_does_not_double_wrap_use_case_error(self):
        """Should not double-wrap UseCaseError."""

        @use_case
        class RethrowingUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                raise UseCaseError("already wrapped")

        uc = RethrowingUseCase(ValidRepository())

        with pytest.raises(UseCaseError) as exc_info:
            await uc.execute(TestRequest(value="test"))

        assert str(exc_info.value) == "already wrapped"
        assert exc_info.value.__cause__ is None


# =============================================================================
# Sync execute tests
# =============================================================================


class TestSyncExecute:
    """Tests for sync execute() methods."""

    def test_works_with_sync_execute(self):
        """Should work with sync execute method."""

        @use_case
        class SyncUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="sync-result")

        uc = SyncUseCase(ValidRepository())
        result = uc.execute(TestRequest(value="test"))
        assert result.result == "sync-result"

    def test_sync_error_wrapping(self):
        """Should wrap sync exceptions in UseCaseError."""

        @use_case
        class SyncFailingUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            def execute(self, request: TestRequest) -> TestResponse:
                raise RuntimeError("sync failure")

        uc = SyncFailingUseCase(ValidRepository())

        with pytest.raises(UseCaseError) as exc_info:
            uc.execute(TestRequest(value="test"))

        assert isinstance(exc_info.value.__cause__, RuntimeError)


# =============================================================================
# Generic base class tests
# =============================================================================


class TestGenericBaseClass:
    """Tests for use with generic base classes (like generic_crud)."""

    def test_inherits_execute_from_base(self):
        """Should work with execute() inherited from base class."""

        class BaseUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="base")

        @use_case
        class DerivedUseCase(BaseUseCase):
            pass

        _uc = DerivedUseCase(ValidRepository())
        assert is_use_case(DerivedUseCase)

    @pytest.mark.asyncio
    async def test_overridden_execute_gets_wrapped(self):
        """Should wrap execute() when overridden in derived class."""

        class BaseUseCase:
            def __init__(self, repo: TestRepository):
                self.repo = repo

            async def execute(self, request: TestRequest) -> TestResponse:
                return TestResponse(result="base")

        @use_case
        class DerivedUseCase(BaseUseCase):
            async def execute(self, request: TestRequest) -> TestResponse:
                raise ValueError("derived error")

        uc = DerivedUseCase(ValidRepository())

        with pytest.raises(UseCaseError) as exc_info:
            await uc.execute(TestRequest(value="test"))

        assert "DerivedUseCase failed" in str(exc_info.value)


# =============================================================================
# Subclass inherits decorator tests
# =============================================================================


class TestSubclassInheritance:
    """Test that generic_crud subclasses inherit @use_case marker."""

    def test_subclass_of_generic_crud_inherits_marker(self):
        """Generic CRUD subclass inherits _is_use_case from decorated base.

        When subclassing GetUseCase (which has @use_case applied), the
        subclass automatically inherits the _is_use_case marker. This means
        subclasses don't need to apply @use_case again.
        """
        from julee.core.use_cases.generic_crud import GetUseCase

        # Create a subclass without applying decorator again
        class MyGetUseCase(GetUseCase):
            pass

        # The subclass should inherit the _is_use_case attribute from GetUseCase
        assert is_use_case(MyGetUseCase)
