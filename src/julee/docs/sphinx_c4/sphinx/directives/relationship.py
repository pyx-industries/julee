"""Relationship directive for C4 Sphinx integration.

Provides the define-relationship directive.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from ...domain.models.relationship import ElementType, Relationship
from .base import C4Directive


class DefineRelationshipDirective(C4Directive):
    """Define a relationship between C4 elements.

    Usage::

        .. define-relationship::
           :from: person:customer
           :to: system:banking-system
           :description: Views balances, makes payments
           :technology: HTTPS

        .. define-relationship::
           :from: container:api-app
           :to: container:database
           :description: Reads/writes data
           :technology: SQL/TCP
    """

    has_content = False
    option_spec = {
        "from": directives.unchanged_required,
        "to": directives.unchanged_required,
        "description": directives.unchanged,
        "technology": directives.unchanged,
        "bidirectional": directives.flag,
        "tags": directives.unchanged,
    }

    def _parse_element_ref(self, ref: str) -> tuple[ElementType, str]:
        """Parse element reference like 'person:customer' or 'system:banking'.

        Args:
            ref: Element reference string

        Returns:
            Tuple of (ElementType, slug)
        """
        if ":" in ref:
            type_str, slug = ref.split(":", 1)
            type_map = {
                "person": ElementType.PERSON,
                "system": ElementType.SOFTWARE_SYSTEM,
                "container": ElementType.CONTAINER,
                "component": ElementType.COMPONENT,
            }
            return type_map.get(type_str.lower(), ElementType.SOFTWARE_SYSTEM), slug
        return ElementType.SOFTWARE_SYSTEM, ref

    def run(self) -> list[nodes.Node]:
        from_ref = self.options.get("from", "")
        to_ref = self.options.get("to", "")
        description = self.options.get("description", "Uses")
        technology = self.options.get("technology", "")
        bidirectional = "bidirectional" in self.options
        tags_str = self.options.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        source_type, source_slug = self._parse_element_ref(from_ref)
        dest_type, dest_slug = self._parse_element_ref(to_ref)

        # Generate slug
        slug = f"{source_slug}-to-{dest_slug}"

        # Create relationship
        relationship = Relationship(
            slug=slug,
            source_type=source_type,
            source_slug=source_slug,
            destination_type=dest_type,
            destination_slug=dest_slug,
            description=description,
            technology=technology,
            bidirectional=bidirectional,
            tags=tags,
            docname=self.docname,
        )

        # Store in environment
        storage = self.get_c4_storage()
        storage["relationships"][slug] = relationship

        # Build output nodes - minimal inline display
        result_nodes = []

        para = nodes.paragraph()
        para += nodes.strong(text=f"{source_slug}")
        if bidirectional:
            para += nodes.Text(" <-> ")
        else:
            para += nodes.Text(" -> ")
        para += nodes.strong(text=f"{dest_slug}")
        para += nodes.Text(f": {description}")
        if technology:
            para += nodes.Text(f" [{technology}]")

        result_nodes.append(para)
        return result_nodes
