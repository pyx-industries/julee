"""Documentation rendering service protocol.

Defines the interface for services that render bounded context entities
to documentation formats (RST, HTML, etc.). Use cases and applications
inject this service to render entity data for documentation output.

The service handles:
- Index views (list of entities)
- Detail views (single entity)
- Summary views (compact inline)

Entity Semantics:
    This service transforms BoundedContext entities into Documentation
    artifacts. It bridges the domain model with documentation output,
    bound to multiple entity types as required for services.

Template discovery follows convention:
    {bc}/infrastructure/templates/{entity_type}_{view_type}.rst.j2

Example:
    julee/hcd/infrastructure/templates/persona_index.rst.j2
    julee/hcd/infrastructure/templates/persona_detail.rst.j2
"""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from julee.core.entities.bounded_context import BoundedContext
from julee.core.entities.documentation import Documentation


@runtime_checkable
class DocumentationRenderingService(Protocol):
    """Service protocol for rendering entities to documentation format.

    Transforms: BoundedContext entities → Documentation artifacts

    Implementations handle template loading, path resolution, and
    format-specific concerns (e.g., Sphinx relative URIs).
    """

    def get_documentation_config(
        self, bounded_context: BoundedContext
    ) -> Documentation:
        """Get documentation configuration for a bounded context.

        Args:
            bounded_context: The bounded context to get docs config for

        Returns:
            Documentation configuration for the context
        """
        ...

    def render_index(
        self,
        entities: list[BaseModel],
        entity_type: str,
        docname: str,
        **options,
    ) -> str:
        """Render a list of entities as an index view.

        Args:
            entities: List of entity instances to render
            entity_type: Entity type name (e.g., "persona", "epic")
            docname: Current document path for relative link calculation
            **options: Additional rendering options (e.g., format="summary")

        Returns:
            Rendered documentation string (typically RST)
        """
        ...

    def render_entity(
        self,
        entity: BaseModel,
        entity_type: str,
        docname: str,
        view_type: str = "detail",
        **options,
    ) -> str:
        """Render a single entity.

        Args:
            entity: Entity instance to render
            entity_type: Entity type name (e.g., "persona", "epic")
            docname: Current document path for relative link calculation
            view_type: View type (e.g., "detail", "summary", "card")
            **options: Additional rendering options

        Returns:
            Rendered documentation string (typically RST)
        """
        ...
