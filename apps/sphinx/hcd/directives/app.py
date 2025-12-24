"""App directives for sphinx_hcd.

Provides directives for rendering application information:
- define-app: Render app info from YAML manifest + derived data
- app-index: Generate index tables grouped by type
- apps-for-persona: List apps for a persona
"""

from docutils import nodes
from docutils.parsers.rst import directives

from julee.hcd.domain.models.app import App, AppInterface, AppType
from julee.hcd.domain.use_cases import (
    get_epics_for_app,
    get_journeys_for_app,
    get_personas_for_app,
    get_stories_for_app,
)
from julee.hcd.utils import normalize_name, parse_csv_option, slugify
from apps.sphinx.shared import path_to_root
from .base import HCDDirective


class DefineAppPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for define-app, replaced at doctree-resolved."""

    pass


class AppIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for app-index, replaced at doctree-resolved."""

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
        existing_app = self.hcd_context.app_repo.get(app_slug)

        if existing_app:
            # Update existing app with directive fields
            update_data = {}
            if interface_str:
                update_data["interface"] = AppInterface.from_string(interface_str)
            if technology:
                update_data["technology"] = technology
            if accelerators:
                update_data["accelerators"] = accelerators
            if description:
                update_data["description"] = description
            if status:
                update_data["status"] = status
            update_data["docname"] = docname

            if update_data:
                updated = existing_app.model_copy(update=update_data)
                self.hcd_context.app_repo.save(updated)
        else:
            # Create new app from directive
            app = App(
                slug=app_slug,
                name=app_slug.replace("-", " ").title(),
                app_type=AppType.from_string(app_type_str) if app_type_str else AppType.UNKNOWN,
                status=status,
                description=description,
                accelerators=accelerators,
                interface=AppInterface.from_string(interface_str) if interface_str else AppInterface.UNKNOWN,
                technology=technology,
                docname=docname,
            )
            self.hcd_context.app_repo.save(app)

        # Track documented apps in environment (for validation)
        if not hasattr(self.env, "documented_apps"):
            self.env.documented_apps = set()
        self.env.documented_apps.add(app_slug)

        # Return placeholder - rendering in doctree-resolved
        node = DefineAppPlaceholder()
        node["app_slug"] = app_slug
        return [node]


class AppIndexDirective(HCDDirective):
    """Generate index tables grouped by app type.

    Usage::

        .. app-index::
    """

    def run(self):
        node = AppIndexPlaceholder()
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

    config = get_config()
    prefix = path_to_root(docname)

    # Get app from repository
    app = hcd_context.app_repo.get(app_slug)
    if not app:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"App '{app_slug}' not found in apps/")
        return [para]

    # Get all entities for cross-references
    all_stories = hcd_context.story_repo.list_all()
    all_epics = hcd_context.epic_repo.list_all()
    all_journeys = hcd_context.journey_repo.list_all()

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
        ref = nodes.reference("", "", refuri=story_path)
        ref += nodes.Text(f"{story_count} stories")
        stories_para += ref
        stories_para += nodes.Text(".")
        result_nodes.append(stories_para)

    # Build seealso box with metadata
    seealso_node = seealso()

    # Type
    type_para = nodes.paragraph()
    type_para += nodes.strong(text="Type: ")
    type_para += nodes.Text(app.type_label)
    seealso_node += type_para

    # Status (if present)
    if app.status:
        status_para = nodes.paragraph()
        status_para += nodes.strong(text="Status: ")
        status_para += nodes.Text(app.status)
        seealso_node += status_para

    # Personas (derived from stories)
    personas = get_personas_for_app(app, all_stories, all_epics)
    if personas:
        persona_para = nodes.paragraph()
        persona_para += nodes.strong(text="Personas: ")
        for i, persona in enumerate(personas):
            persona_slug = slugify(persona.name)
            persona_path = (
                f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
            )
            ref = nodes.reference("", "", refuri=persona_path)
            ref += nodes.Text(persona.name)
            persona_para += ref
            if i < len(personas) - 1:
                persona_para += nodes.Text(", ")
        seealso_node += persona_para

    # Related Journeys
    journeys = get_journeys_for_app(app, all_stories, all_journeys)
    if journeys:
        journey_para = nodes.paragraph()
        journey_para += nodes.strong(text="Journeys: ")
        for i, journey in enumerate(journeys):
            journey_path = (
                f"{prefix}{config.get_doc_path('journeys')}/{journey.slug}.html"
            )
            ref = nodes.reference("", "", refuri=journey_path)
            ref += nodes.Text(journey.slug.replace("-", " ").title())
            journey_para += ref
            if i < len(journeys) - 1:
                journey_para += nodes.Text(", ")
        seealso_node += journey_para

    # Related Epics
    epics = get_epics_for_app(app, all_stories, all_epics)
    if epics:
        epic_para = nodes.paragraph()
        epic_para += nodes.strong(text="Epics: ")
        for i, epic in enumerate(epics):
            epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic.slug}.html"
            ref = nodes.reference("", "", refuri=epic_path)
            ref += nodes.Text(epic.slug.replace("-", " ").title())
            epic_para += ref
            if i < len(epics) - 1:
                epic_para += nodes.Text(", ")
        seealso_node += epic_para

    result_nodes.append(seealso_node)

    return result_nodes


