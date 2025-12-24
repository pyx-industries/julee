"""Use case documentation directive for embedding in docstrings.

This directive generates a sequence diagram (SSD) for a use case class
and can be placed directly in the class's docstring to be rendered by autodoc.

Usage in a docstring::

    class CreateAcceleratorUseCase:
        '''Use case for creating an accelerator.

        .. usecase-documentation:: julee.hcd.domain.use_cases:CreateAcceleratorUseCase

        This creates accelerators in the repository.
        '''
"""

import os

from docutils import nodes
from sphinx.util.docutils import SphinxDirective


class UseCaseDocumentationDirective(SphinxDirective):
    """Directive to embed use case sequence diagram in docstrings.

    Usage::

        .. usecase-documentation:: module.path:ClassName

    The argument is the full module path to the use case class in the format
    ``module.path:ClassName``.
    """

    required_arguments = 1  # module:ClassName
    optional_arguments = 0
    has_content = False
    option_spec = {}

    def run(self) -> list[nodes.Node]:
        """Generate the sequence diagram node."""
        module_class_path = self.arguments[0]

        try:
            from sphinxcontrib.plantuml import plantuml
        except ImportError:
            error = self.state_machine.reporter.error(
                "sphinxcontrib-plantuml is required for usecase-documentation",
                line=self.lineno,
            )
            return [error]

        try:
            from julee.shared.introspection import (
                introspect_use_case,
                resolve_use_case_class,
            )
            from julee.shared.templates import render_ssd

            # Resolve and introspect the use case
            use_case_cls = resolve_use_case_class(module_class_path)
            metadata = introspect_use_case(use_case_cls)
            puml_source = render_ssd(metadata)

            # Create PlantUML node
            node = plantuml(puml_source)
            node["uml"] = puml_source
            node["incdir"] = os.path.dirname(self.env.docname)
            node["filename"] = os.path.basename(self.env.docname)

            return [node]

        except Exception as e:
            # Create a warning node instead of failing the build
            warning = nodes.warning()
            warning_para = nodes.paragraph()
            warning_para += nodes.Text(
                f"Could not generate sequence diagram for {module_class_path}: {e}"
            )
            warning += warning_para
            return [warning]
