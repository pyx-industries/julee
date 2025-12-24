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
    arg_type: str = ""  # e.g., "Accelerator" - inferred from method
    return_type: str = ""  # e.g., "None" - inferred from method


@dataclass
class UseCaseMetadata:
    """Metadata extracted from a use case class."""

    class_name: str
    entry_point_method: str = "execute"
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


def _is_repository_or_service(param_name: str, param_type: type | None) -> bool:
    """Check if a parameter is a Repository or Service protocol.

    Filters based on:
    - Type name ends with 'Repository' or 'Service'
    - Parameter name ends with '_repo' or '_service'

    Args:
        param_name: The parameter name
        param_type: The parameter type (may be None)

    Returns:
        True if this looks like a repository/service dependency
    """
    if param_type is None:
        return False

    type_name = getattr(param_type, "__name__", str(param_type))

    # Check type name
    if type_name.endswith("Repository") or type_name.endswith("Service"):
        return True

    # Check parameter name pattern
    if param_name.endswith("_repo") or param_name.endswith("_service"):
        # Only include if the type isn't a basic type like Callable
        if type_name not in ("Callable", "str", "int", "bool", "float", "None"):
            return True

    return False


def _get_dependencies(use_case_class: type) -> dict[str, type]:
    """Extract repository/service dependencies from __init__.

    Only includes parameters that look like Repository or Service protocols,
    filtering out utility functions, primitives, etc.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        Dict mapping parameter names to their Repository/Service types
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
        if _is_repository_or_service(param_name, param_type):
            deps[param_name] = param_type

    return deps


# Common entry point method names for use cases
_ENTRY_POINT_METHODS = ["execute", "assemble_data", "run", "process", "handle"]


def _find_entry_point_method(use_case_class: type) -> str | None:
    """Find the main entry point method for a use case.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        Method name if found, None otherwise
    """
    for method_name in _ENTRY_POINT_METHODS:
        if hasattr(use_case_class, method_name):
            method = getattr(use_case_class, method_name)
            # Make sure it's actually a method, not inherited from object
            if callable(method) and not method_name.startswith("_"):
                return method_name
    return None


def _get_execute_types(use_case_class: type) -> tuple[type | None, type | None]:
    """Extract Request and Response types from the entry point method.

    Tries common method names like execute, assemble_data, run, etc.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        Tuple of (request_type, response_type), either may be None
    """
    method_name = _find_entry_point_method(use_case_class)
    if method_name is None:
        return None, None

    method = getattr(use_case_class, method_name, None)
    if method is None:
        return None, None

    try:
        hints = get_type_hints(method)
    except Exception:
        return None, None

    # Try common parameter names for the request
    request_type = hints.get("request")
    if request_type is None:
        # Try first non-self parameter
        sig = inspect.signature(method)
        for param_name in sig.parameters:
            if param_name not in ("self", "cls"):
                request_type = hints.get(param_name)
                break

    response_type = hints.get("return")

    return request_type, response_type


def _extract_calls_from_source(source: str, seen: set) -> list[RepositoryCall]:
    """Extract repository calls from source code.

    Args:
        source: Python source code to analyze
        seen: Set of already-seen (repo_attr, method_name) tuples

    Returns:
        List of new RepositoryCall objects found
    """
    import textwrap

    # Dedent source to handle methods that are indented
    # Use textwrap.dedent which preserves relative indentation
    source = textwrap.dedent(source)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    calls = []

    for node in ast.walk(tree):
        # Look for Call or Await(Call) nodes
        call_node = node
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call_node = node.value
        elif not isinstance(node, ast.Call):
            continue

        if not isinstance(call_node, ast.Call):
            continue

        func = call_node.func

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


def _extract_repository_calls(use_case_class: type) -> list[RepositoryCall]:
    """Parse class methods AST to find self.repo.method() calls.

    Examines the entry point method and all private helper methods
    to find repository/service calls.

    Args:
        use_case_class: The use case class to analyze

    Returns:
        List of RepositoryCall objects representing dependency calls
    """
    calls = []
    seen = set()  # Avoid duplicates

    # Get the entry point method
    entry_method_name = _find_entry_point_method(use_case_class)
    if entry_method_name:
        method = getattr(use_case_class, entry_method_name, None)
        if method:
            try:
                source = inspect.getsource(method)
                calls.extend(_extract_calls_from_source(source, seen))
            except (OSError, TypeError):
                pass

    # Also scan private helper methods (they often contain the actual repo calls)
    for name in dir(use_case_class):
        if name.startswith("_") and not name.startswith("__"):
            method = getattr(use_case_class, name, None)
            if callable(method):
                try:
                    source = inspect.getsource(method)
                    calls.extend(_extract_calls_from_source(source, seen))
                except (OSError, TypeError):
                    pass

    return calls


def _get_entity_type_from_repo(dep_name: str, dep_type: type) -> str:
    """Infer the entity type from a repository type name.

    E.g., AcceleratorRepository -> Accelerator
    """
    type_name = getattr(dep_type, "__name__", "")
    if type_name.endswith("Repository"):
        return type_name[:-10]  # Remove "Repository"
    if type_name.endswith("Service"):
        return type_name[:-7]  # Remove "Service"
    return "Entity"


def _infer_method_types(method_name: str, entity_type: str) -> tuple[str, str]:
    """Infer argument and return types for common repository methods.

    Returns:
        (arg_type, return_type) tuple
    """
    # Common CRUD patterns
    method_patterns = {
        "save": (entity_type, "None"),
        "get": ("id: str", f"{entity_type} | None"),
        "get_many": ("ids: list[str]", f"dict[str, {entity_type}]"),
        "list_all": ("", f"list[{entity_type}]"),
        "delete": ("id: str", "bool"),
        "clear": ("", "None"),
        "generate_id": ("", "str"),
        # Service patterns
        "execute_query": ("config, query", "QueryResult"),
        "register_file": ("config, document", "RegistrationResult"),
    }

    if method_name in method_patterns:
        return method_patterns[method_name]

    # Generic fallback
    return ("", "")


def _enrich_calls_with_types(
    calls: list[RepositoryCall],
    dependencies: dict[str, type],
) -> list[RepositoryCall]:
    """Add type information to repository calls."""
    enriched = []
    for call in calls:
        dep_type = dependencies.get(call.repo_attr)
        if dep_type:
            entity_type = _get_entity_type_from_repo(call.repo_attr, dep_type)
            arg_type, return_type = _infer_method_types(call.method_name, entity_type)
            enriched.append(
                RepositoryCall(
                    repo_attr=call.repo_attr,
                    method_name=call.method_name,
                    arg_type=arg_type,
                    return_type=return_type,
                )
            )
        else:
            enriched.append(call)
    return enriched


def _ensure_all_deps_have_calls(
    calls: list[RepositoryCall],
    dependencies: dict[str, type],
) -> list[RepositoryCall]:
    """Ensure every dependency has at least one call.

    If a dependency has no calls, add a generic 'use' call.
    """
    deps_with_calls = {call.repo_attr for call in calls}
    result = list(calls)

    for dep_name, _dep_type in dependencies.items():
        if dep_name not in deps_with_calls:
            # Add a generic call for this dependency
            result.append(
                RepositoryCall(
                    repo_attr=dep_name,
                    method_name="...",  # Indicates potential use
                    arg_type="",
                    return_type="",
                )
            )

    return result


def introspect_use_case(use_case_class: type) -> UseCaseMetadata:
    """Extract metadata from a use case class via reflection + AST.

    Args:
        use_case_class: The use case class to introspect

    Returns:
        UseCaseMetadata with class info, dependencies, types, and calls
    """
    dependencies = _get_dependencies(use_case_class)
    entry_method = _find_entry_point_method(use_case_class) or "execute"
    request_type, response_type = _get_execute_types(use_case_class)
    all_calls = _extract_repository_calls(use_case_class)

    # Filter calls to only include those to known dependencies
    dep_names = set(dependencies.keys())
    filtered_calls = [call for call in all_calls if call.repo_attr in dep_names]

    # Enrich calls with type information
    enriched_calls = _enrich_calls_with_types(filtered_calls, dependencies)

    # Ensure all dependencies have at least one call
    repository_calls = _ensure_all_deps_have_calls(enriched_calls, dependencies)

    return UseCaseMetadata(
        class_name=use_case_class.__name__,
        entry_point_method=entry_method,
        dependencies=dependencies,
        request_type=request_type,
        response_type=response_type,
        repository_calls=repository_calls,
    )