def build_app_index(docname: str, hcd_context):
    """Build the app index grouped by interface."""
    all_apps = hcd_context.app_repo.list_all()

    if not all_apps:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No apps defined")
        return [para]

    # Group apps by interface
    by_interface: dict[AppInterface, list[App]] = {}
    for app in all_apps:
        by_interface.setdefault(app.interface, []).append(app)

    result_nodes = []

    # Define interface sections with labels
    interface_sections = [
        (AppInterface.SPHINX, "Documentation Extensions"),
        (AppInterface.API, "REST APIs"),
        (AppInterface.MCP, "MCP Servers"),
        (AppInterface.WEB, "Web Applications"),
        (AppInterface.CLI, "CLI Tools"),
        (AppInterface.UNKNOWN, "Other Applications"),
    ]

    for interface_key, interface_label in interface_sections:
        apps = by_interface.get(interface_key, [])
        if not apps:
            continue

        # Section heading
        heading = nodes.paragraph()
        heading += nodes.strong(text=interface_label)
        result_nodes.append(heading)

        # App list
        app_list = nodes.bullet_list()

        for app in sorted(apps, key=lambda a: a.name):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to app
            app_path = f"{app.slug}.html"
            ref = nodes.reference("", "", refuri=app_path)
            ref += nodes.Text(app.name)
            para += ref

            # Technology tag
            if app.technology:
                para += nodes.Text(f" — {app.technology}")

            # Description snippet
            if app.description:
                desc = app.description.split(".")[0] + "."
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                para += nodes.Text(f" ")
                para += nodes.emphasis(text=desc)

            item += para
            app_list += item

        result_nodes.append(app_list)

    return result_nodes


def build_apps_for_persona(docname: str, persona_arg: str, hcd_context):
    """Build list of apps for a persona."""
    from ..config import get_config
    from julee.hcd.domain.use_cases import derive_personas, get_apps_for_persona

    config = get_config()
    prefix = path_to_root(docname)
    persona_normalized = normalize_name(persona_arg)

    all_apps = hcd_context.app_repo.list_all()
    all_stories = hcd_context.story_repo.list_all()
    all_epics = hcd_context.epic_repo.list_all()

    # Derive personas
    personas = derive_personas(all_stories, all_epics)

    # Find the persona
    persona = None
    for p in personas:
        if p.normalized_name == persona_normalized:
            persona = p
            break

    if not persona:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No apps found for persona '{persona_arg}'")
        return [para]

    # Get apps for this persona
    matching_apps = get_apps_for_persona(persona, all_apps)

    if not matching_apps:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No apps found for persona '{persona_arg}'")
        return [para]

    bullet_list = nodes.bullet_list()

    for app in sorted(matching_apps, key=lambda a: a.name):
        item = nodes.list_item()
        para = nodes.paragraph()

        app_path = f"{prefix}{config.get_doc_path('applications')}/{app.slug}.html"
        ref = nodes.reference("", "", refuri=app_path)
        ref += nodes.Text(app.name)
        para += ref

        item += para
        bullet_list += item

    return [bullet_list]


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
