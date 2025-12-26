"""Core decorators for use case doctrine enforcement.

This module provides the @use_case decorator that enforces architectural
contracts at runtime, reducing boilerplate while ensuring consistency.
"""

import inspect
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, Protocol, TypeVar, get_args, get_origin, get_type_hints

T = TypeVar("T")


class UseCaseError(Exception):
    """Base error for use case failures.

    All errors from use case execution are wrapped in this type,
    providing a consistent error boundary at the application layer.
    """


class UseCaseConfigurationError(UseCaseError):
    """Raised when a use case is misconfigured.

    This indicates a programming error, not a runtime failure:
    - Missing execute() method
    - Invalid Protocol implementation passed to __init__
    """


def _is_protocol_type(type_hint: Any) -> bool:
    """Check if a type hint is a Protocol class.

    Works with @runtime_checkable protocols to enable isinstance() checks.
    """
    if type_hint is None:
        return False

    # Handle Optional[X] and Union types - extract the non-None type
    origin = get_origin(type_hint)
    if origin is not None:
        return False  # We only validate direct Protocol types, not generics

    # Check for Protocol metaclass
    try:
        return (
            inspect.isclass(type_hint)
            and issubclass(type_hint, Protocol)
            and type_hint is not Protocol
        )
    except TypeError:
        return False


def _validate_protocol_dependencies(
    use_case_class: type,
    init_method: Callable,
    args: tuple,
    kwargs: dict[str, Any],
) -> None:
    """Validate that Protocol-typed constructor args satisfy their protocols.

    Uses @runtime_checkable Protocols and isinstance() for validation.
    """
    try:
        type_hints = get_type_hints(init_method)
    except Exception:
        # If we can't get type hints, skip validation
        return

    sig = inspect.signature(init_method)
    param_names = list(sig.parameters.keys())

    # Skip 'self' parameter
    if param_names and param_names[0] == "self":
        param_names = param_names[1:]

    # Validate positional args
    for i, value in enumerate(args):
        if i >= len(param_names):
            break
        param_name = param_names[i]
        if param_name in type_hints:
            expected_type = type_hints[param_name]
            if _is_protocol_type(expected_type):
                if not isinstance(value, expected_type):
                    raise UseCaseConfigurationError(
                        f"{use_case_class.__name__}: {param_name} does not "
                        f"implement {expected_type.__name__} protocol"
                    )

    # Validate keyword args
    for param_name, value in kwargs.items():
        if param_name in type_hints:
            expected_type = type_hints[param_name]
            if _is_protocol_type(expected_type):
                if not isinstance(value, expected_type):
                    raise UseCaseConfigurationError(
                        f"{use_case_class.__name__}: {param_name} does not "
                        f"implement {expected_type.__name__} protocol"
                    )


def _wrap_execute_method(
    use_case_class: type,
    original_execute: Callable,
) -> Callable:
    """Wrap execute() with logging and error handling.

    Handles both sync and async execute methods transparently.
    """
    is_async = inspect.iscoroutinefunction(original_execute)

    if is_async:

        @wraps(original_execute)
        async def async_execute(self: Any, request: Any) -> Any:
            logger = logging.getLogger(use_case_class.__module__)
            use_case_name = use_case_class.__name__

            logger.debug(
                "Use case starting",
                extra={
                    "use_case": use_case_name,
                    "request_type": type(request).__name__,
                },
            )

            start_time = time.perf_counter()

            try:
                result = await original_execute(self, request)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                logger.info(
                    "Use case completed",
                    extra={
                        "use_case": use_case_name,
                        "duration_ms": duration_ms,
                    },
                )

                return result

            except UseCaseError:
                # Already wrapped, just re-raise
                raise
            except Exception as e:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(
                    "Use case failed",
                    extra={
                        "use_case": use_case_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": duration_ms,
                    },
                    exc_info=True,
                )
                raise UseCaseError(f"{use_case_name} failed: {e}") from e

        return async_execute
    else:

        @wraps(original_execute)
        def sync_execute(self: Any, request: Any) -> Any:
            logger = logging.getLogger(use_case_class.__module__)
            use_case_name = use_case_class.__name__

            logger.debug(
                "Use case starting",
                extra={
                    "use_case": use_case_name,
                    "request_type": type(request).__name__,
                },
            )

            start_time = time.perf_counter()

            try:
                result = original_execute(self, request)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                logger.info(
                    "Use case completed",
                    extra={
                        "use_case": use_case_name,
                        "duration_ms": duration_ms,
                    },
                )

                return result

            except UseCaseError:
                raise
            except Exception as e:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(
                    "Use case failed",
                    extra={
                        "use_case": use_case_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": duration_ms,
                    },
                    exc_info=True,
                )
                raise UseCaseError(f"{use_case_name} failed: {e}") from e

        return sync_execute


def use_case(cls: type[T]) -> type[T]:
    """Decorator that enforces use case doctrine.

    Automatically provides:
    - Protocol validation for constructor dependencies at instantiation time
    - Entry/exit logging with execution duration
    - Error wrapping in UseCaseError for consistent error boundaries

    Usage:
        @use_case
        class GetStoryUseCase:
            def __init__(self, story_repo: StoryRepository):
                self.story_repo = story_repo

            async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
                story = await self.story_repo.get(request.slug)
                return GetStoryResponse(entity=story)

    Validation:
        All Protocol-typed parameters in __init__ are validated at construction
        time using isinstance() with @runtime_checkable protocols. This catches
        misconfiguration early:

            # This raises UseCaseConfigurationError immediately:
            use_case = GetStoryUseCase(not_a_repository)

    Logging:
        Every execute() call is automatically logged:
        - DEBUG on entry with use case name and request type
        - INFO on success with duration
        - ERROR on failure with error details and stack trace

    Error Handling:
        All exceptions from execute() are wrapped in UseCaseError, providing
        a consistent error boundary. The original exception is preserved as
        __cause__ for debugging.

    Note:
        Works with both sync and async execute() methods.
        Works with generic CRUD base classes that define execute().
    """
    # Validate that execute() exists (may be inherited from base class)
    if not hasattr(cls, "execute"):
        raise UseCaseConfigurationError(f"{cls.__name__} must have an execute() method")

    execute_method = getattr(cls, "execute")
    if not callable(execute_method):
        raise UseCaseConfigurationError(f"{cls.__name__}.execute must be callable")

    # Wrap __init__ to validate Protocol dependencies
    original_init = cls.__init__

    @wraps(original_init)
    def validated_init(self: Any, *args: Any, **kwargs: Any) -> None:
        # Validate Protocol-typed parameters before calling original __init__
        _validate_protocol_dependencies(cls, original_init, args, kwargs)
        original_init(self, *args, **kwargs)

    cls.__init__ = validated_init  # type: ignore[method-assign]

    # Wrap execute() for logging and error handling
    # Only wrap if execute is defined on this class (not inherited and already wrapped)
    if "execute" in cls.__dict__:
        wrapped_execute = _wrap_execute_method(cls, execute_method)
        setattr(cls, "execute", wrapped_execute)

    # Mark the class as a use case for doctrine verification
    cls._is_use_case = True  # type: ignore[attr-defined]

    return cls


def is_use_case(cls: type) -> bool:
    """Check if a class is decorated with @use_case.

    Used by doctrine tests to verify all use cases are properly decorated.
    """
    return getattr(cls, "_is_use_case", False)
