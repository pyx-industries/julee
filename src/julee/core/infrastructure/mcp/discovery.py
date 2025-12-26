"""Use case discovery for MCP server framework.

Introspects domain modules to discover use cases and their metadata
for automatic tool generation.
"""

import importlib
import inspect
import re
from collections import defaultdict
from collections.abc import Callable
from types import ModuleType
from typing import Any, get_type_hints

from .types import EntityMetadata, ServiceConfig, UseCaseMetadata

# CRUD operation patterns
CRUD_PREFIXES = ("Create", "Get", "List", "Update", "Delete")
DIAGRAM_PATTERN = re.compile(r"^Get(\w+)Diagram$")


def get_module_summary(module: ModuleType) -> str:
    """Extract first line of module docstring."""
    doc = getattr(module, "__doc__", None)
    if not doc:
        return ""
    return doc.strip().split("\n")[0]


def get_module_description(module: ModuleType) -> str:
    """Extract full module docstring."""
    doc = getattr(module, "__doc__", None)
    return doc.strip() if doc else ""


def get_class_summary(cls: type) -> str:
    """Extract first line of class docstring."""
    doc = getattr(cls, "__doc__", None)
    if not doc:
        return ""
    return doc.strip().split("\n")[0]


def get_use_case_summary(use_case_cls: type) -> str:
    """Extract first line of use case docstring."""
    return get_class_summary(use_case_cls)


def get_entity_summary(entity_cls: type) -> str:
    """Extract first line of entity class docstring."""
    return get_class_summary(entity_cls)


def _extract_request_response_types(
    use_case_cls: type, use_case_module: ModuleType
) -> tuple[type | None, type | None]:
    """Extract Request and Response types from a use case class.

    Looks at the execute() method type hints first, then falls back
    to naming conventions.
    """
    # Try to get from execute() method type hints
    execute_method = getattr(use_case_cls, "execute", None)
    if execute_method:
        try:
            hints = get_type_hints(execute_method)
            request_cls = None
            response_cls = None

            # Get request from first parameter (after self)
            sig = inspect.signature(execute_method)
            params = list(sig.parameters.values())
            if len(params) >= 2:  # self + request
                request_param = params[1]
                if request_param.annotation != inspect.Parameter.empty:
                    request_cls = hints.get(request_param.name)

            # Get response from return type
            response_cls = hints.get("return")

            if request_cls and response_cls:
                return request_cls, response_cls
        except Exception:
            pass

    # Fall back to naming convention: CreateFooUseCase -> CreateFooRequest, CreateFooResponse
    use_case_name = use_case_cls.__name__
    if use_case_name.endswith("UseCase"):
        base_name = use_case_name[:-7]  # Remove 'UseCase'
        request_name = f"{base_name}Request"
        response_name = f"{base_name}Response"

        request_cls = getattr(use_case_module, request_name, None)
        response_cls = getattr(use_case_module, response_name, None)

        if request_cls and response_cls:
            return request_cls, response_cls

    return None, None


def _parse_use_case_name(name: str) -> tuple[str | None, str | None, bool]:
    """Parse use case name to extract CRUD operation and entity name.

    Returns: (crud_operation, entity_name, is_diagram)
    """
    # Check for diagram pattern first: GetFooDiagramUseCase -> ('get', 'FooDiagram', True)
    if name.endswith("UseCase"):
        base = name[:-7]
        diagram_match = DIAGRAM_PATTERN.match(base)
        if diagram_match:
            return "get", diagram_match.group(1), True

        # Check for CRUD pattern
        for prefix in CRUD_PREFIXES:
            if base.startswith(prefix):
                entity = base[len(prefix) :]
                # Handle plurals: ListFoos -> Foo, ListFoosUseCase -> Foo
                if prefix == "List" and entity.endswith("s"):
                    entity = entity[:-1]
                    # Handle special plurals: Stories -> Story
                    if entity.endswith("ie"):
                        entity = entity[:-2] + "y"
                return prefix.lower(), entity, False

    return None, None, False


