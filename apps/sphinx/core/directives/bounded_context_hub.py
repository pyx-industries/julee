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
        """Get persona cross-references via HCD bridge.

        Traces: Persona ← Story → App → Accelerator → BoundedContext

        Returns list of dicts with persona, app, story_count info, grouped
        by persona for display in the BC hub template.
        """
        # Try to get HCD context
        try:
            from apps.sphinx.hcd.context import get_hcd_context
            from julee.hcd.use_cases.crud import (
                ListAppsRequest,
                ListStoriesRequest,
            )

            hcd_context = get_hcd_context(self.env.app)
        except (ImportError, AttributeError):
            return []

        # Step 1: Find apps that use accelerators matching this BC
        apps_response = hcd_context.list_apps.execute_sync(ListAppsRequest())
        apps_using_bc = []

        for app in apps_response.apps:
            # App's accelerators field contains slugs of accelerators it uses
            # An accelerator slug typically matches its BC slug
            if bc_slug in app.accelerators:
                apps_using_bc.append(app)

        if not apps_using_bc:
            return []

        # Step 2: Get stories for those apps, grouped by persona
        persona_data: dict[str, dict[str, int]] = {}  # persona -> {app_slug: count}

        for app in apps_using_bc:
            stories_response = hcd_context.list_stories.execute_sync(
                ListStoriesRequest(app_slug=app.slug)
            )

            for story in stories_response.stories:
                persona = story.persona_normalized or story.persona
                if persona not in persona_data:
                    persona_data[persona] = {}

                if app.slug not in persona_data[persona]:
                    persona_data[persona][app.slug] = 0

                persona_data[persona][app.slug] += 1

        # Step 3: Build cross-reference list for template
        crossrefs = []

        for persona, apps_dict in sorted(persona_data.items()):
            for app_slug, story_count in sorted(apps_dict.items()):
                # Find app name
                app_name = app_slug
                for app in apps_using_bc:
                    if app.slug == app_slug:
                        app_name = app.name
                        break

                crossrefs.append(
                    {
                        "persona": persona,
                        "persona_slug": persona.lower().replace(" ", "-"),
                        "app_slug": app_slug,
                        "app_name": app_name,
                        "story_count": story_count,
                    }
                )

        return crossrefs
