"""Core decorators for use case doctrine enforcement.

This module provides the @use_case decorator that enforces architectural
contracts at runtime, reducing boilerplate while ensuring consistency.

Includes automatic parameter type validation for debugging serialization
issues when use cases are executed as Temporal pipelines.

For async use cases, automatically adds execute_sync() method for
synchronous callers (e.g., Sphinx, CLI).
"""

import asyncio
import inspect
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, Protocol, TypeVar, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel

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


class TypeValidationError(TypeError):
    """Raised when parameter type validation fails with detailed diagnostics."""


# =============================================================================
# Parameter Type Validation (for debugging Temporal serialization issues)
# =============================================================================


def _format_type(type_hint: Any) -> str:
    """Format a type hint for display in error messages."""
    if hasattr(type_hint, "__name__"):
        return str(type_hint.__name__)
    return str(type_hint)


def _format_value(value: Any, max_items: int = 5) -> str:
    """Format a value for display in error messages."""
    if isinstance(value, dict):
        if len(value) <= max_items:
            return str(value)
        items = list(value.items())[:max_items]
        return f"{dict(items)}... ({len(value)} total items)"
    elif isinstance(value, list | tuple):
        if len(value) <= max_items:
            return str(value)
        return f"{value[:max_items]}... ({len(value)} total items)"
    return repr(value)


def _validate_type(
    value: Any,
    expected_type: Any,
    context_name: str = "value",
    allow_none: bool = False,
) -> None:
    """Validate that a value matches the expected type with detailed diagnostics."""
    if value is None:
        if allow_none:
            return
        raise TypeValidationError(
            f"{context_name}: Expected {_format_type(expected_type)}, got None"
        )

    origin_type = get_origin(expected_type)
    type_args = get_args(expected_type)

    if origin_type is None:
        _validate_simple_type(value, expected_type, context_name)
    else:
        _validate_generic_type(
            value, expected_type, origin_type, type_args, context_name
        )


def _validate_simple_type(value: Any, expected_type: Any, context_name: str) -> None:
    """Validate simple (non-generic) types."""
    if isinstance(value, expected_type):
        return

    # Special handling for Pydantic models vs dicts (serialization issue)
    if inspect.isclass(expected_type) and issubclass(expected_type, BaseModel):
        if isinstance(value, dict):
            _raise_pydantic_dict_error(value, expected_type, context_name)
        # Accept any BaseModel when expected_type is a BaseModel subclass.
        # This supports generic CRUD where base class declares `request: CreateRequest`
        # but subclass passes `CreateSoftwareSystemRequest`. Pydantic validates fields.
        if isinstance(value, BaseModel):
            return

    raise TypeValidationError(
        f"{context_name}: Type mismatch\n"
        f"  Expected: {_format_type(expected_type)}\n"
        f"  Actual: {type(value).__name__}\n"
        f"  Value: {_format_value(value)}"
    )


def _validate_generic_type(
    value: Any,
    expected_type: Any,
    origin_type: Any,
    type_args: tuple,
    context_name: str,
) -> None:
    """Validate generic types like List[X], Dict[K,V], etc."""
    if not isinstance(value, origin_type):
        raise TypeValidationError(
            f"{context_name}: Container type mismatch\n"
            f"  Expected: {origin_type.__name__}\n"
            f"  Actual: {type(value).__name__}"
        )

    if origin_type is list and type_args:
        for i, element in enumerate(value):
            _validate_type(element, type_args[0], f"{context_name}[{i}]")
    elif origin_type is dict and len(type_args) >= 2:
        for key, val in value.items():
            _validate_type(key, type_args[0], f"{context_name} key '{key}'")
            _validate_type(val, type_args[1], f"{context_name}['{key}']")
    elif origin_type is Union:
        for union_type in type_args:
            try:
                _validate_type(
                    value, union_type, context_name, allow_none=union_type is type(None)
                )
                return
            except TypeValidationError:
                continue
        raise TypeValidationError(
            f"{context_name}: Value doesn't match any type in Union"
        )


def _raise_pydantic_dict_error(
    value: dict, expected_type: type, context_name: str
) -> None:
    """Raise a detailed error for Pydantic model vs dict serialization issues."""
    model_fields = []
    if hasattr(expected_type, "model_fields"):
        model_fields = list(expected_type.model_fields.keys())

    raise TypeValidationError(
        f"SERIALIZATION ISSUE: {context_name} is dict instead of {expected_type.__name__}!\n"
        f"  Expected: {expected_type.__name__}\n"
        f"  Dict keys: {list(value.keys())}\n"
        f"  Model fields: {model_fields}\n"
        f"  This indicates Temporal deserialized a Pydantic model as a plain dict."
    )


def _validate_execute_request(
    use_case_name: str,
    execute_method: Callable,
    request: Any,
    logger: logging.Logger,
) -> None:
    """Validate the request parameter type for execute()."""
    try:
        type_hints = get_type_hints(execute_method)
    except Exception:
        return  # Can't get hints, skip validation

    if "request" not in type_hints:
        return

    expected_type = type_hints["request"]

    # Handle Optional[X] - extract the non-None type
    origin = get_origin(expected_type)
    if origin is Union:
        args = get_args(expected_type)
        non_none_types = [t for t in args if t is not type(None)]
        if len(non_none_types) == 1:
            expected_type = non_none_types[0]
            if request is None:
                return  # None is valid for Optional

    try:
        _validate_type(request, expected_type, f"{use_case_name}.execute(request)")
    except TypeValidationError as e:
        logger.error(
            "Request parameter type validation failed",
            extra={"use_case": use_case_name, "error": str(e)},
        )
        raise


