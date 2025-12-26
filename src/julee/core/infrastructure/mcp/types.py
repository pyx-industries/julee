"""Type definitions for MCP server framework.

Defines configuration and metadata types used for automatic tool generation
from domain use cases.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any


@dataclass
class UseCaseMetadata:
    """Metadata about a discovered use case.

    Extracted from a use case class for tool generation.
    """

    name: str
    """Use case name, e.g. 'CreateSoftwareSystem'."""

    use_case_cls: type
    """The use case class itself."""

    request_cls: type
    """Request model class (Pydantic BaseModel)."""

    response_cls: type
    """Response model class (Pydantic BaseModel)."""

    factory: Callable[[], Any]
    """DI factory function that creates an instance of the use case."""

    is_crud: bool = False
    """Whether this is a CRUD operation (Create/Get/List/Update/Delete)."""

    crud_operation: str | None = None
    """CRUD operation type: 'create', 'get', 'list', 'update', 'delete'."""

    entity_name: str | None = None
    """Entity name for CRUD operations, e.g. 'SoftwareSystem'."""

    is_diagram: bool = False
    """Whether this is a diagram generation use case."""


@dataclass
class EntityMetadata:
    """Metadata about a domain entity.

    Used for Level 2 progressive disclosure resources.
    """

    name: str
    """Entity class name, e.g. 'SoftwareSystem'."""

    entity_cls: type
    """The entity class itself."""

    summary: str
    """First line of entity docstring."""

    crud_use_cases: list[UseCaseMetadata] = field(default_factory=list)
    """CRUD use cases associated with this entity."""


@dataclass
class ServiceConfig:
    """Configuration for an MCP service.

    Contains all metadata needed to generate tools and resources
    for a domain module.
    """

    slug: str
    """Service identifier used in URIs, e.g. 'c4', 'hcd'."""

    domain_module: ModuleType
    """The domain module (e.g. julee.c4)."""

    context_module: ModuleType
    """The context module with DI factories."""

    use_cases: list[UseCaseMetadata] = field(default_factory=list)
    """All discovered use cases."""

    entities: list[EntityMetadata] = field(default_factory=list)
    """All discovered entities."""
