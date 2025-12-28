"""Bounded Context hub directive.

Shows a BC's contents: use cases (organized by package), apps using it,
and cross-references to personas via HCD stories.
"""

from collections import defaultdict
from pathlib import Path

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.core.context import get_core_context


class BoundedContextHubDirective(SphinxDirective):
    """Show detailed view of a bounded context's contents.

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

        if bc_info is None:
            para = nodes.paragraph()
            para += nodes.emphasis(text=f"Bounded context '{bc_slug}' not found.")
            return [para]

        result_nodes = []

        # Use Cases section (organized by package)
        if bc_info.use_cases:
            result_nodes.extend(self._render_use_cases(bc_info))

        # Apps using this BC
        apps_using_bc = self._find_apps_using_bc(context, bc_slug)
        if apps_using_bc:
            result_nodes.extend(self._render_apps(apps_using_bc))

        # Persona cross-references (HCD bridge)
        persona_refs = self._get_persona_crossrefs(bc_slug)
        if persona_refs:
            result_nodes.extend(self._render_persona_crossrefs(persona_refs))

        if not result_nodes:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No contents discovered for this bounded context.")
            return [para]

        return result_nodes

    def _render_use_cases(self, bc_info) -> list[nodes.Node]:
        """Render use cases organized by package."""
        result = []

        # Section heading
        heading = nodes.rubric(text="Use Cases")
        result.append(heading)

        # Group use cases by file (package)
        by_package = defaultdict(list)
        for uc in bc_info.use_cases:
            # Extract package from file path (e.g., use_cases/crud.py -> crud)
            if uc.file:
                package = Path(uc.file).stem
            else:
                package = "other"
            by_package[package].append(uc)

        # Render each package
        for package in sorted(by_package.keys()):
            use_cases = by_package[package]

            # Package subheading
            pkg_para = nodes.paragraph()
            pkg_para += nodes.strong(text=package)
            result.append(pkg_para)

            # Use case list
            ul = nodes.bullet_list()
            for uc in sorted(use_cases, key=lambda x: x.name):
                item = nodes.list_item()
                para = nodes.paragraph()

                # Use case name
                para += nodes.literal(text=uc.name)

                # First line of docstring as description
                if uc.docstring:
                    first_line = uc.docstring.split("\n")[0].strip()
                    if first_line:
                        para += nodes.Text(f" — {first_line}")

                item += para
                ul += item

            result.append(ul)

        return result

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

    def _render_apps(self, apps) -> list[nodes.Node]:
        """Render apps using this BC."""
        result = []

        heading = nodes.rubric(text="Applications Using This BC")
        result.append(heading)

        ul = nodes.bullet_list()
        for app in sorted(apps, key=lambda x: x.slug):
            item = nodes.list_item()
            para = nodes.paragraph()
            para += nodes.strong(text=app.slug)
            para += nodes.Text(f" [{app.app_type.value}]")
            if app.description:
                para += nodes.Text(f" — {app.description}")
            item += para
            ul += item

        result.append(ul)
        return result

    def _get_persona_crossrefs(self, bc_slug: str) -> list[dict]:
        """Get persona cross-references via HCD bridge.

        Traces: Persona → Story → Feature → App → UseCase

        Returns list of dicts with persona, story, app, use_case info.
        """
        # Try to get HCD context
        try:
            from apps.sphinx.hcd.context import get_hcd_context

            hcd_context = get_hcd_context(self.env.app)
        except (ImportError, AttributeError):
            return []

        # This requires HCD data to be loaded
        # For now, return empty - will implement when HCD bridge is ready
        # The implementation would:
        # 1. List all stories
        # 2. For each story, check if it references use cases in this BC
        # 3. Get the persona from the story
        # 4. Build the cross-reference chain

        return []

    def _render_persona_crossrefs(self, crossrefs: list[dict]) -> list[nodes.Node]:
        """Render persona cross-references."""
        result = []

        heading = nodes.rubric(text="Personas")
        result.append(heading)

        intro = nodes.paragraph()
        intro += nodes.Text(
            "Use cases in this bounded context are exposed to these personas:"
        )
        result.append(intro)

        # Group by persona
        by_persona = defaultdict(list)
        for ref in crossrefs:
            by_persona[ref["persona"]].append(ref)

        dl = nodes.definition_list()
        for persona in sorted(by_persona.keys()):
            refs = by_persona[persona]

            item = nodes.definition_list_item()
            term = nodes.term()
            term += nodes.strong(text=persona)
            item += term

            definition = nodes.definition()
            for ref in refs:
                ref_para = nodes.paragraph()
                ref_para += nodes.Text(f"via ")
                ref_para += nodes.emphasis(text=ref["story"])
                ref_para += nodes.Text(f" on ")
                ref_para += nodes.literal(text=ref["app"])
                ref_para += nodes.Text(f" → ")
                ref_para += nodes.literal(text=ref["use_case"])
                definition += ref_para

            item += definition
            dl += item

        result.append(dl)
        return result
