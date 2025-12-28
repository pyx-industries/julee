"""App directives for sphinx_hcd.

Provides directives for rendering application information:
- define-app: Render app info from YAML manifest + derived data
- app-index: Generate index tables grouped by type
- apps-for-persona: List apps for a persona
"""

from docutils import nodes
from docutils.parsers.rst import directives

from apps.sphinx.shared import path_to_root
from julee.hcd.entities.app import App, AppInterface, AppType
from julee.hcd.use_cases.crud import (
    CreateAppRequest,
    GetAppRequest,
    ListAppsRequest,
    ListEpicsRequest,
    ListJourneysRequest,
    ListStoriesRequest,
    UpdateAppRequest,
)
from julee.hcd.use_cases.resolve_app_references import (
    get_epics_for_app,
    get_journeys_for_app,
    get_personas_for_app,
    get_stories_for_app,
)
from julee.hcd.utils import normalize_name, parse_csv_option, slugify

from ..node_builders import (
    empty_result_paragraph,
    entity_bullet_list,
    grouped_bullet_lists,
    link_list_paragraph,
    metadata_paragraph,
    problematic_paragraph,
)
from .base import HCDDirective


class DefineAppPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for define-app, replaced at doctree-resolved."""

    pass


class AppsForPersonaPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for apps-for-persona, replaced at doctree-resolved."""

    pass


class DefineAppDirective(HCDDirective):
    """Define an app with metadata for C4 mapping.

    Usage::

        .. define-app:: sphinx-hcd
           :interface: sphinx
           :technology: Python/Sphinx
           :accelerators: hcd

           Human-Centered Design documentation extension for Sphinx.

    If app already exists from YAML manifest, updates it with directive fields.
    Otherwise creates a new app entry.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "type": directives.unchanged,
        "status": directives.unchanged,
        "interface": directives.unchanged,
        "technology": directives.unchanged,
        "accelerators": directives.unchanged,
    }

    def run(self):
        app_slug = self.arguments[0]
        docname = self.env.docname

        # Parse options
        app_type_str = self.options.get("type", "").strip()
        status = self.options.get("status", "").strip() or None
        interface_str = self.options.get("interface", "").strip()
        technology = self.options.get("technology", "").strip()
        accelerators = parse_csv_option(self.options.get("accelerators", ""))
        description = "\n".join(self.content).strip()

        # Get existing app from YAML manifest (if any)
        app_response = self.hcd_context.get_app.execute_sync(
            GetAppRequest(slug=app_slug)
        )
        existing_app = app_response.app

        if existing_app:
            # Update existing app with directive fields via use case
            update_request = UpdateAppRequest(
                slug=app_slug,
                interface=AppInterface.from_string(interface_str) if interface_str else None,
                technology=technology if technology else None,
                accelerators=accelerators if accelerators else None,
                description=description if description else None,
                status=status if status else None,
                docname=docname,
            )
            self.hcd_context.update_app.execute_sync(update_request)
        else:
            # Create new app from directive via use case
            create_request = CreateAppRequest(
                slug=app_slug,
                name=app_slug.replace("-", " ").title(),
                app_type=AppType.from_string(app_type_str) if app_type_str else AppType.UNKNOWN,
                status=status,
                description=description,
                accelerators=accelerators,
                interface=AppInterface.from_string(interface_str) if interface_str else AppInterface.UNKNOWN,
                technology=technology,
                docname=docname,
                solution_slug=self.solution_slug,
            )
            self.hcd_context.create_app.execute_sync(create_request)

        # Track documented apps in environment (for validation)
        if not hasattr(self.env, "documented_apps"):
            self.env.documented_apps = set()
        self.env.documented_apps.add(app_slug)

        # Return placeholder - rendering in doctree-resolved
        node = DefineAppPlaceholder()
        node["app_slug"] = app_slug
        return [node]


class AppsForPersonaDirective(HCDDirective):
    """List apps for a specific persona.

    Usage::

        .. apps-for-persona:: Member Implementer
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        node = AppsForPersonaPlaceholder()
        node["persona"] = self.arguments[0]
        return [node]


