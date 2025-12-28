"""Bounded context map directive for solution-level BC overview.

Provides a visual overview of all bounded contexts in the solution,
with grouping by layer (viewpoint, domain, contrib) and optional
dependency visualization.
"""

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.core.context import get_core_context
from apps.sphinx.shared import build_relative_uri


class BoundedContextMapDirective(SphinxDirective):
    """Show bounded context map with grouping and dependencies.

    Usage::

        .. bounded-context-map::
           :show-viewpoints:
           :show-dependencies:
           :group-by-layer:

    Options:
        :show-viewpoints: Highlight HCD, C4 viewpoint bounded contexts
        :show-dependencies: Show inter-BC dependencies via accelerators
        :group-by-layer: Group BCs by layer (viewpoint/domain/contrib)
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    option_spec = {
        "show-viewpoints": directives.flag,
        "show-dependencies": directives.flag,
        "group-by-layer": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)

        show_viewpoints = "show-viewpoints" in self.options
        show_dependencies = "show-dependencies" in self.options
        group_by_layer = "group-by-layer" in self.options

        bounded_contexts = context.list_solution_bounded_contexts()

        if not bounded_contexts:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No bounded contexts found.")
            return [para]

        result = []

        if group_by_layer:
            result.extend(self._render_grouped(bounded_contexts, show_viewpoints))
        else:
            result.extend(self._render_flat(bounded_contexts, show_viewpoints))

        if show_dependencies:
            deps = self._render_dependencies(bounded_contexts)
            if deps:
                result.extend(deps)

        return result

    def _render_grouped(
        self, bounded_contexts: list, show_viewpoints: bool
    ) -> list[nodes.Node]:
        """Render BCs grouped by layer."""
        result = []

        # Group BCs
        viewpoints = [bc for bc in bounded_contexts if bc.is_viewpoint]
        contrib = [bc for bc in bounded_contexts if bc.is_contrib]
        domain = [
            bc
            for bc in bounded_contexts
            if not bc.is_viewpoint and not bc.is_contrib
        ]

        # Viewpoints section
        if viewpoints and show_viewpoints:
            result.append(self._section("Viewpoints", viewpoints, is_viewpoint=True))

        # Domain section
        if domain:
            result.append(self._section("Domain Bounded Contexts", domain))

        # Contrib section
        if contrib:
            result.append(self._section("Contrib Modules", contrib, is_contrib=True))

        return result

    def _render_flat(
        self, bounded_contexts: list, show_viewpoints: bool
    ) -> list[nodes.Node]:
        """Render BCs as a flat list."""
        bullet_list = nodes.bullet_list()

        for bc in sorted(bounded_contexts, key=lambda x: x.slug):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to BC
            uri = build_relative_uri(
                self.env.docname, f"autoapi/julee/{bc.slug}/index"
            )
            ref = nodes.reference("", "", refuri=uri)
            ref += nodes.strong(text=bc.display_name)
            para += ref

            # Add tags
            if bc.is_viewpoint and show_viewpoints:
                para += nodes.Text(" ")
                para += nodes.emphasis(text="[viewpoint]")
            if bc.is_contrib:
                para += nodes.Text(" ")
                para += nodes.emphasis(text="[contrib]")

            # Description
            if bc.description:
                para += nodes.Text(f" - {bc.description}")

            item += para
            bullet_list += item

        return [bullet_list]

    def _section(
        self,
        title: str,
        bcs: list,
        is_viewpoint: bool = False,
        is_contrib: bool = False,
    ) -> nodes.Node:
        """Create a section with a list of BCs."""
        container = nodes.container()

        # Section title
        para = nodes.paragraph()
        para += nodes.strong(text=title)
        container += para

        # BC list
        bullet_list = nodes.bullet_list()

        for bc in sorted(bcs, key=lambda x: x.slug):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to BC
            uri = build_relative_uri(
                self.env.docname, f"autoapi/julee/{bc.slug}/index"
            )
            ref = nodes.reference("", "", refuri=uri)
            ref += nodes.Text(bc.display_name)
            para += ref

            # Description
            if bc.description:
                para += nodes.Text(f" - {bc.description}")

            item += para
            bullet_list += item

        container += bullet_list
        return container

    def _render_dependencies(self, bounded_contexts: list) -> list[nodes.Node]:
        """Render inter-BC dependencies section.

        Dependencies are inferred from accelerator relationships:
        - An accelerator in BC-A that depends on BC-B creates a dependency
        """
        # For now, return empty - dependency extraction requires HCD context
        # which may not be available. This is a placeholder for future work.
        return []
