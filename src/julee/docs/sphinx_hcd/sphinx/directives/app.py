"""App directives for sphinx_hcd.

Provides directives for rendering application information:
- define-app: Render app info from YAML manifest + derived data
- app-index: Generate index tables grouped by type
- apps-for-persona: List apps for a persona
"""

from docutils import nodes

from ...domain.models.app import App, AppType
from ...domain.use_cases import (
    get_app_cross_references,
    get_epics_for_app,
    get_journeys_for_app,
    get_personas_for_app,
    get_stories_for_app,
)
from ...utils import normalize_name, path_to_root, slugify
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
    """Render app info from YAML manifest plus derived data.

    Usage::

        .. define-app:: credential-tool
    """

    required_arguments = 1

    def run(self):
        app_slug = self.arguments[0]

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

    from ...config import get_config

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

    # Description first
    if app.description:
        desc_para = nodes.paragraph()
        desc_para += nodes.Text(app.description)
        result_nodes.append(desc_para)

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
    """Build the app index grouped by type."""
    all_apps = hcd_context.app_repo.list_all()
    all_stories = hcd_context.story_repo.list_all()

    if not all_apps:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No apps defined")
        return [para]

    # Group apps by type
    by_type: dict[AppType, list[App]] = {
        AppType.STAFF: [],
        AppType.EXTERNAL: [],
        AppType.MEMBER_TOOL: [],
    }

    for app in all_apps:
        if app.app_type in by_type:
            by_type[app.app_type].append(app)
        else:
            by_type.setdefault(app.app_type, []).append(app)

    result_nodes = []

    type_sections = [
        (AppType.STAFF, "Staff Applications"),
        (AppType.EXTERNAL, "External Applications"),
        (AppType.MEMBER_TOOL, "Member Tools"),
    ]

    for type_key, type_label in type_sections:
        apps = by_type.get(type_key, [])
        if not apps:
            continue

        # Section heading
        heading = nodes.paragraph()
        heading += nodes.strong(text=type_label)
        result_nodes.append(heading)

        # App list
        app_list = nodes.bullet_list()

        for app in sorted(apps, key=lambda a: a.name):
            # Get personas for this app
            app_stories = get_stories_for_app(app, all_stories)
            personas = {s.persona for s in app_stories}

            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to app
            app_path = f"{app.slug}.html"
            ref = nodes.reference("", "", refuri=app_path)
            ref += nodes.Text(app.name)
            para += ref

            # Personas
            if personas:
                para += nodes.Text(f" ({', '.join(sorted(personas))})")

            item += para
            app_list += item

        result_nodes.append(app_list)

    return result_nodes


def build_apps_for_persona(docname: str, persona_arg: str, hcd_context):
    """Build list of apps for a persona."""
    from ...config import get_config
    from ...domain.use_cases import derive_personas, get_apps_for_persona

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
