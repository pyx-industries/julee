"""Catalog introspection utilities for reflexive documentation.

Provides functions to discover and describe entities, use cases, and repositories
within modules for auto-generated documentation catalogs.
"""

import importlib
import importlib.util
import inspect
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


@dataclass
class EntityMetadata:
    """Metadata extracted from an entity class."""

    class_name: str
    module_path: str
    full_path: str
    summary: str  # First line of docstring
    docstring: str | None
    field_names: list[str] = field(default_factory=list)
    field_count: int = 0


@dataclass
class RepositoryMetadata:
    """Metadata extracted from a repository protocol."""

    class_name: str
    module_path: str
    full_path: str
    summary: str
    docstring: str | None
    method_names: list[str] = field(default_factory=list)
    entity_type: str | None = None  # Inferred from name


@dataclass
class UseCaseCatalogEntry:
    """Simplified use case metadata for catalog listings."""

    class_name: str
    module_path: str
    full_path: str
    summary: str
    docstring: str | None
    crud_type: str | None = None  # Create, Read, Update, Delete, or None


def _get_first_line(docstring: str | None) -> str:
    """Extract first line of docstring as summary."""
    if not docstring:
        return "(no description)"
    lines = docstring.strip().split("\n")
    return lines[0].strip() if lines else "(no description)"


def _classify_crud_type(class_name: str) -> str | None:
    """Classify use case by CRUD type based on naming conventions.

    Args:
        class_name: The use case class name

    Returns:
        'Create', 'Read', 'Update', 'Delete', or None
    """
    name_lower = class_name.lower()

    # Create patterns
    if any(p in name_lower for p in ["create", "add", "register", "new"]):
        return "Create"

    # Read patterns
    if any(p in name_lower for p in ["get", "list", "find", "fetch", "query", "search"]):
        return "Read"

    # Update patterns
    if any(p in name_lower for p in ["update", "modify", "edit", "change", "set"]):
        return "Update"

    # Delete patterns
    if any(p in name_lower for p in ["delete", "remove", "clear", "purge"]):
        return "Delete"

    return None


def _infer_entity_type(class_name: str) -> str | None:
    """Infer entity type from repository class name.

    E.g., AcceleratorRepository -> Accelerator
    """
    if class_name.endswith("Repository"):
        return class_name[:-10]
    return None


def _is_pydantic_model(cls: type) -> bool:
    """Check if a class is a Pydantic BaseModel subclass."""
    try:
        return isinstance(cls, type) and issubclass(cls, BaseModel) and cls is not BaseModel
    except TypeError:
        return False


def _is_protocol(cls: type) -> bool:
    """Check if a class is a Protocol."""
    # Check for typing.Protocol or runtime_checkable Protocol
    if hasattr(cls, "_is_protocol"):
        return cls._is_protocol
    # Also check by inspecting __bases__
    try:
        return Protocol in getattr(cls, "__mro__", ())
    except TypeError:
        return False


def _is_repository_protocol(cls: type) -> bool:
    """Check if a class looks like a Repository protocol."""
    class_name = getattr(cls, "__name__", "")
    return (
        class_name.endswith("Repository")
        and (_is_protocol(cls) or "ABC" in str(type(cls).__mro__))
    )


def _get_module_classes(module: ModuleType) -> list[tuple[str, type]]:
    """Get all classes defined in a module (not imported).

    Args:
        module: The module to inspect

    Returns:
        List of (name, class) tuples for classes defined in this module
    """
    classes = []
    module_name = module.__name__

    for name in dir(module):
        if name.startswith("_"):
            continue

        obj = getattr(module, name)
        if not isinstance(obj, type):
            continue

        # Only include classes defined in this module
        obj_module = getattr(obj, "__module__", None)
        if obj_module == module_name:
            classes.append((name, obj))

    return classes


def _iter_submodules(package: ModuleType) -> list[ModuleType]:
    """Iterate over all submodules of a package.

    Args:
        package: The package to scan

    Returns:
        List of imported submodules
    """
    submodules = []

    # Check if it's a package (has __path__)
    if not hasattr(package, "__path__"):
        return [package]

    package_path = package.__path__
    package_name = package.__name__

    for importer, modname, ispkg in pkgutil.iter_modules(package_path):
        full_name = f"{package_name}.{modname}"
        try:
            submod = importlib.import_module(full_name)
            submodules.append(submod)
        except ImportError:
            continue

    return submodules


