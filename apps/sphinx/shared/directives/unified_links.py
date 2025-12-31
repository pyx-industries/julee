"""Unified links directive for automatic bidirectional documentation.

Renders documentation links via both architectural conformance (instance discovery)
and semantic relations (type declarations).

Usage for Core type CLASS page (hub):
    .. unified-links:: BoundedContext
       :mode: type

Usage for entity INSTANCE page:
    .. unified-links:: Accelerator
       :slug: hcd
       :mode: instance

The directive creates a placeholder that is resolved at doctree-resolved time
to allow cross-references to be fully resolved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from apps.sphinx.shared.services.unified_link_resolver import LinkResult


# =============================================================================
# Placeholder Node
# =============================================================================


class UnifiedLinksPlaceholder(nodes.General, nodes.Element):
    """Placeholder node replaced at doctree-resolved time.

    Stores directive parameters for deferred resolution when all
    cross-references are available.
    """

    pass


# =============================================================================
# Directive
# =============================================================================


class UnifiedLinksDirective(SphinxDirective):
    """Render unified documentation links (instances + semantic relations).

    This directive enables automatic bidirectional documentation by:
    1. Discovering instances of Core types (architectural conformance)
    2. Traversing semantic relations (type declarations)

    Usage:
        .. unified-links:: BoundedContext
           :mode: type

        .. unified-links:: Accelerator
           :slug: hcd
           :mode: instance
    """

    required_arguments = 1  # Entity type name
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = False

    option_spec = {
        "slug": directives.unchanged,
        "mode": directives.unchanged,  # "type" or "instance"
        "show-empty": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Create placeholder for deferred resolution."""
        node = UnifiedLinksPlaceholder()
        node["entity_type_name"] = self.arguments[0]
        node["slug"] = self.options.get("slug")
        node["mode"] = self.options.get("mode", "instance")
        node["show_empty"] = "show-empty" in self.options
        node["docname"] = self.env.docname
        return [node]


# =============================================================================
# Placeholder Resolution
# =============================================================================


def resolve_unified_links_placeholder(
    node: UnifiedLinksPlaceholder,
    app: "Sphinx",
) -> list[nodes.Node]:
    """Resolve placeholder to actual content.

    Called during doctree-resolved event.

    Args:
        node: Placeholder node with stored parameters
        app: Sphinx application

    Returns:
        List of docutils nodes to replace placeholder
    """
    entity_type_name = node["entity_type_name"]
    slug = node.get("slug")
    mode = node.get("mode", "instance")
    show_empty = node.get("show_empty", False)
    docname = node.get("docname", "")

    # Get the entity type
    entity_type = _resolve_entity_type(entity_type_name)
    if entity_type is None:
        if show_empty:
            return []
        para = nodes.paragraph()
        para += nodes.Text(f"Unknown entity type: {entity_type_name}")
        return [para]

    # Get resolver and resolve links
    resolver = _get_resolver(app)

    # Run async code synchronously - handle event loop properly
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're in an async context, create a new task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            if mode == "type":
                future = executor.submit(
                    asyncio.run, resolver.resolve_for_core_type(entity_type)
                )
            else:
                future = executor.submit(
                    asyncio.run, resolver.resolve_for_instance(entity_type, slug or "")
                )
            result = future.result()
    else:
        # No running event loop, use asyncio.run
        if mode == "type":
            result = asyncio.run(resolver.resolve_for_core_type(entity_type))
        else:
            result = asyncio.run(resolver.resolve_for_instance(entity_type, slug or ""))

    if not result.has_content:
        if show_empty:
            return []
        return []

    # Render result to nodes
    return _render_link_result(result, docname)


def _resolve_entity_type(name: str) -> type | None:
    """Resolve entity type name to actual type.

    Args:
        name: Entity type name (e.g., "BoundedContext", "Accelerator")

    Returns:
        Entity class or None if not found
    """
    # Core entities
    if name == "BoundedContext":
        from julee.core.entities.bounded_context import BoundedContext

        return BoundedContext
    if name == "Application":
        from julee.core.entities.application import Application

        return Application

    # HCD entities
    if name == "Accelerator":
        from julee.supply_chain.entities.accelerator import Accelerator

        return Accelerator
    if name == "Persona":
        from julee.hcd.entities.persona import Persona

        return Persona
    if name == "Journey":
        from julee.hcd.entities.journey import Journey

        return Journey
    if name == "Epic":
        from julee.hcd.entities.epic import Epic

        return Epic
    if name == "Story":
        from julee.hcd.entities.story import Story

        return Story
    if name == "App":
        from julee.hcd.entities.app import App

        return App
    if name == "Integration":
        from julee.hcd.entities.integration import Integration

        return Integration

    return None