def _find_factory(
    use_case_cls: type, context_module: ModuleType
) -> Callable[[], Any] | None:
    """Find the factory function for a use case in the context module.

    Looks for patterns like:
    - get_create_foo_use_case() for CreateFooUseCase
    - USE_CASE_FACTORIES dict with class as key
    """
    use_case_name = use_case_cls.__name__

    # Try USE_CASE_FACTORIES dict
    factories = getattr(context_module, "USE_CASE_FACTORIES", None)
    if factories and use_case_cls in factories:
        return factories[use_case_cls]

    # Try function naming convention: CreateFooUseCase -> get_create_foo_use_case
    # Convert CamelCase to snake_case
    snake_name = re.sub(r"([A-Z])", r"_\1", use_case_name).lower().strip("_")
    factory_name = f"get_{snake_name}"

    factory = getattr(context_module, factory_name, None)
    if factory and callable(factory):
        return factory

    # Handle "Get" prefix use cases: GetFooDiagramUseCase -> get_foo_diagram_use_case
    # (avoid double get_ prefix)
    if snake_name.startswith("get_"):
        factory_name = snake_name
        factory = getattr(context_module, factory_name, None)
        if factory and callable(factory):
            return factory

    return None


def discover_use_cases(
    domain_module: ModuleType, context_module: ModuleType
) -> list[UseCaseMetadata]:
    """Discover all use cases from context module imports.

    Instead of scanning the domain module (which may not export use cases),
    we discover by introspecting the context module which imports the use
    case classes it provides factories for.

    Args:
        domain_module: The domain module (e.g. julee.c4) - used for module path
        context_module: The context module with DI factories and use case imports

    Returns:
        List of UseCaseMetadata for each discovered use case
    """
    use_cases: list[UseCaseMetadata] = []
    domain_prefix = domain_module.__name__

    # Discover use cases from context module imports
    for name in dir(context_module):
        if not name.endswith("UseCase"):
            continue

        obj = getattr(context_module, name, None)
        if not inspect.isclass(obj):
            continue

        # Verify it's from the domain module
        obj_module = getattr(obj, "__module__", "")
        if not obj_module.startswith(domain_prefix):
            continue

        # Try to get the module where this class is defined
        try:
            use_case_module = importlib.import_module(obj_module)
        except ImportError:
            use_case_module = context_module

        # Extract request/response types
        request_cls, response_cls = _extract_request_response_types(
            obj, use_case_module
        )
        if not request_cls or not response_cls:
            continue

        # Find factory
        factory = _find_factory(obj, context_module)
        if not factory:
            continue

        # Parse name for CRUD/diagram info
        crud_op, entity_name, is_diagram = _parse_use_case_name(name)

        # Remove only the trailing "UseCase" suffix for display name
        display_name = name[:-7] if name.endswith("UseCase") else name

        use_cases.append(
            UseCaseMetadata(
                name=display_name,
                use_case_cls=obj,
                request_cls=request_cls,
                response_cls=response_cls,
                factory=factory,
                is_crud=crud_op in ("create", "get", "list", "update", "delete"),
                crud_operation=crud_op,
                entity_name=entity_name,
                is_diagram=is_diagram,
            )
        )

    return use_cases


def discover_entities(
    domain_module: ModuleType, use_cases: list[UseCaseMetadata]
) -> list[EntityMetadata]:
    """Discover entities and group CRUD use cases by entity.

    Args:
        domain_module: The domain module
        use_cases: Previously discovered use cases

    Returns:
        List of EntityMetadata with associated CRUD use cases
    """
    # Group use cases by entity name
    entity_use_cases: dict[str, list[UseCaseMetadata]] = defaultdict(list)
    for uc in use_cases:
        if uc.entity_name and uc.is_crud and not uc.is_diagram:
            entity_use_cases[uc.entity_name].append(uc)

    entities: list[EntityMetadata] = []

    # Try to find entity classes in domain_module.entities
    entities_module = getattr(domain_module, "entities", None)

    for entity_name, cruds in entity_use_cases.items():
        # Try to find the entity class
        entity_cls = None
        if entities_module:
            entity_cls = getattr(entities_module, entity_name, None)

        if entity_cls:
            summary = get_entity_summary(entity_cls)
        else:
            summary = f"{entity_name} entity"

        entities.append(
            EntityMetadata(
                name=entity_name,
                entity_cls=entity_cls,  # type: ignore
                summary=summary,
                crud_use_cases=cruds,
            )
        )

    return entities


def build_service_config(
    slug: str, domain_module: ModuleType, context_module: ModuleType
) -> ServiceConfig:
    """Build complete service configuration from domain module.

    Args:
        slug: Service identifier (e.g. 'c4', 'hcd')
        domain_module: The domain module
        context_module: The context module with DI factories

    Returns:
        ServiceConfig with all discovered use cases and entities
    """
    use_cases = discover_use_cases(domain_module, context_module)
    entities = discover_entities(domain_module, use_cases)

    return ServiceConfig(
        slug=slug,
        domain_module=domain_module,
        context_module=context_module,
        use_cases=use_cases,
        entities=entities,
    )
