"""Unified link resolver for automatic bidirectional documentation.

This service provides automatic documentation cross-references via two mechanisms:

1. **Architectural Conformance (Instance Discovery)**
   When solution code creates instances of Core entities (e.g., a BC at src/crm/),
   Core entity documentation pages automatically list all instances without
   requiring any decorators.

2. **Semantic Relations (Type Declarations)**
   When entities are decorated with @semantic_relation, documentation shows
   bidirectional links automatically.

Example:
    resolver = UnifiedLinkResolver(registry, mapping, bc_repo, app_repo)

    # For Core type CLASS page (hub) - lists all instances
    result = await resolver.resolve_for_core_type(BoundedContext)
    # Returns instances of all BCs + inbound semantic references

    # For entity INSTANCE page - shows semantic relations
    result = await resolver.resolve_for_instance(Accelerator, "hcd")
    # Returns outbound + inbound semantic links

The result can be rendered by templates to create hub pages where Core entity
documentation lists all instances and shows what references them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from julee.core.entities.semantic_relation import RelationType
from julee.core.services.semantic_relation_registry import (
    RelationEdge,
    SemanticRelationRegistry,
    get_forward_label,
    get_inverse_label,
)

if TYPE_CHECKING:
    from apps.sphinx.shared.documentation_mapping import DocumentationMapping
    from julee.core.repositories.application import ApplicationRepository
    from julee.core.repositories.bounded_context import BoundedContextRepository


# =============================================================================
# Data Structures
# =============================================================================


@dataclass(frozen=True)
class Link:
    """A resolved documentation link.

    Attributes:
        title: Display text for the link
        href: Documentation URL (relative or absolute)
        slug: Entity slug for identification
        category: Classification (e.g., "framework", "solution", "semantic")
    """

    title: str
    href: str
    slug: str
    category: str = "default"


@dataclass
class LinkGroup:
    """A labeled group of related links.

    Used to organize links by relationship type (e.g., "Projects", "Referenced by").

    Attributes:
        label: Human-readable group label
        links: Links in this group
        relation_type: Optional relation type this group represents
    """

    label: str
    links: list[Link] = field(default_factory=list)
    relation_type: RelationType | None = None


@dataclass
class LinkResult:
    """Result of resolving links for an entity.

    Combines instance discovery and semantic relation results.

    Attributes:
        instances: Discovered instances (for Core type pages)
        outbound: Outbound semantic relations (entity -> others)
        inbound: Inbound semantic relations (others -> entity)
        entity_type_name: Name of the entity type being documented
    """

    entity_type_name: str = ""
    instances: list[LinkGroup] = field(default_factory=list)
    outbound: list[LinkGroup] = field(default_factory=list)
    inbound: list[LinkGroup] = field(default_factory=list)

    @property
    def has_content(self) -> bool:
        """True if there are any links to display."""
        return bool(self.instances or self.outbound or self.inbound)


# =============================================================================
# Resolver
# =============================================================================


class UnifiedLinkResolver:
    """Resolves documentation links via both architectural and semantic mechanisms.

    This service enables automatic bidirectional documentation by:

    1. Discovering instances of Core types (BoundedContext, Application)
       without requiring any decorators - the code structure IS the declaration.

    2. Traversing semantic relations declared via @semantic_relation decorator
       to create bidirectional cross-references.

    Example:
        # On BoundedContext class page (hub):
        result = await resolver.resolve_for_core_type(BoundedContext)
        # instances: [Link(hcd), Link(c4), Link(core), ...]
        # inbound: [LinkGroup("Projected by", [Link(Accelerator)])]

        # On Accelerator instance page:
        result = await resolver.resolve_for_instance(Accelerator, "hcd")
        # outbound: [LinkGroup("Projects", [Link(BoundedContext hcd)])]
    """

    def __init__(
        self,
        registry: SemanticRelationRegistry,
        mapping: "DocumentationMapping",
        bc_repo: "BoundedContextRepository | None" = None,
        app_repo: "ApplicationRepository | None" = None,
    ):
        """Initialize the resolver.

        Args:
            registry: SemanticRelationRegistry for relation traversal
            mapping: DocumentationMapping for URL resolution
            bc_repo: Optional repository for BC instance discovery
            app_repo: Optional repository for Application instance discovery
        """
        self.registry = registry
        self.mapping = mapping
        self.bc_repo = bc_repo
        self.app_repo = app_repo

    async def resolve_for_core_type(self, core_type: type) -> LinkResult:
        """Resolve links for a Core entity TYPE page (hub page).

        For Core entity class documentation pages, this discovers all instances
        of that type and finds semantic relations pointing to it.

        Args:
            core_type: Core entity class (e.g., BoundedContext, Application)

        Returns:
            LinkResult with instances and inbound semantic references
        """
        result = LinkResult(entity_type_name=core_type.__name__)

        # Mechanism 1: Instance Discovery
        instances = await self._discover_instances(core_type)
        if instances:
            result.instances = instances

        # Mechanism 2: Inbound Semantic Relations (at type level)
        inbound = self._get_inbound_type_relations(core_type)
        if inbound:
            result.inbound = inbound

        return result

    async def resolve_for_instance(
        self,
        entity_type: type,
        slug: str,
        instance: Any = None,
    ) -> LinkResult:
        """Resolve links for an entity INSTANCE page.

        For entity instance documentation pages, this finds both outbound
        and inbound semantic relations.

        Args:
            entity_type: Entity class (e.g., Accelerator, Story)
            slug: Entity instance slug
            instance: Optional entity instance for additional context

        Returns:
            LinkResult with outbound and inbound semantic links
        """
        result = LinkResult(entity_type_name=entity_type.__name__)

        # Outbound semantic relations (this entity -> others)
        outbound = self._get_outbound_relations(entity_type, slug, instance)
        if outbound:
            result.outbound = outbound

        # Inbound semantic relations (others -> this entity)
        # Note: This requires knowing what instances of other types
        # have relations pointing to this specific instance
        inbound = await self._get_inbound_instance_relations(
            entity_type, slug, instance
        )
        if inbound:
            result.inbound = inbound

        return result

    # -------------------------------------------------------------------------
    # Instance Discovery (Architectural Conformance)
    # -------------------------------------------------------------------------

    async def _discover_instances(self, core_type: type) -> list[LinkGroup]:
        """Discover all instances of a Core type.

        Uses repositories to find instances - no decorator required.

        Args:
            core_type: Core entity class to discover instances of

        Returns:
            List of LinkGroups categorized by framework/solution
        """
        from julee.core.entities.application import Application
        from julee.core.entities.bounded_context import BoundedContext

        links: list[Link] = []

        if core_type == BoundedContext and self.bc_repo:
            bcs = await self.bc_repo.list_all()
            for bc in bcs:
                href = self._resolve_href(BoundedContext, bc.slug)
                category = self._categorize_bc(bc)
                links.append(
                    Link(
                        title=bc.display_name,
                        href=href,
                        slug=bc.slug,
                        category=category,
                    )
                )

        elif core_type == Application and self.app_repo:
            apps = await self.app_repo.list_all()
            for app in apps:
                href = self._resolve_href(Application, app.slug)
                links.append(
                    Link(
                        title=app.display_name,
                        href=href,
                        slug=app.slug,
                        category="application",
                    )
                )

        if not links:
            return []

        # Group by category
        groups: dict[str, list[Link]] = {}
        for link in links:
            if link.category not in groups:
                groups[link.category] = []
            groups[link.category].append(link)

        return [
            LinkGroup(label=category.title(), links=sorted(group_links, key=lambda l: l.slug))
            for category, group_links in sorted(groups.items())
        ]

    def _categorize_bc(self, bc: Any) -> str:
        """Categorize a bounded context for grouping.

        Args:
            bc: BoundedContext instance

        Returns:
            Category string (e.g., "framework", "viewpoint", "contrib")
        """
        if bc.is_viewpoint:
            return "viewpoint"
        if bc.is_contrib:
            return "contrib"
        # Check if it's a framework BC (under julee.*)
        if hasattr(bc, "import_path") and bc.import_path.startswith("julee."):
            return "framework"
        return "solution"

    # -------------------------------------------------------------------------
    # Semantic Relations
    # -------------------------------------------------------------------------

    def _get_outbound_relations(
        self,
        entity_type: type,
        slug: str,
        instance: Any = None,
    ) -> list[LinkGroup]:
        """Get outbound semantic relations for an entity instance.

        Args:
            entity_type: Entity class
            slug: Entity slug
            instance: Optional entity instance

        Returns:
            List of LinkGroups for outbound relations
        """
        edges = self.registry.get_outbound_relations(entity_type)
        if not edges:
            return []

        # Group edges by relation type
        groups_by_type: dict[RelationType, list[RelationEdge]] = {}
        for edge in edges:
            if edge.relation_type not in groups_by_type:
                groups_by_type[edge.relation_type] = []
            groups_by_type[edge.relation_type].append(edge)

        result = []
        for rel_type, rel_edges in groups_by_type.items():
            links = []
            for edge in rel_edges:
                # For outbound, we need the target's slug
                # Convention: entity has {target_type_lower}_slug attribute
                target_slug = self._get_target_slug(edge.target_type, instance)
                if target_slug:
                    href = self._resolve_href(edge.target_type, target_slug)
                    links.append(
                        Link(
                            title=self._get_target_title(edge.target_type, target_slug),
                            href=href,
                            slug=target_slug,
                            category="semantic",
                        )
                    )

            if links:
                result.append(
                    LinkGroup(
                        label=get_forward_label(rel_type),
                        links=links,
                        relation_type=rel_type,
                    )
                )

        return result

    def _get_inbound_type_relations(self, entity_type: type) -> list[LinkGroup]:
        """Get inbound semantic relations at the TYPE level.

        This finds what entity TYPES have relations pointing to this type.
        Used for hub pages to show "Accelerator PROJECTS BoundedContext".

        Args:
            entity_type: Entity class being documented

        Returns:
            List of LinkGroups for inbound type-level relations
        """
        edges = self.registry.get_inbound_relations(entity_type)
        if not edges:
            return []

        # Group edges by relation type
        groups_by_type: dict[RelationType, list[RelationEdge]] = {}
        for edge in edges:
            if edge.relation_type not in groups_by_type:
                groups_by_type[edge.relation_type] = []
            groups_by_type[edge.relation_type].append(edge)

        result = []
        for rel_type, rel_edges in groups_by_type.items():
            links = []
            for edge in rel_edges:
                # Link to the source type's documentation
                source_type = edge.source_type
                # For type-level links, link to the class page
                href = self._resolve_type_href(source_type)
                links.append(
                    Link(
                        title=source_type.__name__,
                        href=href,
                        slug=source_type.__name__.lower(),
                        category="semantic",
                    )
                )

            if links:
                result.append(
                    LinkGroup(
                        label=get_inverse_label(rel_type),
                        links=links,
                        relation_type=rel_type,
                    )
                )

        return result

    async def _get_inbound_instance_relations(
        self,
        entity_type: type,
        slug: str,
        instance: Any = None,
    ) -> list[LinkGroup]:
        """Get inbound semantic relations for a specific instance.

        This finds what other entity INSTANCES have relations pointing to
        this specific instance. More complex than type-level lookup as it
        requires scanning instance data.

        Args:
            entity_type: Entity class
            slug: Entity slug
            instance: Optional entity instance

        Returns:
            List of LinkGroups for inbound instance-level relations
        """
        # For now, return type-level inbound relations
        # Instance-level back-references would require scanning all instances
        # of source types - this could be extended with a more sophisticated
        # indexing mechanism if needed
        return self._get_inbound_type_relations(entity_type)

    # -------------------------------------------------------------------------
    # URL Resolution Helpers
    # -------------------------------------------------------------------------

    def _resolve_href(self, entity_type: type, slug: str) -> str:
        """Resolve documentation URL for an entity instance.

        Args:
            entity_type: Entity class
            slug: Entity slug

        Returns:
            Documentation URL (relative)
        """
        result = self.mapping.resolve(entity_type, slug)
        if result is None:
            return f"#{slug}"
        if isinstance(result, tuple):
            docname, anchor = result
            return f"{docname}.html#{anchor}"
        return f"{result}.html"

    def _resolve_type_href(self, entity_type: type) -> str:
        """Resolve documentation URL for an entity TYPE (class page).

        Args:
            entity_type: Entity class

        Returns:
            Documentation URL for the class page
        """
        # Convention: autoapi pages are at autoapi/{module}/{class}/index.html
        module = entity_type.__module__.replace(".", "/")
        return f"autoapi/{module}/index.html#{entity_type.__name__}"

    def _get_target_slug(self, target_type: type, instance: Any) -> str | None:
        """Get the slug for a relation target from an instance.

        Convention: instance has {target_type_lower}_slug attribute.

        Args:
            target_type: Target entity type
            instance: Source entity instance

        Returns:
            Target slug or None if not found
        """
        if instance is None:
            return None

        # Try {type_lower}_slug convention
        attr_name = f"{target_type.__name__.lower()}_slug"
        slug = getattr(instance, attr_name, None)
        if slug:
            return slug

        # Try {type_lower} as direct attribute
        attr_name = target_type.__name__.lower()
        return getattr(instance, attr_name, None)

    def _get_target_title(self, target_type: type, slug: str) -> str:
        """Get display title for a target entity.

        Args:
            target_type: Target entity type
            slug: Target entity slug

        Returns:
            Human-readable title
        """
        return slug.replace("-", " ").replace("_", " ").title()


# =============================================================================
# Factory
# =============================================================================


def create_unified_link_resolver(
    bc_repo: "BoundedContextRepository | None" = None,
    app_repo: "ApplicationRepository | None" = None,
) -> UnifiedLinkResolver:
    """Create a UnifiedLinkResolver with default configuration.

    Args:
        bc_repo: Optional BoundedContext repository for instance discovery
        app_repo: Optional Application repository for instance discovery

    Returns:
        Configured UnifiedLinkResolver
    """
    from apps.sphinx.shared.documentation_mapping import get_documentation_mapping

    from julee.core.services.semantic_relation_registry import SemanticRelationRegistry

    registry = SemanticRelationRegistry()
    mapping = get_documentation_mapping()

    return UnifiedLinkResolver(
        registry=registry,
        mapping=mapping,
        bc_repo=bc_repo,
        app_repo=app_repo,
    )