def introspect_entities(
    module: ModuleType | str,
    recursive: bool = True,
) -> list[EntityMetadata]:
    """Find all Pydantic models in a module.

    Args:
        module: Module object or import path string
        recursive: If True, also scan submodules of a package

    Returns:
        List of EntityMetadata for each Pydantic model found
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    entities = []

    # Get modules to scan
    if recursive:
        modules_to_scan = _iter_submodules(module)
        # Also include the package itself
        modules_to_scan.insert(0, module)
    else:
        modules_to_scan = [module]

    for mod in modules_to_scan:
        module_name = mod.__name__

        for name, cls in _get_module_classes(mod):
            if not _is_pydantic_model(cls):
                continue

            docstring = cls.__doc__
            summary = _get_first_line(docstring)

            # Get field names from Pydantic model_fields
            field_names = []
            if hasattr(cls, "model_fields"):
                field_names = list(cls.model_fields.keys())

            entities.append(
                EntityMetadata(
                    class_name=name,
                    module_path=module_name,
                    full_path=f"{module_name}.{name}",
                    summary=summary,
                    docstring=docstring,
                    field_names=field_names,
                    field_count=len(field_names),
                )
            )

    # Sort by class name for consistent ordering
    entities.sort(key=lambda e: e.class_name)
    return entities


def introspect_repositories(
    module: ModuleType | str,
    recursive: bool = True,
) -> list[RepositoryMetadata]:
    """Find all repository protocols in a module.

    Args:
        module: Module object or import path string
        recursive: If True, also scan submodules of a package

    Returns:
        List of RepositoryMetadata for each repository found
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    repositories = []

    # Get modules to scan
    if recursive:
        modules_to_scan = _iter_submodules(module)
        modules_to_scan.insert(0, module)
    else:
        modules_to_scan = [module]

    for mod in modules_to_scan:
        module_name = mod.__name__

        for name, cls in _get_module_classes(mod):
            # Check if it looks like a repository (name ends with Repository)
            if not name.endswith("Repository"):
                continue

            docstring = cls.__doc__
            summary = _get_first_line(docstring)

            # Get method names (exclude dunder methods)
            method_names = []
            for attr_name in dir(cls):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(cls, attr_name, None)
                if callable(attr) or isinstance(attr, property):
                    method_names.append(attr_name)

            entity_type = _infer_entity_type(name)

            repositories.append(
                RepositoryMetadata(
                    class_name=name,
                    module_path=module_name,
                    full_path=f"{module_name}.{name}",
                    summary=summary,
                    docstring=docstring,
                    method_names=method_names,
                    entity_type=entity_type,
                )
            )

    repositories.sort(key=lambda r: r.class_name)
    return repositories


def introspect_use_cases(
    module: ModuleType | str,
    recursive: bool = True,
) -> list[UseCaseCatalogEntry]:
    """Find all use case classes in a module.

    Use cases are identified by:
    - Class name ending in common use case suffixes (UseCase, Interactor, etc.)
    - Having an execute, run, or similar entry point method

    Args:
        module: Module object or import path string
        recursive: If True, also scan submodules of a package

    Returns:
        List of UseCaseCatalogEntry for each use case found
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    use_cases = []

    # Get modules to scan
    if recursive:
        modules_to_scan = _iter_submodules(module)
        modules_to_scan.insert(0, module)
    else:
        modules_to_scan = [module]

    # Common use case naming patterns
    use_case_suffixes = ("UseCase", "Interactor", "Handler", "Command", "Query")
    entry_methods = {"execute", "run", "handle", "process", "assemble_data"}

    for mod in modules_to_scan:
        module_name = mod.__name__

        for name, cls in _get_module_classes(mod):
            # Check if it looks like a use case
            is_use_case = False

            # Check by name suffix
            if any(name.endswith(suffix) for suffix in use_case_suffixes):
                is_use_case = True

            # Check by having entry point method
            if not is_use_case:
                class_methods = {m for m in dir(cls) if not m.startswith("_")}
                if class_methods & entry_methods:
                    is_use_case = True

            if not is_use_case:
                continue

            docstring = cls.__doc__
            summary = _get_first_line(docstring)
            crud_type = _classify_crud_type(name)

            use_cases.append(
                UseCaseCatalogEntry(
                    class_name=name,
                    module_path=module_name,
                    full_path=f"{module_name}.{name}",
                    summary=summary,
                    docstring=docstring,
                    crud_type=crud_type,
                )
            )

    use_cases.sort(key=lambda u: u.class_name)
    return use_cases


def introspect_module_recursive(
    base_module: ModuleType | str,
    entity_filter: str = "entities",
    repository_filter: str = "repositories",
    use_case_filter: str = "use_cases",
) -> dict[str, list]:
    """Recursively introspect a module tree.

    Finds entities, repositories, and use cases in submodules matching
    the given filter patterns.

    Args:
        base_module: Root module to start from
        entity_filter: Submodule name pattern for entities
        repository_filter: Submodule name pattern for repositories
        use_case_filter: Submodule name pattern for use cases

    Returns:
        Dict with 'entities', 'repositories', 'use_cases' keys
    """
    if isinstance(base_module, str):
        base_module = importlib.import_module(base_module)

    base_path = base_module.__name__
    result = {"entities": [], "repositories": [], "use_cases": []}

    # Try to import entity submodule
    try:
        entity_module = importlib.import_module(f"{base_path}.{entity_filter}")
        result["entities"] = introspect_entities(entity_module)
    except ImportError:
        pass

    # Try to import repository submodule
    try:
        repo_module = importlib.import_module(f"{base_path}.{repository_filter}")
        result["repositories"] = introspect_repositories(repo_module)
    except ImportError:
        pass

    # Try to import use case submodule
    try:
        uc_module = importlib.import_module(f"{base_path}.{use_case_filter}")
        result["use_cases"] = introspect_use_cases(uc_module)
    except ImportError:
        pass

    return result
