"""Sphinx roles for cross-referencing domain entities.

Provides role factories for creating inline cross-references to:
- Core entities (UseCase, Entity, BoundedContext, Application) -> autoapi pages
- HCD entities (Persona, Epic, Journey) -> dedicated pages
- HCD entities (Story, Integration) -> anchors in other pages
- C4 entities (SoftwareSystem, Container) -> views over Core entities
"""

import re
from typing import TYPE_CHECKING, Callable

from docutils import nodes
from sphinx.util.docutils import SphinxRole

from . import build_relative_uri

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from apps.sphinx.shared.documentation_mapping import DocumentationMapping


class EntityRefRole(SphinxRole):
    """Base role for entity cross-references.

    Provides:
    - Parsing of `Title <slug>` or `slug` syntax
    - Relative URI building
    - Dangling reference tolerance
    """

    def parse_target(self) -> tuple[str, str]:
        """Parse role content into (title, slug).

        Supports:
        - `slug` -> (title_from_slug, slug)
        - `Title <slug>` -> (Title, slug)
        """
        text = self.text.strip()

        # Check for explicit title: `Title <slug>`
        match = re.match(r"^(.+?)\s*<([^>]+)>$", text)
        if match:
            title = match.group(1).strip()
            slug = match.group(2).strip()
            return title, slug

        # Just slug - derive title from slug
        slug = text
        title = slug.replace("-", " ").replace("_", " ").title()
        return title, slug

    def build_uri(self, target_doc: str, anchor: str | None = None) -> str:
        """Build relative URI from current document to target."""
        return build_relative_uri(self.env.docname, target_doc, anchor)

    def make_ref_node(self, title: str, uri: str) -> nodes.reference:
        """Create reference node with title and URI."""
        ref = nodes.reference("", "", refuri=uri)
        ref += nodes.Text(title)
        return ref

    def run(self) -> tuple[list[nodes.Node], list]:
        """Execute role - subclasses should override resolve()."""
        title, slug = self.parse_target()
        uri = self.resolve(slug)
        return [self.make_ref_node(title, uri)], []

    def resolve(self, slug: str) -> str:
        """Resolve slug to URI - subclasses must implement."""
        raise NotImplementedError


def make_autoapi_role(path_pattern: str) -> type[SphinxRole]:
    """Create role that resolves to autoapi page.

    Args:
        path_pattern: Pattern with {slug} placeholder
                      e.g., "autoapi/julee/{slug}/index"

    Returns:
        Role class for registration

    Example:
        BCRole = make_autoapi_role("autoapi/julee/{slug}/index")
        app.add_role("bc", BCRole())
    """

    class AutoapiRole(EntityRefRole):
        """Role resolving to autoapi page."""

        def resolve(self, slug: str) -> str:
            target_doc = path_pattern.format(slug=slug)
            return self.build_uri(target_doc)

    return AutoapiRole


def make_page_role(page_pattern: str) -> type[SphinxRole]:
    """Create role that resolves to dedicated page.

    Args:
        page_pattern: Pattern with {slug} placeholder
                      e.g., "users/personas/{slug}"

    Returns:
        Role class for registration

    Example:
        PersonaRole = make_page_role("users/personas/{slug}")
        app.add_role("persona", PersonaRole())
    """

    class PageRole(EntityRefRole):
        """Role resolving to dedicated page."""

        def resolve(self, slug: str) -> str:
            target_doc = page_pattern.format(slug=slug)
            return self.build_uri(target_doc)

    return PageRole


def make_anchor_role(
    lookup_func: Callable[[str, "Sphinx"], tuple[str, str] | None],
) -> type[SphinxRole]:
    """Create role that resolves to anchor in another page.

    Args:
        lookup_func: Function(slug, app) -> (docname, anchor) or None
                     Called to resolve entity location

    Returns:
        Role class for registration

    Example:
        def lookup_story(slug, app):
            # Find story and return its app page + anchor
            story = get_story(app, slug)
            if story:
                return (f"applications/{story.app_slug}", f"story-{slug}")
            return None

        StoryRole = make_anchor_role(lookup_story)
        app.add_role("story", StoryRole())
    """

    class AnchorRole(EntityRefRole):
        """Role resolving to anchor in another page."""

        def resolve(self, slug: str) -> str:
            location = lookup_func(slug, self.env.app)
            if location:
                docname, anchor = location
                return self.build_uri(docname, anchor)
            # Dangling ref - just return anchor
            return f"#{slug}"

    return AnchorRole


def make_conditional_role(
    lookup_func: Callable[[str, "Sphinx"], str | tuple[str, str] | None],
) -> type[SphinxRole]:
    """Create role that conditionally resolves based on lookup result.

    The lookup function can return:
    - str: Direct target docname (no anchor)
    - tuple[str, str]: (docname, anchor)
    - None: Entity not found (dangling ref)

    This is useful for entities like C4 Container which can map to
    either Application OR BoundedContext depending on the container type.

    Args:
        lookup_func: Function(slug, app) -> docname | (docname, anchor) | None

    Returns:
        Role class for registration
    """

    class ConditionalRole(EntityRefRole):
        """Role with conditional resolution logic."""

        def resolve(self, slug: str) -> str:
            result = lookup_func(slug, self.env.app)
            if result is None:
                return f"#{slug}"
            if isinstance(result, str):
                return self.build_uri(result)
            docname, anchor = result
            return self.build_uri(docname, anchor)

    return ConditionalRole


def make_semantic_role(
    entity_type: type,
    mapping: "DocumentationMapping",
) -> type[SphinxRole]:
    """Create role that resolves using SemanticRelation and DocumentationMapping.

    This factory creates roles that:
    1. Look up the entity type in the DocumentationMapping
    2. Follow PROJECTS relations to find the documentation target
    3. Resolve the slug using the discovered pattern

    Args:
        entity_type: The entity class this role references
        mapping: DocumentationMapping instance for pattern lookup

    Returns:
        Role class for registration

    Example:
        from apps.sphinx.shared.documentation_mapping import get_documentation_mapping
        from julee.supply_chain.entities.accelerator import Accelerator

        mapping = get_documentation_mapping()
        AcceleratorRole = make_semantic_role(Accelerator, mapping)
        app.add_role("accelerator", AcceleratorRole())

        # :accelerator:`slug` resolves to autoapi/julee/{slug}/index
        # because Accelerator PROJECTS BoundedContext
    """
    from apps.sphinx.shared.documentation_mapping import DocumentationMapping

    class SemanticRole(EntityRefRole):
        """Role resolving via SemanticRelation."""

        def resolve(self, slug: str) -> str:
            result = mapping.resolve(entity_type, slug, self.env.app)
            if result is None:
                # No pattern found - return slug as dangling ref
                return f"#{slug}"
            if isinstance(result, tuple):
                # Anchor result
                docname, anchor = result
                return self.build_uri(docname, anchor)
            # Page/autoapi result
            return self.build_uri(result)

    return SemanticRole


__all__ = [
    "EntityRefRole",
    "make_autoapi_role",
    "make_page_role",
    "make_anchor_role",
    "make_conditional_role",
    "make_semantic_role",
]
