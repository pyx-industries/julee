"""Placeholder resolution handler for supply_chain Sphinx extension.

Handles accelerator-related placeholder resolution.
"""

from typing import TYPE_CHECKING

from docutils import nodes

if TYPE_CHECKING:
    from sphinx.application import Sphinx

    from apps.sphinx.hcd.context import HCDContext


class AcceleratorPlaceholderHandler:
    """Handler for accelerator-related placeholders."""

    name = "Accelerator"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process accelerator placeholders.

        Args:
            app: Sphinx application
            doctree: Document tree
            docname: Document name
            context: HCD context (for cross-entity queries like apps/integrations)
        """
        from ...directives.accelerator import (
            AcceleratorDependencyDiagramPlaceholder,
            AcceleratorsForAppPlaceholder,
            DefineAcceleratorPlaceholder,
            DependentAcceleratorsPlaceholder,
            build_accelerator_content,
            build_accelerators_for_app,
            build_dependency_diagram,
        )
        from ...generated_directives import GeneratedAcceleratorIndexDirective

        for node in doctree.traverse(DefineAcceleratorPlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_content(slug, docname, context)
            node.replace_self(content)

        # Process accelerator-index using generated directive
        placeholder_cls = GeneratedAcceleratorIndexDirective.placeholder_class
        for node in doctree.traverse(placeholder_cls):
            content = GeneratedAcceleratorIndexDirective.resolve_placeholder(node, app)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorsForAppPlaceholder):
            app_slug = node["app_slug"]
            content = build_accelerators_for_app(app_slug, docname, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorDependencyDiagramPlaceholder):
            content = build_dependency_diagram(docname, context)
            node.replace_self(content)

        for node in doctree.traverse(DependentAcceleratorsPlaceholder):
            # Not yet implemented - render a placeholder message
            para = nodes.paragraph()
            para += nodes.emphasis(text="Dependent accelerators list not yet implemented")
            node.replace_self([para])


class CodeLinksPlaceholderHandler:
    """Handler for code link placeholders."""

    name = "CodeLinks"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process code link placeholders."""
        from ...directives.code_links import (
            AcceleratorCodePlaceholder,
            AcceleratorEntityListPlaceholder,
            AcceleratorUseCaseListPlaceholder,
            build_accelerator_code_links,
            build_accelerator_entity_list,
            build_accelerator_usecase_list,
        )

        for node in doctree.traverse(AcceleratorCodePlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_code_links(slug, docname, app, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorEntityListPlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_entity_list(slug, docname, app, context)
            node.replace_self(content)

        for node in doctree.traverse(AcceleratorUseCaseListPlaceholder):
            slug = node["accelerator_slug"]
            content = build_accelerator_usecase_list(slug, docname, app, context)
            node.replace_self(content)


class EntityDiagramPlaceholderHandler:
    """Handler for entity diagram placeholders."""

    name = "EntityDiagram"

    def handle(
        self,
        app: "Sphinx",
        doctree: nodes.document,
        docname: str,
        context: "HCDContext",
    ) -> None:
        """Process entity diagram placeholders."""
        from ...directives.code_links import (
            EntityDiagramPlaceholder,
            build_entity_diagram,
        )

        for node in doctree.traverse(EntityDiagramPlaceholder):
            slug = node["accelerator_slug"]
            content = build_entity_diagram(slug, docname, context)
            node.replace_self(content)
