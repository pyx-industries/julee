"""Generic placeholder infrastructure for sphinx_hcd.

Provides a base placeholder class and registry for centralized
placeholder resolution during the doctree-resolved phase.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from docutils import nodes

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from ..context import HCDContext

# Type for builder functions
BuilderFn = Callable[["Sphinx", nodes.Element, str, "HCDContext"], list[nodes.Node]]


class HCDPlaceholder(nodes.General, nodes.Element):
    """Base placeholder node for deferred resolution.

    All HCD placeholder nodes inherit from this class. Placeholders
    are created during directive parsing and replaced with actual
    content during the doctree-resolved phase.

    Attributes stored on the node (via node["key"] = value) are
    preserved and available during resolution.

    Example:
        class MyPlaceholder(HCDPlaceholder):
            '''Placeholder for my directive.'''
            pass

        # In directive.run():
        node = MyPlaceholder()
        node["entity_slug"] = self.arguments[0]
        return [node]

        # Register builder:
        PlaceholderRegistry.register(MyPlaceholder, build_my_content)
    """

    pass


class PlaceholderRegistry:
    """Registry mapping placeholder classes to builder functions.

    Provides centralized registration and resolution of placeholders.
    Builder functions receive (app, node, docname, context) and return
    a list of replacement nodes.

    Example:
        # Register a builder
        PlaceholderRegistry.register(
            MyPlaceholder,
            lambda app, node, docname, ctx: build_content(node["slug"], docname, ctx)
        )

        # Process all registered placeholders
        PlaceholderRegistry.process_all(app, doctree, docname, context)
    """

    _registry: dict[type[HCDPlaceholder], BuilderFn] = {}

    @classmethod
    def register(
        cls,
        placeholder_class: type[HCDPlaceholder],
        builder_fn: BuilderFn,
    ) -> None:
        """Register a builder function for a placeholder type.

        Args:
            placeholder_class: The placeholder node class
            builder_fn: Function that builds replacement nodes
        """
        cls._registry[placeholder_class] = builder_fn

    @classmethod
    def unregister(cls, placeholder_class: type[HCDPlaceholder]) -> None:
        """Remove a placeholder from the registry.

        Args:
            placeholder_class: The placeholder node class to remove
        """
        cls._registry.pop(placeholder_class, None)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered placeholders."""
        cls._registry.clear()

    @classmethod
    def get_builder(
        cls, placeholder_class: type[HCDPlaceholder]
    ) -> BuilderFn | None:
        """Get the builder function for a placeholder type.

        Args:
            placeholder_class: The placeholder node class

        Returns:
            Builder function or None if not registered
        """
        return cls._registry.get(placeholder_class)

    @classmethod
    def is_registered(cls, placeholder_class: type[HCDPlaceholder]) -> bool:
        """Check if a placeholder type is registered.

        Args:
            placeholder_class: The placeholder node class

        Returns:
            True if registered
        """
        return placeholder_class in cls._registry

    @classmethod
    def registered_types(cls) -> list[type[HCDPlaceholder]]:
        """Get all registered placeholder types.

        Returns:
            List of registered placeholder classes
        """
        return list(cls._registry.keys())

    @classmethod
    def process_all(
        cls,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> int:
        """Process all registered placeholders in the doctree.

        Args:
            app: Sphinx application instance
            doctree: The document tree
            docname: The document name
            context: HCD context with repositories

        Returns:
            Number of placeholders resolved
        """
        count = 0
        for placeholder_class, builder_fn in cls._registry.items():
            for node in doctree.traverse(placeholder_class):
                try:
                    replacement = builder_fn(app, node, docname, context)
                    node.replace_self(replacement)
                    count += 1
                except Exception as e:
                    # Log error but continue processing
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Error resolving {placeholder_class.__name__} in {docname}: {e}"
                    )
        return count


def register_placeholder(
    placeholder_class: type[HCDPlaceholder],
) -> Callable[[BuilderFn], BuilderFn]:
    """Decorator to register a builder function for a placeholder.

    Example:
        @register_placeholder(MyPlaceholder)
        def build_my_content(app, node, docname, context):
            return [nodes.paragraph(text="Hello")]

    Args:
        placeholder_class: The placeholder node class

    Returns:
        Decorator function
    """

    def decorator(builder_fn: BuilderFn) -> BuilderFn:
        PlaceholderRegistry.register(placeholder_class, builder_fn)
        return builder_fn

    return decorator
