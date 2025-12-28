"""Placeholder resolution handler protocol for sphinx_hcd.

Defines the interface for handlers that resolve placeholder nodes
in the doctree during the doctree-resolved phase.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from docutils import nodes

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from ..context import HCDContext


@runtime_checkable
class PlaceholderResolutionHandler(Protocol):
    """Handler for resolving placeholder nodes in doctree.

    Each handler is responsible for finding and replacing placeholder
    nodes of a specific type with rendered content.

    Implementations should:
    1. Find all placeholder nodes of their type in the doctree
    2. Build replacement nodes using HCDContext repositories
    3. Replace placeholder nodes with the built content
    """

    @property
    def name(self) -> str:
        """Handler name for logging and debugging."""
        ...

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Resolve all placeholders of this type in doctree.

        Args:
            app: Sphinx application instance
            doctree: The document tree to process
            docname: The document name
            context: HCD context with repositories
        """
        ...


class BasePlaceholderHandler:
    """Base class for placeholder resolution handlers.

    Provides common functionality for traversing doctrees and
    replacing placeholder nodes.
    """

    placeholder_class: type[nodes.Element]

    @property
    def name(self) -> str:
        """Handler name derived from placeholder class."""
        return self.placeholder_class.__name__.replace("Placeholder", "")

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Find and replace all placeholder nodes."""
        for node in doctree.traverse(self.placeholder_class):
            replacement = self.build_replacement(app, node, docname, context)
            node.replace_self(replacement)

    def build_replacement(
        self,
        app: "Sphinx",
        node: nodes.Element,
        docname: str,
        context: "HCDContext",
    ) -> list[nodes.Node]:
        """Build replacement nodes for a placeholder.

        Subclasses must implement this method.

        Args:
            app: Sphinx application instance
            node: The placeholder node to replace
            docname: The document name
            context: HCD context with repositories

        Returns:
            List of nodes to replace the placeholder with
        """
        raise NotImplementedError
