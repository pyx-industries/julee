"""EntityLinkBuilder service for creating documentation links.

Uses SemanticRelation and DocumentationMapping to build links to entity
documentation pages, eliminating hardcoded path constructions.

Example:
    link_builder = EntityLinkBuilder(mapping)

    # Build a link to a Persona page
    link = link_builder.build_link(Persona, "doc-writer", prefix="../")
    # Returns: "../users/personas/doc-writer.html"

    # Build a docutils node
    node = link_builder.build_node(Persona, "doc-writer", "Doc Writer", prefix)
"""

from typing import TYPE_CHECKING

from docutils import nodes

if TYPE_CHECKING:
    from apps.sphinx.shared.documentation_mapping import DocumentationMapping


class EntityLinkBuilder:
    """Build documentation links using SemanticRelation.

    Centralizes link generation for entity types, using DocumentationMapping
    to resolve entity types to documentation patterns via semantic relations.
    """

    def __init__(self, mapping: "DocumentationMapping"):
        """Initialize the link builder.

        Args:
            mapping: DocumentationMapping instance for pattern resolution
        """
        self.mapping = mapping

    def build_link(
        self,
        entity_type: type,
        slug: str,
        prefix: str = "",
        anchor: str | None = None,
    ) -> str:
        """Build documentation URL for an entity.

        Uses DocumentationMapping to resolve the entity type to a pattern,
        following PROJECTS relations if needed.

        Args:
            entity_type: The entity class (e.g., Persona, Accelerator)
            slug: Entity slug
            prefix: Path prefix (e.g., "../" for relative navigation)
            anchor: Optional anchor within the page

        Returns:
            URL string (e.g., "../users/personas/doc-writer.html")
        """
        result = self.mapping.resolve(entity_type, slug)

        if result is None:
            # No pattern found - return dangling anchor
            return f"#{slug}"

        if isinstance(result, tuple):
            # Anchor-based pattern (docname, anchor)
            docname, result_anchor = result
            url = f"{prefix}{docname}.html"
            if result_anchor:
                url = f"{url}#{result_anchor}"
            return url

        # Page/autoapi pattern - result is docname
        url = f"{prefix}{result}.html"
        if anchor:
            url = f"{url}#{anchor}"
        return url

    def build_node(
        self,
        entity_type: type,
        slug: str,
        title: str | None = None,
        prefix: str = "",
        anchor: str | None = None,
        strong: bool = False,
    ) -> nodes.reference:
        """Create a docutils reference node for an entity.

        Args:
            entity_type: The entity class
            slug: Entity slug
            title: Display text (defaults to titlecased slug)
            prefix: Path prefix for relative navigation
            anchor: Optional anchor within the page
            strong: Whether to make text bold

        Returns:
            docutils reference node
        """
        url = self.build_link(entity_type, slug, prefix, anchor)
        display_title = title or slug.replace("-", " ").replace("_", " ").title()

        ref = nodes.reference("", "", refuri=url)
        if strong:
            ref += nodes.strong(text=display_title)
        else:
            ref += nodes.Text(display_title)
        return ref

    def build_entity_node(
        self,
        entity,
        prefix: str = "",
        title_attr: str = "name",
        slug_attr: str = "slug",
        strong: bool = False,
    ) -> nodes.reference:
        """Create a reference node from an entity instance.

        Extracts type, slug, and title from the entity automatically.

        Args:
            entity: Entity instance (e.g., Persona, Story)
            prefix: Path prefix
            title_attr: Attribute name for display title
            slug_attr: Attribute name for slug
            strong: Whether to make text bold

        Returns:
            docutils reference node
        """
        entity_type = type(entity)
        slug = getattr(entity, slug_attr, str(entity))
        title = getattr(entity, title_attr, None)

        return self.build_node(entity_type, slug, title, prefix, strong=strong)


# Convenience function to get a configured builder
def get_entity_link_builder() -> EntityLinkBuilder:
    """Get an EntityLinkBuilder with the global DocumentationMapping.

    Returns:
        Configured EntityLinkBuilder
    """
    from apps.sphinx.shared.documentation_mapping import get_documentation_mapping

    return EntityLinkBuilder(get_documentation_mapping())