# =============================================================================
# Protocol Validation
# =============================================================================


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
    """Wrap execute() with logging, parameter validation, and error handling.

    Handles both sync and async execute methods transparently.
    Validates request parameter types to catch Temporal serialization issues.
    """
    is_async = inspect.iscoroutinefunction(original_execute)

    if is_async:

        @wraps(original_execute)
        async def async_execute(self: Any, request: Any) -> Any:
            logger = logging.getLogger(use_case_class.__module__)
            use_case_name = use_case_class.__name__

            # Validate request parameter type (catches Temporal serialization issues)
            _validate_execute_request(use_case_name, original_execute, request, logger)

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

            # Validate request parameter type (catches Temporal serialization issues)
            _validate_execute_request(use_case_name, original_execute, request, logger)

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
    - execute_sync() method for async use cases (synchronous callers)

    Usage:
        @use_case
        class GetStoryUseCase:
            def __init__(self, story_repo: StoryRepository):
                self.story_repo = story_repo

            async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
                story = await self.story_repo.get(request.slug)
                return GetStoryResponse(entity=story)

        # Async caller:
        response = await use_case.execute(request)

        # Sync caller (Sphinx, CLI):
        response = use_case.execute_sync(request)

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

    Sync Support:
        For async use cases, execute_sync() is automatically added. This
        method wraps asyncio.run(self.execute(request)) for synchronous
        callers like Sphinx directives or CLI commands.

    Note:
        Works with both sync and async execute() methods.
        Works with generic CRUD base classes that define execute().
    """
    # Validate that execute() exists (may be inherited from base class)
    if not hasattr(cls, "execute"):
        raise UseCaseConfigurationError(f"{cls.__name__} must have an execute() method")

    execute_method = cls.execute
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
        cls.execute = wrapped_execute

    # Add execute_sync() for async use cases to support synchronous callers
    if inspect.iscoroutinefunction(execute_method):

        def execute_sync(self: Any, request: Any) -> Any:
            """Execute use case synchronously.

            Convenience method for synchronous callers (Sphinx, CLI).
            Wraps asyncio.run(self.execute(request)).
            """
            return asyncio.run(self.execute(request))

        # Set proper metadata so sphinx_autodoc_typehints doesn't see this as a local function
        execute_sync.__module__ = cls.__module__
        execute_sync.__qualname__ = f"{cls.__qualname__}.execute_sync"
        cls.execute_sync = execute_sync  # type: ignore[attr-defined]

    # Mark the class as a use case for doctrine verification
    cls._is_use_case = True  # type: ignore[attr-defined]

    return cls


def is_use_case(cls: type) -> bool:
    """Check if a class is decorated with @use_case.

    Used by doctrine tests to verify all use cases are properly decorated.
    """
    return getattr(cls, "_is_use_case", False)


# =============================================================================
# Semantic Relation Decorator
# =============================================================================


def _resolve_type_reference(type_ref: "type | str | Callable[[], type]") -> type:
    """Resolve a type reference to an actual type.

    Handles:
    - Direct type references (pass through)
    - String references like "julee.hcd.entities.story.Story"
    - Callable type providers (legacy support)
    """
    if isinstance(type_ref, type):
        return type_ref

    if isinstance(type_ref, str):
        # String reference: "module.path.ClassName"
        parts = type_ref.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid type reference: {type_ref}. Expected 'module.ClassName'")
        module_path, class_name = parts
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    if callable(type_ref):
        # Legacy callable support
        return type_ref()

    raise TypeError(f"Invalid type reference: {type_ref}")


def semantic_relation(
    target_type: "type | str | Callable[[], type]",
    relation: "RelationType",
) -> Callable[[type], type]:
    """Declare a semantic relationship from the decorated class to target_type.

    Used to explicitly declare how entities relate across bounded contexts
    and framework layers. The relationship is stored as a SemanticRelation
    entity on the decorated class.

    Args:
        target_type: The entity type to relate to. Can be:
                     - A type directly (if no circular import)
                     - A string like "julee.hcd.entities.story.Story"
                     - A callable returning the type (legacy)
        relation: The type of relationship (from RelationType enum)

    Returns:
        Decorator that adds the semantic relation to the class

    Example:
        from julee.core.decorators import semantic_relation
        from julee.core.entities.semantic_relation import RelationType

        # Direct type reference (when no circular import):
        @semantic_relation(Persona, RelationType.IS_A)
        class CustomerSegment(BaseModel):
            slug: str

        # String reference (for circular imports):
        @semantic_relation("julee.hcd.entities.app.App", RelationType.PART_OF)
        @semantic_relation("julee.hcd.entities.persona.Persona", RelationType.REFERENCES)
        class Story(BaseModel):
            slug: str

    The decorated class will have a __semantic_relations__ attribute
    containing a list of SemanticRelation entities.
    """
    # Import here to avoid circular dependency
    from julee.core.entities.semantic_relation import RelationType, SemanticRelation

    def decorator(cls: type) -> type:
        if not hasattr(cls, "__semantic_relations__"):
            cls.__semantic_relations__ = []  # type: ignore[attr-defined]

        resolved_type = _resolve_type_reference(target_type)

        cls.__semantic_relations__.append(  # type: ignore[attr-defined]
            SemanticRelation(
                source_type=cls,
                target_type=resolved_type,
                relation_type=relation,
            )
        )
        return cls

    return decorator


def get_semantic_relations(cls: type) -> list:
    """Get semantic relations declared on a class.

    Args:
        cls: The class to inspect

    Returns:
        List of SemanticRelation entities declared on the class,
        or empty list if none declared.
    """
    return getattr(cls, "__semantic_relations__", [])