def build_app_content(app_slug: str, docname: str, hcd_context):
    """Build the content nodes for an app."""
    from sphinx.addnodes import seealso

    from ..config import get_config
    from ..node_builders import make_link

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)

    # Get app via use case
    app_response = hcd_context.get_app.execute_sync(GetAppRequest(slug=app_slug))
    app = app_response.app
    if not app:
        return [problematic_paragraph(f"App '{app_slug}' not found in apps/")]

    # Get all entities for cross-references via use cases
    stories_response = hcd_context.list_stories.execute_sync(
        ListStoriesRequest(solution_slug=solution)
    )
    epics_response = hcd_context.list_epics.execute_sync(
        ListEpicsRequest(solution_slug=solution)
    )
    journeys_response = hcd_context.list_journeys.execute_sync(
        ListJourneysRequest(solution_slug=solution)
    )
    all_stories = stories_response.stories
    all_epics = epics_response.epics
    all_journeys = journeys_response.journeys

    result_nodes = []

    # Description first - parse as RST for formatting support
    if app.description:
        from .base import parse_rst_content

        desc_nodes = parse_rst_content(app.description, f"<{app.slug}>")
        result_nodes.extend(desc_nodes)

    # Stories count and link
    app_stories = get_stories_for_app(app, all_stories)

    if app_stories:
        story_count = len(app_stories)
        stories_para = nodes.paragraph()
        stories_para += nodes.Text(f"The {app.name} has ")
        story_path = f"{prefix}{config.get_doc_path('stories')}/{app_slug}.html"
        stories_para += make_link(story_path, f"{story_count} stories")
        stories_para += nodes.Text(".")
        result_nodes.append(stories_para)

    # Build seealso box with metadata
    seealso_node = seealso()

    seealso_node += metadata_paragraph("Type", app.type_label)

    if app.status:
        seealso_node += metadata_paragraph("Status", app.status)

    # Personas (derived from stories)
    personas = get_personas_for_app(app, all_stories, all_epics)
    if personas:
        seealso_node += link_list_paragraph(
            "Personas",
            personas,
            lambda p: (
                f"{prefix}{config.get_doc_path('personas')}/{slugify(p.name)}.html",
                p.name,
            ),
        )

    # Related Journeys
    journeys = get_journeys_for_app(app, all_stories, all_journeys)
    if journeys:
        seealso_node += link_list_paragraph(
            "Journeys",
            journeys,
            lambda j: (
                f"{prefix}{config.get_doc_path('journeys')}/{j.slug}.html",
                j.slug.replace("-", " ").title(),
            ),
        )

    # Related Epics
    epics = get_epics_for_app(app, all_stories, all_epics)
    if epics:
        seealso_node += link_list_paragraph(
            "Epics",
            epics,
            lambda e: (
                f"{prefix}{config.get_doc_path('epics')}/{e.slug}.html",
                e.slug.replace("-", " ").title(),
            ),
        )

    result_nodes.append(seealso_node)

    return result_nodes


def build_app_index(docname: str, hcd_context):
    """Build the app index grouped by interface."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    apps_response = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    )
    all_apps = apps_response.apps

    if not all_apps:
        return [empty_result_paragraph("No apps defined")]

    # Group apps by interface
    by_interface: dict[AppInterface, list[App]] = {}
    for app in all_apps:
        by_interface.setdefault(app.interface, []).append(app)

    # Sort entities within each group
    for interface in by_interface:
        by_interface[interface] = sorted(by_interface[interface], key=lambda a: a.name)

    # Define interface sections with labels
    interface_sections = [
        (AppInterface.SPHINX, "Documentation Extensions"),
        (AppInterface.API, "REST APIs"),
        (AppInterface.MCP, "MCP Servers"),
        (AppInterface.WEB, "Web Applications"),
        (AppInterface.CLI, "CLI Tools"),
        (AppInterface.UNKNOWN, "Other Applications"),
    ]

    def get_suffix(app: App) -> str | None:
        if app.technology:
            return f" — {app.technology}"
        return None

    def get_desc(app: App) -> str | None:
        if app.description:
            desc = app.description.split(".")[0] + "."
            if len(desc) > 80:
                desc = desc[:77] + "..."
            return desc
        return None

    return grouped_bullet_lists(
        by_interface,
        interface_sections,
        link_fn=lambda a: (f"{a.slug}.html", a.name),
        suffix_fn=get_suffix,
        desc_fn=get_desc,
    )


def build_apps_for_persona(docname: str, persona_arg: str, hcd_context):
    """Build list of apps for a persona."""
    from julee.hcd.use_cases.derive_personas import (
        derive_personas,
        get_apps_for_persona,
    )

    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)
    persona_normalized = normalize_name(persona_arg)

    # Get entities via use cases
    apps_response = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    )
    stories_response = hcd_context.list_stories.execute_sync(
        ListStoriesRequest(solution_slug=solution)
    )
    epics_response = hcd_context.list_epics.execute_sync(
        ListEpicsRequest(solution_slug=solution)
    )
    all_apps = apps_response.apps
    all_stories = stories_response.stories
    all_epics = epics_response.epics

    # Derive personas
    personas = derive_personas(all_stories, all_epics)

    # Find the persona
    persona = None
    for p in personas:
        if p.normalized_name == persona_normalized:
            persona = p
            break

    if not persona:
        return [empty_result_paragraph(f"No apps found for persona '{persona_arg}'")]

    # Get apps for this persona
    matching_apps = get_apps_for_persona(persona, all_apps)

    if not matching_apps:
        return [empty_result_paragraph(f"No apps found for persona '{persona_arg}'")]

    return [
        entity_bullet_list(
            sorted(matching_apps, key=lambda a: a.name),
            link_fn=lambda a: (
                f"{prefix}{config.get_doc_path('applications')}/{a.slug}.html",
                a.name,
            ),
        )
    ]


def process_app_placeholders(app, doctree, docname):
    """Replace app placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    # Process define-app placeholders
    for node in doctree.traverse(DefineAppPlaceholder):
        app_slug = node["app_slug"]
        content = build_app_content(app_slug, docname, hcd_context)
        node.replace_self(content)

    # Process app-index placeholders
    for node in doctree.traverse(AppIndexPlaceholder):
        content = build_app_index(docname, hcd_context)
        node.replace_self(content)

    # Process apps-for-persona placeholders
    for node in doctree.traverse(AppsForPersonaPlaceholder):
        persona = node["persona"]
        content = build_apps_for_persona(docname, persona, hcd_context)
        node.replace_self(content)