def _get_resolver(app: "Sphinx") -> Any:
    """Get the UnifiedLinkResolver for the app.

    Args:
        app: Sphinx application

    Returns:
        Configured UnifiedLinkResolver
    """
    from apps.sphinx.shared.documentation_mapping import get_documentation_mapping
    from apps.sphinx.shared.services.unified_link_resolver import UnifiedLinkResolver

    from julee.core.services.semantic_relation_registry import SemanticRelationRegistry

    # Check if resolver is cached on app
    if not hasattr(app, "_unified_link_resolver"):
        # Get registry from app if available (initialized by builder-inited)
        registry = getattr(app, "_semantic_relation_registry", None)
        if registry is None:
            registry = SemanticRelationRegistry()

        # Get repositories if available
        bc_repo = None
        app_repo = None

        # Try to get from core context if available
        if hasattr(app, "_core_context"):
            ctx = app._core_context
            if hasattr(ctx, "bc_repo"):
                bc_repo = ctx.bc_repo
            if hasattr(ctx, "app_repo"):
                app_repo = ctx.app_repo

        mapping = get_documentation_mapping()
        app._unified_link_resolver = UnifiedLinkResolver(
            registry=registry,
            mapping=mapping,
            bc_repo=bc_repo,
            app_repo=app_repo,
        )

    return app._unified_link_resolver


def _render_link_result(result: "LinkResult", docname: str) -> list[nodes.Node]:
    """Render LinkResult to docutils nodes.

    Args:
        result: LinkResult from resolver
        docname: Current document name for relative path calculation

    Returns:
        List of docutils nodes
    """
    result_nodes: list[nodes.Node] = []

    # Render instances (for hub pages)
    if result.instances:
        section = nodes.section()
        section["ids"] = [f"all-{result.entity_type_name.lower()}s"]

        title = nodes.title()
        title += nodes.Text(f"All {result.entity_type_name}s")
        section += title

        for group in result.instances:
            if group.links:
                # Add category heading
                para = nodes.paragraph()
                para += nodes.strong(text=f"{group.label}:")
                section += para

                # Add links as bullet list
                bullet_list = nodes.bullet_list()
                for link in group.links:
                    item = nodes.list_item()
                    para = nodes.paragraph()
                    ref = nodes.reference("", "", refuri=link.href)
                    ref += nodes.Text(link.title)
                    para += ref
                    item += para
                    bullet_list += item
                section += bullet_list

        result_nodes.append(section)

    # Render outbound relations
    if result.outbound:
        section = nodes.section()
        section["ids"] = ["related-entities"]

        title = nodes.title()
        title += nodes.Text("Related Entities")
        section += title

        for group in result.outbound:
            if group.links:
                para = nodes.paragraph()
                para += nodes.strong(text=f"{group.label}:")
                section += para

                bullet_list = nodes.bullet_list()
                for link in group.links:
                    item = nodes.list_item()
                    para = nodes.paragraph()
                    ref = nodes.reference("", "", refuri=link.href)
                    ref += nodes.Text(link.title)
                    para += ref
                    item += para
                    bullet_list += item
                section += bullet_list

        result_nodes.append(section)

    # Render inbound relations
    if result.inbound:
        section = nodes.section()
        section["ids"] = ["referenced-by"]

        title = nodes.title()
        title += nodes.Text("Referenced By")
        section += title

        for group in result.inbound:
            if group.links:
                para = nodes.paragraph()
                para += nodes.strong(text=f"{group.label}:")
                section += para

                bullet_list = nodes.bullet_list()
                for link in group.links:
                    item = nodes.list_item()
                    para = nodes.paragraph()
                    ref = nodes.reference("", "", refuri=link.href)
                    ref += nodes.Text(link.title)
                    para += ref
                    item += para
                    bullet_list += item
                section += bullet_list

        result_nodes.append(section)

    return result_nodes


# =============================================================================
# Event Handler
# =============================================================================


def process_unified_links_placeholders(
    app: "Sphinx",
    doctree: nodes.document,
    docname: str,
) -> None:
    """Process UnifiedLinksPlaceholder nodes during doctree-resolved.

    Args:
        app: Sphinx application
        doctree: Document tree being processed
        docname: Name of document being processed
    """
    for node in doctree.traverse(UnifiedLinksPlaceholder):
        replacement = resolve_unified_links_placeholder(node, app)
        node.replace_self(replacement)
