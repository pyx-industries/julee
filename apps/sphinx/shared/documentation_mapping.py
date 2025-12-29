"""Documentation mapping registry using SemanticRelation.

Centralizes the mapping from entity types to documentation patterns.
Uses SemanticRelation introspection to determine documentation targets:

- Entities with PROJECTS relations inherit their target's documentation pattern
- Entities with explicit patterns use those directly
- Entities without explicit patterns use a default autoapi pattern

This allows role resolution to be driven by semantic relations declared
on entity types, rather than hardcoded patterns in Sphinx extensions.

Example:
    # Accelerator PROJECTS BoundedContext
    # So :accelerator:`slug` resolves to BC's autoapi page

    from apps.sphinx.shared.documentation_mapping import DocumentationMapping

    mapping = DocumentationMapping()
    pattern = mapping.get_pattern(Accelerator)
    # Returns "autoapi/julee/{slug}/index" (from BoundedContext)
"""

from typing import TYPE_CHECKING, Callable

from julee.core.decorators import get_semantic_relations
from julee.core.entities.semantic_relation import RelationType

if TYPE_CHECKING:
    from sphinx.application import Sphinx


class DocumentationPattern:
    """A documentation pattern for an entity type.

    Patterns describe how to resolve an entity slug to a documentation URI:

    - page: Direct page pattern, e.g., "users/personas/{slug}"
    - autoapi: Autoapi page pattern, e.g., "autoapi/julee/{slug}/index"
    - anchor: Lookup function returning (docname, anchor) tuple
    - projected: Follow PROJECTS relation to get target's pattern
    """

    def __init__(
        self,
        pattern_type: str,
        pattern: str | None = None,
        lookup_func: Callable[[str, "Sphinx"], tuple[str, str] | None] | None = None,
    ):
        """Initialize documentation pattern.

        Args:
            pattern_type: One of "page", "autoapi", "anchor", "projected"
            pattern: URL pattern with {slug} placeholder (for page/autoapi)
            lookup_func: Function for anchor lookup (for anchor type)
        """
        self.pattern_type = pattern_type
        self.pattern = pattern
        self.lookup_func = lookup_func

    def resolve(self, slug: str, app: "Sphinx | None" = None) -> str | tuple[str, str]:
        """Resolve slug to documentation target.

        Args:
            slug: Entity slug to resolve
            app: Sphinx application (required for anchor lookups)

        Returns:
            For page/autoapi: docname string
            For anchor: (docname, anchor) tuple
        """
        if self.pattern_type in ("page", "autoapi"):
            if self.pattern is None:
                raise ValueError(f"Pattern required for {self.pattern_type} type")
            return self.pattern.format(slug=slug)

        if self.pattern_type == "anchor":
            if self.lookup_func is None:
                raise ValueError("Lookup function required for anchor type")
            if app is None:
                raise ValueError("Sphinx app required for anchor lookup")
            result = self.lookup_func(slug, app)
            if result is None:
                # Dangling ref - return slug as anchor
                return (slug, slug)
            return result

        raise ValueError(f"Unknown pattern type: {self.pattern_type}")


class DocumentationMapping:
    """Registry mapping entity types to documentation patterns.

    Uses SemanticRelation introspection to resolve patterns:
    - If entity has PROJECTS relation, follow to target's pattern
    - Otherwise use registered pattern for the entity type
    """

    def __init__(self):
        """Initialize the mapping registry."""
        self._patterns: dict[type, DocumentationPattern] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default patterns for framework entity types."""
        # Import here to avoid circular imports at module level
        from julee.core.entities.application import Application
        from julee.core.entities.bounded_context import BoundedContext

        # Core entities - autoapi pages
        self.register(
            BoundedContext,
            DocumentationPattern("autoapi", "autoapi/julee/{slug}/index"),
        )
        self.register(
            Application,
            DocumentationPattern("autoapi", "autoapi/apps/{slug}/index"),
        )

        # HCD entities with dedicated pages
        from julee.hcd.entities.epic import Epic
        from julee.hcd.entities.journey import Journey
        from julee.hcd.entities.persona import Persona

        self.register(
            Persona,
            DocumentationPattern("page", "users/personas/{slug}"),
        )
        self.register(
            Epic,
            DocumentationPattern("page", "users/epics/{slug}"),
        )
        self.register(
            Journey,
            DocumentationPattern("page", "users/journeys/{slug}"),
        )

        # Note: Story and Integration use anchor patterns that require
        # Sphinx app for lookup. These should be registered by the
        # Sphinx extension using register_anchor().

    def register(self, entity_type: type, pattern: DocumentationPattern):
        """Register a documentation pattern for an entity type.

        Args:
            entity_type: The entity class
            pattern: Documentation pattern for that type
        """
        self._patterns[entity_type] = pattern

    def register_anchor(
        self,
        entity_type: type,
        lookup_func: Callable[[str, "Sphinx"], tuple[str, str] | None],
    ):
        """Register an anchor-based pattern for an entity type.

        Args:
            entity_type: The entity class
            lookup_func: Function(slug, app) -> (docname, anchor) or None
        """
        self._patterns[entity_type] = DocumentationPattern(
            "anchor", lookup_func=lookup_func
        )

    def get_pattern(self, entity_type: type) -> DocumentationPattern | None:
        """Get documentation pattern for an entity type.

        Resolves PROJECTS relations to find the target's pattern.

        Args:
            entity_type: The entity class to look up

        Returns:
            DocumentationPattern or None if not found
        """
        # Check for direct registration first
        if entity_type in self._patterns:
            return self._patterns[entity_type]

        # Check for PROJECTS relation - use target's pattern
        relations = get_semantic_relations(entity_type)
        for rel in relations:
            if rel.relation_type == RelationType.PROJECTS:
                target_pattern = self.get_pattern(rel.target_type)
                if target_pattern:
                    return target_pattern

        return None

    def resolve(
        self, entity_type: type, slug: str, app: "Sphinx | None" = None
    ) -> str | tuple[str, str] | None:
        """Resolve entity slug to documentation target.

        Args:
            entity_type: The entity class
            slug: Entity slug to resolve
            app: Sphinx application (required for anchor lookups)

        Returns:
            docname string, (docname, anchor) tuple, or None if not found
        """
        pattern = self.get_pattern(entity_type)
        if pattern is None:
            return None
        return pattern.resolve(slug, app)


# Singleton instance for use across Sphinx extensions
_mapping: DocumentationMapping | None = None


def get_documentation_mapping() -> DocumentationMapping:
    """Get the global documentation mapping instance.

    Returns:
        The singleton DocumentationMapping
    """
    global _mapping
    if _mapping is None:
        _mapping = DocumentationMapping()
    return _mapping
