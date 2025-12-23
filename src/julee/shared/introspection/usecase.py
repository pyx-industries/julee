"""Use case introspection utilities.

Extracts metadata from use case classes via reflection and AST analysis
to support dynamic diagram generation.
"""

import ast
import importlib
import inspect
from dataclasses import dataclass, field
from typing import get_type_hints


@dataclass
class RepositoryCall:
    """Represents a method call on a repository/service dependency."""

    repo_attr: str  # e.g., "accelerator_repo"
    method_name: str  # e.g., "save"


@dataclass
class UseCaseMetadata:
    """Metadata extracted from a use case class."""

    class_name: str
    dependencies: dict[str, type] = field(default_factory=dict)
    request_type: type | None = None
    response_type: type | None = None
    repository_calls: list[RepositoryCall] = field(default_factory=list)


def resolve_use_case_class(module_class_path: str) -> type:
    """Resolve use case class from module:ClassName path.

    Args:
        module_class_path: Path in format "module.path:ClassName"

    Returns:
        The resolved class

    Raises:
        ValueError: If path format is invalid
        ImportError: If module cannot be imported
        AttributeError: If class not found in module
    """
    if ":" not in module_class_path:
        raise ValueError(
            f"Invalid path format: {module_class_path}. "
            "Expected 'module.path:ClassName'"
        )

    module_path, class_name = module_class_path.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _get_dependencies(use_case_class: type) -> dict[str, type]:
    """Extract repository/service dependencies from __init__.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        Dict mapping parameter names to their types
    """
    try:
        hints = get_type_hints(use_case_class.__init__)
    except Exception:
        hints = {}

    sig = inspect.signature(use_case_class.__init__)

    deps = {}
    for param_name in sig.parameters:
        if param_name == "self":
            continue
        param_type = hints.get(param_name)
        if param_type is not None:
            deps[param_name] = param_type

    return deps


def _get_execute_types(use_case_class: type) -> tuple[type | None, type | None]:
    """Extract Request and Response types from execute method.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        Tuple of (request_type, response_type), either may be None
    """
    execute_method = getattr(use_case_class, "execute", None)
    if execute_method is None:
        return None, None

    try:
        hints = get_type_hints(execute_method)
    except Exception:
        return None, None

    request_type = hints.get("request")
    response_type = hints.get("return")

    return request_type, response_type


def _extract_repository_calls(use_case_class: type) -> list[RepositoryCall]:
    """Parse execute method AST to find self.repo.method() calls.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        List of RepositoryCall objects representing dependency calls
    """
    execute_method = getattr(use_case_class, "execute", None)
    if execute_method is None:
        return []

    try:
        source = inspect.getsource(execute_method)
    except (OSError, TypeError):
        return []

    # Dedent source to handle methods that are indented
    source = inspect.cleandoc(source)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    calls = []
    seen = set()  # Avoid duplicates

    for node in ast.walk(tree):
        # Look for Call nodes
        if isinstance(node, ast.Call):
            func = node.func

            # Match pattern: self.{repo_attr}.{method}()
            if isinstance(func, ast.Attribute):
                method_name = func.attr

                if isinstance(func.value, ast.Attribute):
                    repo_attr = func.value.attr

                    if isinstance(func.value.value, ast.Name):
                        if func.value.value.id == "self":
                            key = (repo_attr, method_name)
                            if key not in seen:
                                seen.add(key)
                                calls.append(
                                    RepositoryCall(
                                        repo_attr=repo_attr,
                                        method_name=method_name,
                                    )
                                )

    return calls


def introspect_use_case(use_case_class: type) -> UseCaseMetadata:
    """Extract metadata from a use case class via reflection + AST.

    Args:
        use_case_class: The use case class to introspect

    Returns:
        UseCaseMetadata with class info, dependencies, types, and calls
    """
    dependencies = _get_dependencies(use_case_class)
    request_type, response_type = _get_execute_types(use_case_class)
    repository_calls = _extract_repository_calls(use_case_class)

    return UseCaseMetadata(
        class_name=use_case_class.__name__,
        dependencies=dependencies,
        request_type=request_type,
        response_type=response_type,
        repository_calls=repository_calls,
    )
