"""Bounded Context hub directive.

Shows a BC's contents: use cases (organized by package), apps using it,
and cross-references to personas via HCD stories.

Template-driven pattern:
1. Directive fetches BC info, apps, persona refs
2. Data is passed to bc_hub.rst.jinja template
3. Template renders RST
4. RST is parsed to docutils nodes
"""

from pathlib import Path

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.core.context import get_core_context
from apps.sphinx.directive_factory import parse_rst_to_nodes

from .catalog import _get_jinja_env


class BoundedContextHubDirective(SphinxDirective):
    """Show detailed view of a bounded context's contents.

    Uses template-driven rendering:
    1. Fetches BC info, apps using BC, persona cross-refs
    2. Passes data to bc_hub.rst.jinja template
    3. Template renders RST which is parsed to nodes

    Usage::

        .. bc-hub:: hcd

    Shows:
    - Use cases organized by package/module
    - Apps that use this BC
    - Persona cross-references (if HCD data available)
    """

    required_arguments = 1  # BC slug
    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        bc_slug = self.arguments[0]
        context = get_core_context(self.env.app)

        # Get BC info via introspection
        bc_info = context.get_bounded_context(f"julee.{bc_slug}")

        # Apps using this BC
        apps_using_bc = self._find_apps_using_bc(context, bc_slug) if bc_info else []

        # Persona cross-references (HCD bridge)
        persona_refs = self._get_persona_crossrefs(bc_slug) if bc_info else []

        # Render template
        env = _get_jinja_env()
        template = env.get_template("bc_hub.rst.jinja")
        rst_content = template.render(
            bc_info=bc_info,
            bc_slug=bc_slug,
            apps_using_bc=apps_using_bc,
            persona_crossrefs=persona_refs,
        )

        # Parse RST to nodes
        return parse_rst_to_nodes(rst_content, self.env.docname)

    def _find_apps_using_bc(self, context, bc_slug: str) -> list:
        """Find apps that use this bounded context.

        Detection methods:
        1. App has a subdirectory matching BC slug (BC-organized apps)
        2. App's markers indicate it uses this BC
        """
        apps_using = []
        all_apps = context.list_applications()

        for app in all_apps:
            # Check for BC-organized subdirectory
            app_path = Path(app.path)
            bc_subdir = app_path / bc_slug
            if bc_subdir.exists() and bc_subdir.is_dir():
                apps_using.append(app)
                continue

            # Check if app uses BC organization and has this BC
            if app.markers.uses_bc_organization:
                for subdir in app.bc_subdirs:
                    if subdir == bc_slug:
                        apps_using.append(app)
                        break

        return apps_using

    def _get_persona_crossrefs(self, bc_slug: str) -> list[dict]:
        """Get persona cross-references via HCD bridge using semantic relations.

        Uses RelationTraversal to trace relationships declared on entities:
        BoundedContext ← PROJECTS ← Accelerator ← uses ← App ← PART_OF ← Story → REFERENCES → Persona

        Returns list of dicts with persona, app, story_count info, grouped
        by persona for display in the BC hub template.
        """
        try:
            from apps.sphinx.hcd.context import get_hcd_context
            from apps.sphinx.shared.services.relation_traversal import (
                get_relation_traversal,
            )

            hcd_context = get_hcd_context(self.env.app)
            traversal = get_relation_traversal()
            return traversal.build_bc_persona_crossrefs(bc_slug, hcd_context)
        except (ImportError, AttributeError):
            return []
