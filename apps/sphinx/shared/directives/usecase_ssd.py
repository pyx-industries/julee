"""Use Case System Sequence Diagram directive.

Generates PlantUML sequence diagrams from use case class introspection.
Domain-agnostic - works with any use case following the standard pattern.
"""

import os

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class UseCaseSSDDirective(SphinxDirective):
    """Generate a sequence diagram for a use case.

    Usage::

        .. usecase-ssd:: julee.hcd.domain.use_cases:CreateAcceleratorUseCase
           :title: Create Accelerator Flow

    The directive introspects the use case class to extract:
    - Constructor dependencies (repositories, services)
    - Execute method signature (request/response types)
    - Repository/service method calls via AST analysis

    Then generates a PlantUML sequence diagram showing the interaction flow.
    """

    required_arguments = 1  # module:ClassName
    optional_arguments = 0
    has_content = False
    final_argument_whitespace = False

    option_spec = {
        "title": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        module_class_path = self.arguments[0]
        title = self.options.get("title", "")

        try:
            # 1. Resolve class from module:ClassName
            from julee.core.introspection import (
                introspect_use_case,
                resolve_use_case_class,
            )

            use_case_cls = resolve_use_case_class(module_class_path)

            # 2. Introspect
            metadata = introspect_use_case(use_case_cls)

            # 3. Generate PlantUML via Jinja template
            from julee.core.templates.rendering import render_ssd

            puml_source = render_ssd(metadata, title=title)

            # 4. Create plantuml node
            return [self._make_plantuml_node(puml_source)]

        except Exception as e:
            # Return error message as problematic node
            para = nodes.paragraph()
            para += nodes.problematic(text=f"Error generating SSD for {module_class_path}: {e}")
            return [para]

    def _make_plantuml_node(self, puml_source: str) -> nodes.Node:
        """Create a PlantUML node or fallback to literal block.

        Args:
            puml_source: PlantUML source code

        Returns:
            PlantUML node or literal block if extension not available
        """
        try:
            from sphinxcontrib.plantuml import plantuml

            node = plantuml(puml_source)
            node["uml"] = puml_source
            # Required by sphinxcontrib.plantuml for rendering
            node["incdir"] = os.path.dirname(self.env.docname)
            node["filename"] = os.path.basename(self.env.docname)
            return node
        except ImportError:
            # Fallback to literal block if PlantUML not available
            return nodes.literal_block(puml_source, puml_source)
