"""Base directive for C4 Sphinx directives.

Provides common functionality for accessing C4 use cases and building nodes.
"""

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from ..context import C4Context, get_c4_context


class C4Directive(SphinxDirective):
    """Base directive for C4 elements.

    Provides common utilities for building docutils nodes and accessing
    C4 use cases via C4Context.
    """

    @property
    def docname(self) -> str:
        """Get the current document name."""
        return self.env.docname

    @property
    def c4_context(self) -> C4Context:
        """Get the C4Context for accessing use cases."""
        return get_c4_context(self.env.app)

    def get_c4_storage(self) -> dict:
        """Get or create C4 storage in Sphinx environment.

        DEPRECATED: Use c4_context and use cases instead.

        Returns:
            Dictionary for storing C4 elements during the build
        """
        if not hasattr(self.env, "c4_storage"):
            self.env.c4_storage = {
                "software_systems": {},
                "containers": {},
                "components": {},
                "relationships": {},
                "deployment_nodes": {},
                "dynamic_steps": {},
            }
        return self.env.c4_storage

    def empty_result(self, message: str) -> list[nodes.Node]:
        """Create an emphasized message for empty results."""
        para = nodes.paragraph()
        para += nodes.emphasis(text=message)
        return [para]

    def warning_node(self, message: str) -> nodes.paragraph:
        """Create a warning paragraph."""
        para = nodes.paragraph()
        para += nodes.problematic(text=f"[{message}]")
        return para

    def make_title(self, text: str, level: int = 2) -> nodes.title:
        """Create a title node.

        Args:
            text: Title text
            level: Heading level (1-6)

        Returns:
            Title node
        """
        return nodes.title(text=text)

    def make_paragraph(self, text: str) -> nodes.paragraph:
        """Create a paragraph node.

        Args:
            text: Paragraph text

        Returns:
            Paragraph node
        """
        para = nodes.paragraph()
        para += nodes.Text(text)
        return para

    def make_field(self, name: str, value: str) -> nodes.paragraph:
        """Create a field paragraph with bold name.

        Args:
            name: Field name
            value: Field value

        Returns:
            Paragraph node with bold name
        """
        para = nodes.paragraph()
        para += nodes.strong(text=f"{name}: ")
        para += nodes.Text(value)
        return para
